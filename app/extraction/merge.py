import re
from typing import Any

from openai import OpenAI

from app.extraction.client import create_client
from app.extraction.common import (
    MERGE_MATCH_MODEL_NAME,
    field_relation,
    list_overlap_score,
    normalize_lookup_key,
    preview_match_list,
    preview_match_text,
    prune_match_payload,
    split_rewritten_text,
    text_similarity,
)
from app.extraction.education import merge_education_courses, merge_education_honors
from app.extraction.entity_resolution import prefer_full_entity_name
from app.extraction.experience import experience_text_overlap
from app.extraction.models import ObjectMatchSelection
from app.extraction.prompt_collection import build_object_match_messages
from app.extraction.schema_tools import (
    identity_fields_for_path,
    is_blank_object,
    seed_data_from_blueprint,
)
from app.extraction.skills_engine import merge_skill_values


def merge_experience_summary_text(current: Any, incoming: Any) -> str:
    from app.extraction.common import join_rewritten_sentences

    current_sentences = split_rewritten_text(current)
    incoming_sentences = split_rewritten_text(incoming)
    return join_rewritten_sentences(current_sentences + incoming_sentences)


def merge_city_with_location(current: Any, incoming: Any) -> Any:
    if not isinstance(current, str) or not isinstance(incoming, str):
        return current
    if not current or not incoming:
        return incoming if not current else current

    if "(" not in incoming or "(" in current:
        return current

    current_base = re.sub(r"\s*\([^)]*\)\s*$", "", current).strip()
    incoming_base = re.sub(r"\s*\([^)]*\)\s*$", "", incoming).strip()
    if normalize_lookup_key(current_base) and normalize_lookup_key(current_base) == normalize_lookup_key(incoming_base):
        return incoming
    return current


def find_matching_experience_index(current_list: list[Any], incoming_item: dict[str, Any]) -> int | None:
    best_index: int | None = None
    best_score = 0.0

    for index, current_item in enumerate(current_list):
        if not isinstance(current_item, dict):
            continue

        _, company_similarity = field_relation(current_item.get("company"), incoming_item.get("company"), similarity_threshold=0.72)
        _, title_similarity = field_relation(current_item.get("job_title"), incoming_item.get("job_title"), similarity_threshold=0.72)
        start_relation, start_similarity = field_relation(current_item.get("start_date"), incoming_item.get("start_date"), similarity_threshold=0.7)
        end_relation, end_similarity = field_relation(current_item.get("end_date"), incoming_item.get("end_date"), similarity_threshold=0.7)

        dates_conflict = start_relation == -1 or end_relation == -1
        date_matches = int(start_relation == 1) + int(end_relation == 1)
        date_similarity = max(start_similarity, end_similarity)

        content_overlap = experience_text_overlap(current_item.get("content", []), incoming_item.get("content", []))
        method_overlap = experience_text_overlap(current_item.get("method", []), incoming_item.get("method", []))
        result_overlap = experience_text_overlap(current_item.get("result", []), incoming_item.get("result", []))
        text_overlap = max(content_overlap, method_overlap, result_overlap)

        bool_match = (
            0.4
            if current_item.get("is_current") is not None
            and incoming_item.get("is_current") is not None
            and current_item.get("is_current") == incoming_item.get("is_current")
            else 0.0
        )

        if dates_conflict and company_similarity < 0.9 and title_similarity < 0.9:
            continue

        strong_match = (
            (company_similarity >= 0.9 and title_similarity >= 0.72 and not dates_conflict)
            or (company_similarity >= 0.9 and date_matches >= 1 and not dates_conflict)
            or (title_similarity >= 0.9 and date_matches >= 1 and not dates_conflict)
            or (title_similarity >= 0.8 and text_overlap >= 0.55 and not dates_conflict)
            or (company_similarity >= 0.72 and text_overlap >= 0.68 and not dates_conflict)
            or (company_similarity >= 0.72 and title_similarity >= 0.72 and date_similarity >= 0.7)
        )
        if not strong_match:
            continue

        score = (
            company_similarity * 3.0
            + title_similarity * 3.0
            + date_matches * 1.5
            + date_similarity * 0.8
            + text_overlap * 2.2
            + bool_match
        )
        if score > best_score:
            best_score = score
            best_index = index

    return best_index


