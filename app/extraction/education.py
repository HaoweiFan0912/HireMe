import re
from typing import Any

from openai import OpenAI

from app.extraction.common import MODEL_NAME, dedupe_preserve_order, normalize_text
from app.extraction.models import EducationCoursesRewriteSelection, EducationHonorsRewriteSelection
from app.extraction.prompt_collection import (
    build_education_courses_messages,
    build_education_honors_messages,
)


def clean_course_value(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.replace("\n", " ").split()).strip(" ,;:|")


def normalize_course_key(value: Any) -> str:
    cleaned = clean_course_value(value)
    if not cleaned:
        return ""
    return normalize_text(cleaned)


def normalize_course_display(value: Any) -> str:
    cleaned = clean_course_value(value)
    if not cleaned:
        return ""
    return cleaned


def prefer_course_label(current: str, incoming: str) -> str:
    current_display = normalize_course_display(current)
    incoming_display = normalize_course_display(incoming)
    if not current_display:
        return incoming_display
    if not incoming_display:
        return current_display
    return current_display


def merge_education_courses(current_values: list[Any], incoming_values: list[Any]) -> list[str]:
    merged: list[str] = []
    index_by_key: dict[str, int] = {}

    for raw_value in list(current_values) + list(incoming_values):
        display_value = normalize_course_display(raw_value)
        normalized_key = normalize_course_key(display_value)
        if not display_value or not normalized_key:
            continue

        existing_index = index_by_key.get(normalized_key)
        if existing_index is None:
            index_by_key[normalized_key] = len(merged)
            merged.append(display_value)
            continue

        merged[existing_index] = prefer_course_label(merged[existing_index], display_value)

    return merged


def split_honor_and_time(value: Any) -> tuple[str, str]:
    if not isinstance(value, str):
        return "", ""

    cleaned = " ".join(value.split()).strip()
    if not cleaned:
        return "", ""

    parenthetical_match = re.match(r"^(?P<name>.+?)\s*\((?P<time>[^()]+)\)\s*$", cleaned)
    if parenthetical_match:
        return (
            parenthetical_match.group("name").strip(),
            parenthetical_match.group("time").strip(),
        )

    timed_prefix_patterns = (
        re.compile(
            r"^(?P<time>(?:19|20)\d{2}\s+(?:Spring|Summer|Fall|Winter))\s*[-:–—]\s*(?P<name>.+)$",
            re.IGNORECASE,
        ),
        re.compile(
            r"^(?P<time>(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\s+\d{4})\s*[-:–—]\s*(?P<name>.+)$",
            re.IGNORECASE,
        ),
    )
    for pattern in timed_prefix_patterns:
        timed_match = pattern.match(cleaned)
        if timed_match:
            return (
                timed_match.group("name").strip(),
                timed_match.group("time").strip(),
            )

    return cleaned, ""


def format_honor_display(name: Any, time_value: Any) -> str:
    if not isinstance(name, str):
        return ""

    cleaned_name = " ".join(name.split()).strip()
    if not cleaned_name:
        return ""

    if not isinstance(time_value, str) or not time_value.strip():
        return cleaned_name

    cleaned_time = " ".join(time_value.split()).strip()
    return f"{cleaned_name} ({cleaned_time})"


def merge_education_honors(current_values: list[Any], incoming_values: list[Any]) -> list[str]:
    merged: list[str | None] = []
    exact_seen: set[tuple[str, str]] = set()
    timed_seen_by_base: set[str] = set()
    untimed_index_by_base: dict[str, int] = {}

    for raw_value in list(current_values) + list(incoming_values):
        base_name, time_value = split_honor_and_time(raw_value)
        display_value = format_honor_display(base_name, time_value)
        if not display_value:
            continue

        base_key = normalize_text(base_name)
        time_key = normalize_text(time_value)
        if not base_key:
            continue

        dedupe_key = (base_key, time_key)
        if dedupe_key in exact_seen:
            continue

        if time_key:
            if base_key in untimed_index_by_base:
                merged[untimed_index_by_base[base_key]] = None
                del untimed_index_by_base[base_key]

            merged.append(display_value)
            exact_seen.add(dedupe_key)
            timed_seen_by_base.add(base_key)
            continue

        if base_key in timed_seen_by_base:
            continue

        untimed_index_by_base[base_key] = len(merged)
        merged.append(display_value)
        exact_seen.add(dedupe_key)

    return [item for item in merged if isinstance(item, str)]


def collect_honor_context_lines(document_text: str, extracted: dict[str, Any]) -> list[str]:
    education_entries = extracted.get("education")
    if not isinstance(education_entries, list):
        return []

    honor_terms = {
        "dean",
        "scholar",
        "distinction",
        "honor",
        "honours",
        "award",
        "fellow",
        "prize",
        "scholarship",
        "cum laude",
    }

    for entry in education_entries:
        if not isinstance(entry, dict):
            continue

        for honor in entry.get("honors", []):
            base_name, _ = split_honor_and_time(honor)
            normalized = normalize_text(base_name)
            if not normalized:
                continue
            honor_terms.add(normalized)
            honor_terms.update(token for token in normalized.split() if len(token) >= 4)

    selected_lines: list[str] = []
    for raw_line in document_text.splitlines():
        line = " ".join(raw_line.split()).strip()
        if not line:
            continue

        normalized_line = normalize_text(line)
        if not normalized_line:
            continue

        if any(term and term in normalized_line for term in honor_terms):
            selected_lines.append(line)

    return dedupe_preserve_order(selected_lines)


