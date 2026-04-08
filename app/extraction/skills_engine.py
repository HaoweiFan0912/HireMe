import re
from typing import Any

from openai import OpenAI

from app.extraction.common import MERGE_MATCH_MODEL_NAME, MODEL_NAME, SKILL_ALIASES, normalize_text
from app.extraction.models import SkillDeduplicationSelection, SkillInferenceSelection
from app.extraction.prompt_collection import (
    build_skill_deduplication_messages,
    build_skill_inference_messages,
)


def clean_skill_value(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.replace("\n", " ").split()).strip(" ,;:|")


def looks_like_acronym_skill(value: str) -> bool:
    letters_only = re.sub(r"[^A-Za-z]", "", value)
    if not 2 <= len(letters_only) <= 8:
        return False
    return value.upper() == value and letters_only.isalpha()


def canonical_skill_map() -> dict[str, str]:
    return {normalize_text(display): display for display in SKILL_ALIASES.values()}


def normalize_skill_key(value: Any) -> str:
    cleaned = clean_skill_value(value)
    if not cleaned:
        return ""

    normalized = normalize_text(cleaned)
    if not normalized:
        return ""

    alias_value = SKILL_ALIASES.get(normalized)
    if alias_value:
        return normalize_text(alias_value)

    singular_normalized = re.sub(r"\b([a-z0-9]+)s\b$", r"\1", normalized)
    if singular_normalized in canonical_skill_map():
        return singular_normalized

    return normalized


def normalize_skill_display(value: Any) -> str:
    cleaned = clean_skill_value(value)
    if not cleaned:
        return ""

    normalized = normalize_skill_key(cleaned)
    canonical_display = canonical_skill_map().get(normalized)
    if canonical_display:
        return canonical_display

    return cleaned


def prefer_skill_label(current: str, incoming: str) -> str:
    current_display = normalize_skill_display(current)
    incoming_display = normalize_skill_display(incoming)
    if not current_display:
        return incoming_display
    if not incoming_display:
        return current_display

    current_is_acronym = looks_like_acronym_skill(clean_skill_value(current))
    incoming_is_acronym = looks_like_acronym_skill(clean_skill_value(incoming))
    if current_is_acronym and not incoming_is_acronym:
        return incoming_display
    if incoming_is_acronym and not current_is_acronym:
        return current_display

    if len(incoming_display) > len(current_display):
        return incoming_display
    return current_display


def merge_skill_values_locally(current_values: list[Any], incoming_values: list[Any]) -> list[str]:
    merged: list[str] = []
    index_by_key: dict[str, int] = {}

    for raw_value in list(current_values) + list(incoming_values):
        display_value = normalize_skill_display(raw_value)
        normalized_key = normalize_skill_key(display_value)
        if not display_value or not normalized_key:
            continue

        existing_index = index_by_key.get(normalized_key)
        if existing_index is None:
            index_by_key[normalized_key] = len(merged)
            merged.append(display_value)
            continue

        merged[existing_index] = prefer_skill_label(merged[existing_index], display_value)

    return merged


def dedupe_skill_values_with_gpt(
    client: OpenAI | None,
    category_name: str,
    skill_values: list[str],
) -> list[str]:
    if client is None or len(skill_values) <= 1:
        return skill_values

    try:
        completion = client.chat.completions.parse(
            model=MERGE_MATCH_MODEL_NAME,
            temperature=0,
            messages=build_skill_deduplication_messages(category_name, skill_values),
            response_format=SkillDeduplicationSelection,
        )
        message = completion.choices[0].message
    except Exception:
        return skill_values

    if getattr(message, "refusal", None) or message.parsed is None:
        return skill_values

    keep_indexes: list[int] = []
    seen_indexes: set[int] = set()
    for index in message.parsed.keep_indexes:
        if not isinstance(index, int):
            continue
        if not 0 <= index < len(skill_values):
            continue
        if index in seen_indexes:
            continue
        seen_indexes.add(index)
        keep_indexes.append(index)

    if not keep_indexes:
        return skill_values

    keep_indexes.sort()
    return [skill_values[index] for index in keep_indexes]


def merge_skill_values(
    current_values: list[Any],
    incoming_values: list[Any],
    *,
    client: OpenAI | None = None,
    category_name: str = "skills",
) -> list[str]:
    merged = merge_skill_values_locally(current_values, incoming_values)
    return dedupe_skill_values_with_gpt(client, category_name, merged)


def has_non_empty_skill_context(skills: dict[str, Any]) -> bool:
    return any(
        isinstance(skills.get(field_name), list)
        and any(isinstance(item, str) and item.strip() for item in skills.get(field_name, []))
        for field_name in ("languages", "computer")
    )


def refine_skills_from_document(
    client: OpenAI,
    document_text: str | None,
    extracted: dict[str, Any],
) -> dict[str, Any]:
    skills = extracted.get("skills")
    if not isinstance(skills, dict):
        skills = {}

    skills["languages"] = merge_skill_values(
        skills.get("languages", []),
        [],
        client=client,
        category_name="languages",
    )
    skills["computer"] = merge_skill_values(
        skills.get("computer", []),
        [],
        client=client,
        category_name="computer skills",
    )
    extracted["skills"] = skills

    inference_context = {
        "education": extracted.get("education", []),
        "professional_experience": extracted.get("professional_experience", []),
        "activities": extracted.get("activities", []),
        "existing_skills": skills,
    }

    has_structured_context = any(
        isinstance(inference_context.get(field_name), list) and bool(inference_context.get(field_name))
        for field_name in ("education", "professional_experience", "activities")
    ) or has_non_empty_skill_context(skills)
    has_document_context = bool((document_text or "").strip())
    if not has_document_context and not has_structured_context:
        return extracted

    try:
        refinement = client.chat.completions.parse(
            model=MODEL_NAME,
            temperature=0,
            messages=build_skill_inference_messages(document_text, inference_context),
            response_format=SkillInferenceSelection,
        )
        message = refinement.choices[0].message
    except Exception:
        return extracted

    if getattr(message, "refusal", None) or message.parsed is None:
        return extracted

    skills["languages"] = merge_skill_values(
        skills.get("languages", []),
        message.parsed.languages,
        client=client,
        category_name="languages",
    )
    skills["computer"] = merge_skill_values(
        skills.get("computer", []),
        message.parsed.computer,
        client=client,
        category_name="computer skills",
    )
    extracted["skills"] = skills
    return extracted