def find_matching_education_index(current_list: list[Any], incoming_item: dict[str, Any]) -> int | None:
    best_index: int | None = None
    best_score = 0.0

    for index, current_item in enumerate(current_list):
        if not isinstance(current_item, dict):
            continue

        _, institution_similarity = field_relation(current_item.get("institution"), incoming_item.get("institution"), similarity_threshold=0.72)
        _, degree_similarity = field_relation(current_item.get("degree"), incoming_item.get("degree"), similarity_threshold=0.72)
        start_relation, start_similarity = field_relation(current_item.get("start_date"), incoming_item.get("start_date"), similarity_threshold=0.7)
        end_relation, end_similarity = field_relation(current_item.get("end_date"), incoming_item.get("end_date"), similarity_threshold=0.7)

        dates_conflict = start_relation == -1 or end_relation == -1
        date_matches = int(start_relation == 1) + int(end_relation == 1)
        date_similarity = max(start_similarity, end_similarity)
        major_overlap = list_overlap_score(current_item.get("majors_or_programs", []), incoming_item.get("majors_or_programs", []))
        course_overlap = list_overlap_score(current_item.get("courses", []), incoming_item.get("courses", []))

        if dates_conflict and institution_similarity < 0.9:
            continue

        strong_match = (
            (institution_similarity >= 0.9 and not dates_conflict)
            or (institution_similarity >= 0.82 and date_matches >= 1 and not dates_conflict)
            or (institution_similarity >= 0.72 and degree_similarity >= 0.72 and date_matches >= 1)
            or (major_overlap >= 0.68 and date_matches >= 1 and not dates_conflict)
            or (course_overlap >= 0.72 and date_matches >= 1 and not dates_conflict)
        )
        if not strong_match:
            continue

        score = (
            institution_similarity * 3.0
            + degree_similarity * 2.0
            + date_matches * 1.5
            + date_similarity * 0.8
            + major_overlap * 1.5
            + course_overlap * 1.2
        )
        if score > best_score:
            best_score = score
            best_index = index

    return best_index


def find_matching_activity_index(current_list: list[Any], incoming_item: dict[str, Any]) -> int | None:
    best_index: int | None = None
    best_score = 0.0

    for index, current_item in enumerate(current_list):
        if not isinstance(current_item, dict):
            continue

        _, organization_similarity = field_relation(current_item.get("organization"), incoming_item.get("organization"), similarity_threshold=0.72)
        _, role_similarity = field_relation(current_item.get("role"), incoming_item.get("role"), similarity_threshold=0.72)
        start_relation, start_similarity = field_relation(current_item.get("start_date"), incoming_item.get("start_date"), similarity_threshold=0.7)
        end_relation, end_similarity = field_relation(current_item.get("end_date"), incoming_item.get("end_date"), similarity_threshold=0.7)

        dates_conflict = start_relation == -1 or end_relation == -1
        date_matches = int(start_relation == 1) + int(end_relation == 1)
        date_similarity = max(start_similarity, end_similarity)
        description_overlap = list_overlap_score(current_item.get("description", []), incoming_item.get("description", []))

        if dates_conflict and organization_similarity < 0.9:
            continue

        strong_match = (
            (organization_similarity >= 0.9 and not dates_conflict)
            or (organization_similarity >= 0.72 and role_similarity >= 0.72 and date_matches >= 1)
            or (organization_similarity >= 0.82 and date_matches >= 1 and not dates_conflict)
            or (description_overlap >= 0.68 and role_similarity >= 0.72)
        )
        if not strong_match:
            continue

        score = (
            organization_similarity * 3.0
            + role_similarity * 2.0
            + date_matches * 1.5
            + date_similarity * 0.8
            + description_overlap * 1.4
        )
        if score > best_score:
            best_score = score
            best_index = index

    return best_index


