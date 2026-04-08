from typing import Any

from app.extraction.client import create_client
from app.extraction.document_content import build_document_content
from app.extraction.education import refine_education_courses, refine_education_honors
from app.extraction.entity_resolution import (
    lookup_education_locations_with_gpt,
    lookup_entity_full_names_with_gpt,
    lookup_experience_locations_with_gpt,
    normalize_links,
)
from app.extraction.experience import refine_experience_with_evidence
from app.extraction.merge import merge_into_blank_slots, merge_resume_data
from app.extraction.models import ExtractedResumeSchema
from app.extraction.prompt_collection import build_initial_extraction_messages
from app.extraction.schema_tools import (
    build_resume_blueprint,
    build_resume_template,
    normalize_data_to_blueprint,
)
from app.extraction.skills_engine import refine_skills_from_document
from app.extraction.common import MODEL_NAME


def extract_resume_from_bytes(
    filename: str,
    content_type: str | None,
    file_bytes: bytes,
    api_key_override: str | None = None,
) -> dict[str, Any]:
    client = create_client(api_key_override)
    content, document_text = build_document_content(filename, content_type, file_bytes)

    completion = client.chat.completions.parse(
        model=MODEL_NAME,
        temperature=0,
        messages=build_initial_extraction_messages(content),
        response_format=ExtractedResumeSchema,
    )

    message = completion.choices[0].message
    if getattr(message, "refusal", None):
        raise ValueError(f"The model refused to process this file: {message.refusal}")
    if message.parsed is None:
        raise ValueError("The model did not return a parseable structured result.")

    extracted = normalize_links(message.parsed.model_dump(mode="json"))
    extracted = lookup_entity_full_names_with_gpt(client, document_text, extracted)
    extracted = lookup_education_locations_with_gpt(client, document_text, extracted)
    extracted = refine_education_honors(client, document_text, extracted)
    extracted = refine_education_courses(client, document_text, extracted)
    extracted = lookup_experience_locations_with_gpt(client, document_text, extracted)
    extracted = refine_experience_with_evidence(client, document_text, extracted)
    return refine_skills_from_document(client, document_text, extracted)


__all__ = [
    "build_resume_blueprint",
    "build_resume_template",
    "extract_resume_from_bytes",
    "merge_into_blank_slots",
    "merge_resume_data",
    "normalize_data_to_blueprint",
]
