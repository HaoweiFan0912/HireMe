import re
from typing import Any

from openai import OpenAI

from app.extraction.common import (
    MODEL_NAME,
    coerce_text_segments,
    dedupe_preserve_order,
    join_rewritten_sentences,
    list_overlap_score,
    normalize_text,
    text_similarity,
)
from app.extraction.models import ExperienceEvidenceSelection, ExperienceRewriteSelection
from app.extraction.prompt_collection import (
    build_experience_evidence_messages,
    build_experience_rewrite_messages,
)


def split_into_source_segments(document_text: str) -> list[str]:
    lines = [line.strip() for line in document_text.splitlines()]
    segments: list[str] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if not paragraph_lines:
            return

        paragraph = " ".join(part for part in paragraph_lines if part).strip()
        paragraph_lines = []
        if not paragraph:
            return

        if re.match(r"^(name|email|tel|title|address)\s*:", paragraph, re.IGNORECASE):
            segments.append(paragraph)
            return

        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"“'])", paragraph)
        for part in parts:
            cleaned = " ".join(part.split()).strip()
            if cleaned:
                segments.append(cleaned)

    for line in lines:
        if not line:
            flush_paragraph()
            continue

        if re.match(r"^(name|email|tel|title|address)\s*:", line, re.IGNORECASE):
            flush_paragraph()
            segments.append(line)
            continue

        paragraph_lines.append(line)

    flush_paragraph()
    return segments


def looks_like_result(segment: str) -> bool:
    text = normalize_text(segment)
    negative_markers = (
        " will make ",
        " would make ",
        " attitude and passion ",
        " highly recommend ",
        " recommendation ",
        " future ",
        " valuable member ",
    )
    padded = f" {text} "
    if any(marker in padded for marker in negative_markers):
        return False

    result_markers = (
        " team ",
        " project ",
        " company ",
        " business ",
        " customer ",
        " client ",
        " efficiency ",
        " quality ",
        " development ",
        " contribution ",
        " contributions ",
        " contributed ",
        " improved ",
        " improve ",
        " reduced ",
        " reduce ",
        " increased ",
        " increase ",
        " outcome ",
        " result ",
        " impact ",
        " efficiency ",
        " effective ",
        " effectiveness ",
        " saved ",
        " save ",
        " accelerated ",
        " faster ",
        " improved accuracy ",
        " accuracy ",
        " reduced manual ",
        " automated ",
        " recognized ",
        " recognition ",
    )
    return any(marker in padded for marker in result_markers)


def apply_experience_fallback_strings(experiences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for experience in experiences:
        experience["content"] = join_rewritten_sentences(coerce_text_segments(experience.get("content", [])))
        experience["method"] = join_rewritten_sentences(coerce_text_segments(experience.get("method", [])))
        result_text = join_rewritten_sentences(coerce_text_segments(experience.get("result", [])))
        experience["result"] = result_text if looks_like_result(result_text) else ""
    return experiences


def experience_text_overlap(left: Any, right: Any) -> float:
    if isinstance(left, list) and isinstance(right, list):
        return list_overlap_score(left, right)
    if isinstance(left, str) and isinstance(right, str):
        return text_similarity(left, right)
    if isinstance(left, list) and isinstance(right, str):
        return max((text_similarity(item, right) for item in left if isinstance(item, str)), default=0.0)
    if isinstance(left, str) and isinstance(right, list):
        return max((text_similarity(left, item) for item in right if isinstance(item, str)), default=0.0)
    return 0.0


def refine_experience_with_evidence(
    client: OpenAI,
    document_text: str | None,
    extracted: dict[str, Any],
) -> dict[str, Any]:
    experiences = extracted.get("professional_experience")
    if not isinstance(experiences, list) or not experiences:
        return extracted
    if not document_text:
        extracted["professional_experience"] = apply_experience_fallback_strings(experiences)
        return extracted

    segments = split_into_source_segments(document_text)
    if not segments:
        extracted["professional_experience"] = apply_experience_fallback_strings(experiences)
        return extracted

    selection = client.chat.completions.parse(
        model=MODEL_NAME,
        temperature=0,
        messages=build_experience_evidence_messages(experiences, segments),
        response_format=ExperienceEvidenceSelection,
    )

    message = selection.choices[0].message
    if getattr(message, "refusal", None) or message.parsed is None:
        extracted["professional_experience"] = apply_experience_fallback_strings(experiences)
        return extracted

    items_by_index = {item.entry_index: item for item in message.parsed.items}
    rewrite_payload: list[dict[str, Any]] = []

    for index, experience in enumerate(experiences):
        evidence = items_by_index.get(index)
        content_segments = (
            [segments[segment_id] for segment_id in evidence.content_segment_ids if 0 <= segment_id < len(segments)]
            if evidence is not None
            else []
        )
        method_segments = (
            [segments[segment_id] for segment_id in evidence.method_segment_ids if 0 <= segment_id < len(segments)]
            if evidence is not None
            else []
        )
        result_segments = (
            [segments[segment_id] for segment_id in evidence.result_segment_ids if 0 <= segment_id < len(segments)]
            if evidence is not None
            else []
        )
        filtered_result_segments = [segment for segment in result_segments if looks_like_result(segment)]

        rewrite_payload.append(
            {
                "entry_index": index,
                "content_segments": dedupe_preserve_order(
                    content_segments or [item for item in experience.get("content", []) if isinstance(item, str)]
                ),
                "method_segments": dedupe_preserve_order(
                    method_segments or [item for item in experience.get("method", []) if isinstance(item, str)]
                ),
                "result_segments": dedupe_preserve_order(
                    filtered_result_segments
                    or result_segments
                    or [item for item in experience.get("result", []) if isinstance(item, str)]
                ),
            }
        )

    rewrite_payload = [
        item
        for item in rewrite_payload
        if item["content_segments"] or item["method_segments"] or item["result_segments"]
    ]
    if rewrite_payload:
        rewrite_response = client.chat.completions.parse(
            model=MODEL_NAME,
            temperature=0,
            messages=build_experience_rewrite_messages(rewrite_payload),
            response_format=ExperienceRewriteSelection,
        )

        rewrite_message = rewrite_response.choices[0].message
        rewritten_by_index = (
            {item.entry_index: item for item in rewrite_message.parsed.items}
            if getattr(rewrite_message, "refusal", None) is None and rewrite_message.parsed is not None
            else {}
        )
    else:
        rewritten_by_index = {}

    for index, experience in enumerate(experiences):
        rewritten = rewritten_by_index.get(index)
        if rewritten is not None:
            experience["content"] = join_rewritten_sentences([rewritten.content or ""])
            experience["method"] = join_rewritten_sentences([rewritten.method or ""])
            result_text = join_rewritten_sentences([rewritten.result or ""])
            experience["result"] = result_text if looks_like_result(result_text) else ""
        else:
            payload_item = next((item for item in rewrite_payload if item["entry_index"] == index), None)
            experience["content"] = join_rewritten_sentences(payload_item["content_segments"] if payload_item else [])
            experience["method"] = join_rewritten_sentences(payload_item["method_segments"] if payload_item else [])
            result_text = join_rewritten_sentences(payload_item["result_segments"] if payload_item else [])
            experience["result"] = result_text if looks_like_result(result_text) else ""

    extracted["professional_experience"] = experiences
    return extracted