def find_matching_object_index(path: tuple[str, ...], current_list: list[Any], incoming_item: dict[str, Any]) -> int | None:
    if path == ("professional_experience",):
        return find_matching_experience_index(current_list, incoming_item)
    if path == ("education",):
        return find_matching_education_index(current_list, incoming_item)
    if path == ("activities",):
        return find_matching_activity_index(current_list, incoming_item)

    identity_fields = identity_fields_for_path(path)
    if not identity_fields:
        return None

    best_index: int | None = None
    best_score = 0

    for index, current_item in enumerate(current_list):
        if not isinstance(current_item, dict):
            continue

        score = 0
        conflict = False
        for field in identity_fields:
            existing_value = current_item.get(field)
            incoming_value = incoming_item.get(field)

            if not existing_value and not incoming_value:
                continue
            if existing_value and incoming_value:
                if existing_value == incoming_value:
                    score += 1
                else:
                    conflict = True
                    break

        if not conflict and score > best_score:
            best_index = index
            best_score = score

    return best_index if best_score > 0 else None


def serialize_object_match_entry(
    path: tuple[str, ...],
    item: dict[str, Any],
    *,
    candidate_index: int | None = None,
) -> dict[str, Any]:
    if path == ("education",):
        payload = {
            "candidate_index": candidate_index,
            "institution": preview_match_text(item.get("institution")),
            "degree": preview_match_text(item.get("degree")),
            "start_date": preview_match_text(item.get("start_date")),
            "end_date": preview_match_text(item.get("end_date")),
            "city": preview_match_text(item.get("city")),
            "state_or_province": preview_match_text(item.get("state_or_province")),
            "country": preview_match_text(item.get("country")),
            "majors_or_programs": preview_match_list(item.get("majors_or_programs"), limit=5),
            "courses_preview": preview_match_list(item.get("courses"), limit=8),
            "courses_count": len(item.get("courses", [])) if isinstance(item.get("courses"), list) else 0,
            "gpa": preview_match_text(item.get("gpa")),
            "honors": preview_match_list(item.get("honors"), limit=5),
        }
        return prune_match_payload(payload)

    if path == ("professional_experience",):
        payload = {
            "candidate_index": candidate_index,
            "company": preview_match_text(item.get("company")),
            "job_title": preview_match_text(item.get("job_title")),
            "start_date": preview_match_text(item.get("start_date")),
            "end_date": preview_match_text(item.get("end_date")),
            "is_current": item.get("is_current"),
            "city": preview_match_text(item.get("city")),
            "state_or_province": preview_match_text(item.get("state_or_province")),
            "country": preview_match_text(item.get("country")),
            "content": preview_match_text(item.get("content"), limit=260),
            "method": preview_match_text(item.get("method"), limit=260),
            "result": preview_match_text(item.get("result"), limit=260),
        }
        return prune_match_payload(payload)

    if path == ("activities",):
        payload = {
            "candidate_index": candidate_index,
            "organization": preview_match_text(item.get("organization")),
            "role": preview_match_text(item.get("role")),
            "start_date": preview_match_text(item.get("start_date")),
            "end_date": preview_match_text(item.get("end_date")),
            "description": preview_match_list(item.get("description"), limit=6, item_limit=220),
        }
        return prune_match_payload(payload)

    payload = dict(item)
    if candidate_index is not None:
        payload["candidate_index"] = candidate_index
    return prune_match_payload(payload)


def find_matching_object_index_with_gpt(
    client: OpenAI | None,
    path: tuple[str, ...],
    current_list: list[Any],
    incoming_item: dict[str, Any],
) -> tuple[bool, int | None]:
    if client is None or path not in {("education",), ("professional_experience",), ("activities",)}:
        return False, None

    candidate_payload: list[dict[str, Any]] = []
    candidate_indexes: set[int] = set()
    for index, current_item in enumerate(current_list):
        if not isinstance(current_item, dict) or is_blank_object(current_item):
            continue
        candidate_payload.append(serialize_object_match_entry(path, current_item, candidate_index=index))
        candidate_indexes.add(index)

    if not candidate_payload:
        return False, None

    try:
        completion = client.chat.completions.parse(
            model=MERGE_MATCH_MODEL_NAME,
            temperature=0,
            messages=build_object_match_messages(path[0], serialize_object_match_entry(path, incoming_item), candidate_payload),
            response_format=ObjectMatchSelection,
        )
        message = completion.choices[0].message
    except Exception:
        return False, None

    if getattr(message, "refusal", None) or message.parsed is None:
        return False, None

    if message.parsed.match_index in candidate_indexes:
        return True, message.parsed.match_index
    return True, None


