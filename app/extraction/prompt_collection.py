import json
from typing import Any

from app.extraction.extraction_skills import (
    ACTIVITY_OBJECT_MATCH_RULES,
    EDUCATION_COURSES_RULES,
    EDUCATION_COURSES_SYSTEM_SKILL,
    EDUCATION_HONORS_RULES,
    EDUCATION_HONORS_SYSTEM_SKILL,
    EDUCATION_OBJECT_MATCH_RULES,
    ENTITY_FULL_NAME_LOOKUP_RULES,
    ENTITY_FULL_NAME_LOOKUP_SYSTEM_SKILL,
    EDUCATION_LOCATION_LOOKUP_RULES,
    EDUCATION_LOCATION_LOOKUP_SYSTEM_SKILL,
    EXPERIENCE_OBJECT_MATCH_RULES,
    EXPERIENCE_EVIDENCE_SELECTION_RULES,
    EXPERIENCE_EVIDENCE_SELECTION_SYSTEM_SKILL,
    EXPERIENCE_LOCATION_LOOKUP_RULES,
    EXPERIENCE_LOCATION_LOOKUP_SYSTEM_SKILL,
    EXPERIENCE_REWRITE_RULES,
    EXPERIENCE_REWRITE_SYSTEM_SKILL,
    OBJECT_MATCH_BASE_RULES,
    OBJECT_MATCH_SYSTEM_SKILL,
    SKILL_DEDUPLICATION_RULES,
    SKILL_DEDUPLICATION_SYSTEM_SKILL,
    SKILL_INFERENCE_RULES,
    SKILL_INFERENCE_SYSTEM_SKILL,
    STRICT_EXTRACTION_SYSTEM_SKILL,
    STRICT_SCHEMA_EXTRACTION_SKILL,
)


def truncate_context_text(value: str | None, limit: int = 12000) -> str:
    cleaned = (value or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "\n...[truncated]"


def build_initial_extraction_messages(content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "role": "system",
            "content": STRICT_EXTRACTION_SYSTEM_SKILL,
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": STRICT_SCHEMA_EXTRACTION_SKILL,
                },
                *content,
            ],
        },
    ]


def build_object_match_messages(
    section_name: str,
    incoming_entry: dict[str, Any],
    candidate_entries: list[dict[str, Any]],
) -> list[dict[str, str]]:
    section_rules = {
        "education": EDUCATION_OBJECT_MATCH_RULES,
        "professional_experience": EXPERIENCE_OBJECT_MATCH_RULES,
        "activities": ACTIVITY_OBJECT_MATCH_RULES,
    }.get(section_name, "")

    return [
        {
            "role": "system",
            "content": OBJECT_MATCH_SYSTEM_SKILL,
        },
        {
            "role": "user",
            "content": (
                "Decide whether the incoming extracted entry is the same object as one of the existing entries.\n\n"
                "Rules:\n"
                f"{OBJECT_MATCH_BASE_RULES}\n\n"
                "Section-specific guidance:\n"
                f"{section_rules}\n\n"
                f"Section: {section_name}\n\n"
                "Existing candidate entries:\n"
                f"{json.dumps(candidate_entries, ensure_ascii=False, indent=2)}\n\n"
                "Incoming entry:\n"
                f"{json.dumps(incoming_entry, ensure_ascii=False, indent=2)}\n\n"
                "Return `match_index` as the selected candidate index, or null if there is no confident match."
            ),
        },
    ]


def build_entity_full_name_lookup_prompt(
    lookup_payload: list[dict[str, Any]],
    document_text: str | None,
) -> str:
    context_text = truncate_context_text(document_text)
    if not context_text:
        context_text = "(No extracted document text was available for disambiguation clues.)"

    return (
        "Resolve the full official names for extracted schools, companies, and organizations.\n\n"
        "Rules:\n"
        f"{ENTITY_FULL_NAME_LOOKUP_RULES}\n\n"
        f"Entries needing lookup:\n{json.dumps(lookup_payload, ensure_ascii=False, indent=2)}\n\n"
        f"Document text for disambiguation:\n{context_text}"
    )