def extract_time_from_honor_line(line: str) -> str:
    time_patterns = (
        re.compile(r"\b((?:19|20)\d{2}\s+(?:Spring|Summer|Fall|Winter))\b", re.IGNORECASE),
        re.compile(r"\b((?:Spring|Summer|Fall|Winter)\s+(?:19|20)\d{2})\b", re.IGNORECASE),
        re.compile(
            r"\b((?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\s+\d{4})\b",
            re.IGNORECASE,
        ),
    )

    for pattern in time_patterns:
        match = pattern.search(line)
        if match:
            return match.group(1).strip()
    return ""


def enrich_honors_with_source_times(honors: list[Any], honor_lines: list[str]) -> list[str]:
    enriched: list[str] = []
    for honor in honors:
        base_name, time_value = split_honor_and_time(honor)
        if not base_name:
            continue

        if not time_value:
            base_key = normalize_text(base_name)
            for line in honor_lines:
                normalized_line = normalize_text(line)
                if base_key and base_key in normalized_line:
                    candidate_time = extract_time_from_honor_line(line)
                    if candidate_time:
                        time_value = candidate_time
                        break

        enriched.append(format_honor_display(base_name, time_value))

    return merge_education_honors([], enriched)


def refine_education_honors(
    client: OpenAI,
    document_text: str | None,
    extracted: dict[str, Any],
) -> dict[str, Any]:
    education = extracted.get("education")
    if not isinstance(education, list):
        return extracted

    for entry in education:
        if isinstance(entry, dict):
            entry["honors"] = merge_education_honors(entry.get("honors", []), [])

    if not document_text:
        extracted["education"] = education
        return extracted

    honor_lines = collect_honor_context_lines(document_text, extracted)
    if not honor_lines:
        extracted["education"] = education
        return extracted

    honors_payload = [
        {
            "entry_index": index,
            "institution": entry.get("institution"),
            "degree": entry.get("degree"),
            "start_date": entry.get("start_date"),
            "end_date": entry.get("end_date"),
            "current_honors": entry.get("honors", []),
        }
        for index, entry in enumerate(education)
        if isinstance(entry, dict)
    ]

    if not any(item["current_honors"] for item in honors_payload):
        extracted["education"] = education
        return extracted

    try:
        refinement = client.chat.completions.parse(
            model=MODEL_NAME,
            temperature=0,
            messages=build_education_honors_messages(honors_payload, honor_lines),
            response_format=EducationHonorsRewriteSelection,
        )
        message = refinement.choices[0].message
    except Exception:
        for entry in education:
            if isinstance(entry, dict):
                entry["honors"] = enrich_honors_with_source_times(entry.get("honors", []), honor_lines)
        extracted["education"] = education
        return extracted

    if getattr(message, "refusal", None) or message.parsed is None:
        for entry in education:
            if isinstance(entry, dict):
                entry["honors"] = enrich_honors_with_source_times(entry.get("honors", []), honor_lines)
        extracted["education"] = education
        return extracted

    rewritten_by_index = {item.entry_index: item.honors for item in message.parsed.items}
    for index, entry in enumerate(education):
        if not isinstance(entry, dict):
            continue
        entry["honors"] = merge_education_honors(entry.get("honors", []), rewritten_by_index.get(index, []))
        entry["honors"] = enrich_honors_with_source_times(entry.get("honors", []), honor_lines)

    extracted["education"] = education
    return extracted


def refine_education_courses(
    client: OpenAI,
    document_text: str | None,
    extracted: dict[str, Any],
) -> dict[str, Any]:
    education = extracted.get("education")
    if not isinstance(education, list):
        return extracted

    for entry in education:
        if isinstance(entry, dict):
            entry["courses"] = merge_education_courses(entry.get("courses", []), [])

    has_current_courses = any(isinstance(entry, dict) and entry.get("courses") for entry in education)
    if not document_text and not has_current_courses:
        extracted["education"] = education
        return extracted

    courses_payload = [
        {
            "entry_index": index,
            "institution": entry.get("institution"),
            "degree": entry.get("degree"),
            "start_date": entry.get("start_date"),
            "end_date": entry.get("end_date"),
            "majors_or_programs": entry.get("majors_or_programs", []),
            "current_courses": entry.get("courses", []),
        }
        for index, entry in enumerate(education)
        if isinstance(entry, dict)
    ]
    if not courses_payload:
        extracted["education"] = education
        return extracted

    try:
        refinement = client.chat.completions.parse(
            model=MODEL_NAME,
            temperature=0,
            messages=build_education_courses_messages(courses_payload, document_text),
            response_format=EducationCoursesRewriteSelection,
        )
        message = refinement.choices[0].message
    except Exception:
        extracted["education"] = education
        return extracted

    if getattr(message, "refusal", None) or message.parsed is None:
        extracted["education"] = education
        return extracted

    rewritten_by_index = {item.entry_index: item.courses for item in message.parsed.items}
    for index, entry in enumerate(education):
        if not isinstance(entry, dict):
            continue
        entry["courses"] = merge_education_courses(entry.get("courses", []), rewritten_by_index.get(index, []))

    extracted["education"] = education
    return extracted