def merge_resume_data(
    current: Any,
    incoming: Any,
    blueprint: dict[str, Any],
    api_key_override: str | None = None,
) -> Any:
    try:
        client = create_client(api_key_override)
    except Exception:
        client = None
    return merge_into_blank_slots(current, incoming, blueprint, client=client)


def merge_into_blank_slots(
    current: Any,
    incoming: Any,
    blueprint: dict[str, Any],
    path: tuple[str, ...] = (),
    *,
    client: OpenAI | None = None,
) -> Any:
    kind = blueprint["kind"]

    if kind == "object":
        current_obj = current if isinstance(current, dict) else {}
        incoming_obj = incoming if isinstance(incoming, dict) else {}
        merged: dict[str, Any] = {}

        for field in blueprint["fields"]:
            field_name = field["name"]
            field_blueprint = field["blueprint"]
            merged[field_name] = merge_into_blank_slots(
                current_obj.get(field_name, seed_data_from_blueprint(field_blueprint)),
                incoming_obj.get(field_name),
                field_blueprint,
                path + (field_name,),
                client=client,
            )
        return merged

    if kind == "list":
        item_blueprint = blueprint["item_blueprint"]
        current_list = current if isinstance(current, list) else []
        incoming_list = incoming if isinstance(incoming, list) else []

        if path in {("skills", "languages"), ("skills", "computer")}:
            return merge_skill_values(
                current_list,
                incoming_list,
                client=client,
                category_name="languages" if path == ("skills", "languages") else "computer skills",
            )

        if not current_list and not incoming_list:
            return []
        if not incoming_list:
            return current_list
        if not current_list:
            if path == ("education", "honors"):
                return merge_education_honors([], incoming_list)
            if path == ("education", "courses"):
                return merge_education_courses([], incoming_list)
            return [
                merge_into_blank_slots(seed_data_from_blueprint(item_blueprint), item, item_blueprint, client=client)
                for item in incoming_list
            ]

        if path == ("education", "honors"):
            return merge_education_honors(current_list, incoming_list)
        if path == ("education", "courses"):
            return merge_education_courses(current_list, incoming_list)

        if item_blueprint["kind"] in {"string", "boolean"}:
            merged_list = list(current_list)
            for item in incoming_list:
                if item not in merged_list and item not in ("", None):
                    merged_list.append(item)
            return merged_list

        blank_item = seed_data_from_blueprint(item_blueprint)
        merged_list: list[Any] = list(current_list)

        for incoming_item in incoming_list:
            if item_blueprint["kind"] == "object" and isinstance(incoming_item, dict):
                if is_blank_object(incoming_item):
                    continue

                used_gpt_matcher, match_index = find_matching_object_index_with_gpt(client, path, merged_list, incoming_item)
                if not used_gpt_matcher:
                    match_index = find_matching_object_index(path, merged_list, incoming_item)
                if match_index is not None:
                    merged_list[match_index] = merge_into_blank_slots(
                        merged_list[match_index],
                        incoming_item,
                        item_blueprint,
                        path,
                        client=client,
                    )
                else:
                    merged_list.append(
                        merge_into_blank_slots(blank_item, incoming_item, item_blueprint, path, client=client)
                    )
                continue

            if incoming_item not in merged_list and incoming_item not in ("", None):
                merged_list.append(incoming_item)
        return merged_list

    if kind == "boolean":
        return incoming if current is None and incoming is not None else current

    if path in {
        ("professional_experience", "content"),
        ("professional_experience", "method"),
        ("professional_experience", "result"),
    }:
        if isinstance(current, str) and isinstance(incoming, str):
            if not current:
                return incoming
            if not incoming:
                return current
            return merge_experience_summary_text(current, incoming)

    if path in {
        ("education", "institution"),
        ("professional_experience", "company"),
        ("activities", "organization"),
    }:
        merged_name = prefer_full_entity_name(current, incoming)
        if merged_name:
            return merged_name

    if path in {("education", "city"), ("professional_experience", "city")}:
        merged_city = merge_city_with_location(current, incoming)
        if merged_city != current:
            return merged_city

    if isinstance(incoming, str) and incoming != "" and current in ("", None):
        return incoming
    return "" if current is None else current