def build_entity_full_name_lookup_fallback_messages(prompt: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": ENTITY_FULL_NAME_LOOKUP_SYSTEM_SKILL,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]


def build_education_location_lookup_prompt(
    lookup_payload: list[dict[str, Any]],
    document_text: str | None,
) -> str:
    context_text = truncate_context_text(document_text)
    if not context_text:
        context_text = "(No extracted document text was available for campus clues.)"

    return (
        "Resolve missing school location fields for the extracted education entries.\n\n"
        "Rules:\n"
        f"{EDUCATION_LOCATION_LOOKUP_RULES}\n\n"
        f"Entries needing lookup:\n{json.dumps(lookup_payload, ensure_ascii=False, indent=2)}\n\n"
        f"Document text for campus clues:\n{context_text}"
    )


def build_education_location_lookup_fallback_messages(prompt: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": EDUCATION_LOCATION_LOOKUP_SYSTEM_SKILL,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]


def build_experience_location_lookup_prompt(
    lookup_payload: list[dict[str, Any]],
    document_text: str | None,
) -> str:
    context_text = truncate_context_text(document_text)
    if not context_text:
        context_text = "(No extracted document text was available for office or branch clues.)"

    return (
        "Resolve missing work-experience location fields for the extracted experience entries.\n\n"
        "Rules:\n"
        f"{EXPERIENCE_LOCATION_LOOKUP_RULES}\n\n"
        f"Entries needing lookup:\n{json.dumps(lookup_payload, ensure_ascii=False, indent=2)}\n\n"
        f"Document text for office clues:\n{context_text}"
    )


def build_experience_location_lookup_fallback_messages(prompt: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": EXPERIENCE_LOCATION_LOOKUP_SYSTEM_SKILL,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]


def build_education_honors_messages(
    honors_payload: list[dict[str, Any]],
    honor_lines: list[str],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": EDUCATION_HONORS_SYSTEM_SKILL,
        },
        {
            "role": "user",
            "content": (
                "Normalize honors for each education entry.\n\n"
                "Rules:\n"
                f"{EDUCATION_HONORS_RULES}\n\n"
                f"Education entries:\n{json.dumps(honors_payload, ensure_ascii=False, indent=2)}\n\n"
                "Honor lines from the document:\n"
                + "\n".join(f"- {line}" for line in honor_lines[:80])
            ),
        },
    ]


def build_education_courses_messages(
    courses_payload: list[dict[str, Any]],
    document_text: str | None,
) -> list[dict[str, str]]:
    context_text = truncate_context_text(document_text, limit=20000)
    if not context_text:
        context_text = "(No extracted document text was available for course identification.)"

    return [
        {
            "role": "system",
            "content": EDUCATION_COURSES_SYSTEM_SKILL,
        },
        {
            "role": "user",
            "content": (
                "Identify and normalize courses for each education entry.\n\n"
                "Rules:\n"
                f"{EDUCATION_COURSES_RULES}\n\n"
                f"Education entries:\n{json.dumps(courses_payload, ensure_ascii=False, indent=2)}\n\n"
                f"Document text:\n{context_text}"
            ),
        },
    ]


def build_experience_evidence_messages(
    experiences: list[dict[str, Any]],
    segments: list[str],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": EXPERIENCE_EVIDENCE_SELECTION_SYSTEM_SKILL,
        },
        {
            "role": "user",
            "content": (
                "Given the extracted professional experience entries and the numbered source segments, "
                "select all segment ids that belong to each entry.\n\n"
                "Rules:\n"
                f"{EXPERIENCE_EVIDENCE_SELECTION_RULES}\n\n"
                f"Extracted entries:\n{json.dumps(experiences, ensure_ascii=False, indent=2)}\n\n"
                "Source segments:\n"
                + "\n".join(f"[{index}] {segment}" for index, segment in enumerate(segments))
            ),
        },
    ]


def build_experience_rewrite_messages(rewrite_payload: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": EXPERIENCE_REWRITE_SYSTEM_SKILL,
        },
        {
            "role": "user",
            "content": (
                "For each experience entry, produce exactly three rewritten fields:\n"
                "1. `content`: one single natural and fluent text block describing only what the person completed or delivered.\n"
                "2. `method`: one single natural and fluent text block describing only how the person did the work, "
                "including tools, technologies, algorithms, workflows, or approaches.\n"
                "3. `result`: one single natural and fluent text block describing only the explicit outcome or effect.\n\n"
                "Rules:\n"
                f"{EXPERIENCE_REWRITE_RULES}\n\n"
                f"Entries:\n{json.dumps(rewrite_payload, ensure_ascii=False, indent=2)}"
            ),
        },
    ]


def build_skill_deduplication_messages(
    category_name: str,
    skill_values: list[str],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SKILL_DEDUPLICATION_SYSTEM_SKILL,
        },
        {
            "role": "user",
            "content": (
                f"Deduplicate the extracted {category_name} skill list.\n\n"
                "Rules:\n"
                f"{SKILL_DEDUPLICATION_RULES}\n\n"
                "Skill items:\n"
                + "\n".join(f"[{index}] {value}" for index, value in enumerate(skill_values))
            ),
        },
    ]


def build_skill_inference_messages(
    document_text: str | None,
    inference_context: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SKILL_INFERENCE_SYSTEM_SKILL,
        },
        {
            "role": "user",
            "content": (
                "Infer the person's skills from the uploaded document and the extracted resume structure.\n\n"
                "Rules:\n"
                f"{SKILL_INFERENCE_RULES}\n\n"
                f"Document text:\n{truncate_context_text(document_text)}\n\n"
                "Extracted context:\n"
                f"{json.dumps(inference_context, ensure_ascii=False, indent=2)}"
            ),
        },
    ]
