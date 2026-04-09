from dataclasses import dataclass
import re
from typing import Any

from openai import OpenAI
from pydantic import BaseModel

from app.extraction.client import create_client
from app.extraction.common import MODEL_NAME
from app.generation.models import (
    EvidenceAlignmentSelection,
    GeneralResumeGeneration,
    GeneratedResumeDocument,
    JDRequirementAnalysis,
    ResumeJudgeEvaluation,
    ResumeSectionEntry,
    ResumeSkillsGroup,
    TailoredResumeGeneration,
    TailoredResumeSafetyReview,
)
from app.generation.prompt_collection import (
    build_evidence_alignment_messages,
    build_general_resume_messages,
    build_jd_analysis_messages,
    build_resume_judge_messages,
    build_tailored_draft_messages,
    build_tailored_resume_baseline_messages,
    build_tailored_revision_messages,
    build_tailored_safety_messages,
)


@dataclass
class TailoredResumePipelineArtifacts:
    base_resume: GeneralResumeGeneration
    jd_analysis: JDRequirementAnalysis
    evidence_alignment: EvidenceAlignmentSelection
    initial_resume: TailoredResumeGeneration
    initial_safety_review: TailoredResumeSafetyReview
    final_resume: TailoredResumeGeneration
    final_safety_review: TailoredResumeSafetyReview


def _parse_chat_completion(
    *,
    client: OpenAI,
    response_model: type[BaseModel],
    messages: list[dict[str, str]],
) -> BaseModel:
    completion = client.chat.completions.parse(
        model=MODEL_NAME,
        temperature=0,
        messages=messages,
        response_format=response_model,
    )
    message = completion.choices[0].message
    if getattr(message, "refusal", None):
        raise ValueError(f"The model refused to generate the resume: {message.refusal}")
    if message.parsed is None:
        raise ValueError("The model did not return a parseable resume result.")
    return message.parsed


def _resolve_base_resume(
    *,
    client: OpenAI,
    record: dict[str, Any],
    target_role: str | None,
    base_resume: GeneralResumeGeneration | dict[str, Any] | None,
) -> GeneralResumeGeneration:
    if base_resume is None:
        parsed = _parse_chat_completion(
            client=client,
            response_model=GeneralResumeGeneration,
            messages=build_general_resume_messages(record, target_role=target_role),
        )
        return GeneralResumeGeneration.model_validate(parsed)

    if isinstance(base_resume, GeneralResumeGeneration):
        return base_resume

    return GeneralResumeGeneration.model_validate(base_resume)


def _analyze_job_description(
    *,
    client: OpenAI,
    job_description: str,
    target_role: str | None,
) -> JDRequirementAnalysis:
    parsed = _parse_chat_completion(
        client=client,
        response_model=JDRequirementAnalysis,
        messages=build_jd_analysis_messages(job_description, target_role=target_role),
    )
    return JDRequirementAnalysis.model_validate(parsed)


def _align_candidate_evidence(
    *,
    client: OpenAI,
    record: dict[str, Any],
    base_resume: GeneralResumeGeneration,
    jd_analysis: JDRequirementAnalysis,
) -> EvidenceAlignmentSelection:
    parsed = _parse_chat_completion(
        client=client,
        response_model=EvidenceAlignmentSelection,
        messages=build_evidence_alignment_messages(
            record,
            base_resume.model_dump(mode="json"),
            jd_analysis.model_dump(mode="json"),
        ),
    )
    return EvidenceAlignmentSelection.model_validate(parsed)


def _draft_tailored_resume(
    *,
    client: OpenAI,
    record: dict[str, Any],
    base_resume: GeneralResumeGeneration,
    jd_analysis: JDRequirementAnalysis,
    evidence_alignment: EvidenceAlignmentSelection,
    target_role: str | None,
) -> TailoredResumeGeneration:
    parsed = _parse_chat_completion(
        client=client,
        response_model=TailoredResumeGeneration,
        messages=build_tailored_draft_messages(
            record,
            base_resume.model_dump(mode="json"),
            jd_analysis.model_dump(mode="json"),
            evidence_alignment.model_dump(mode="json"),
            target_role=target_role,
        ),
    )
    return TailoredResumeGeneration.model_validate(parsed)


def review_tailored_resume_output(
    record: dict[str, Any],
    job_description: str,
    *,
    api_key_override: str | None = None,
    jd_analysis: JDRequirementAnalysis,
    evidence_alignment: EvidenceAlignmentSelection,
    tailored_resume: TailoredResumeGeneration,
) -> TailoredResumeSafetyReview:
    client = create_client(api_key_override)
    parsed = _parse_chat_completion(
        client=client,
        response_model=TailoredResumeSafetyReview,
        messages=build_tailored_safety_messages(
            record,
            job_description,
            jd_analysis.model_dump(mode="json"),
            evidence_alignment.model_dump(mode="json"),
            tailored_resume.model_dump(mode="json"),
        ),
    )
    return TailoredResumeSafetyReview.model_validate(parsed)


def _review_tailored_resume_with_client(
    *,
    client: OpenAI,
    record: dict[str, Any],
    job_description: str,
    jd_analysis: JDRequirementAnalysis,
    evidence_alignment: EvidenceAlignmentSelection,
    tailored_resume: TailoredResumeGeneration,
) -> TailoredResumeSafetyReview:
    parsed = _parse_chat_completion(
        client=client,
        response_model=TailoredResumeSafetyReview,
        messages=build_tailored_safety_messages(
            record,
            job_description,
            jd_analysis.model_dump(mode="json"),
            evidence_alignment.model_dump(mode="json"),
            tailored_resume.model_dump(mode="json"),
        ),
    )
    return TailoredResumeSafetyReview.model_validate(parsed)


def _revise_tailored_resume(
    *,
    client: OpenAI,
    record: dict[str, Any],
    base_resume: GeneralResumeGeneration,
    jd_analysis: JDRequirementAnalysis,
    evidence_alignment: EvidenceAlignmentSelection,
    tailored_resume: TailoredResumeGeneration,
    safety_review: TailoredResumeSafetyReview,
    target_role: str | None,
) -> TailoredResumeGeneration:
    parsed = _parse_chat_completion(
        client=client,
        response_model=TailoredResumeGeneration,
        messages=build_tailored_revision_messages(
            record,
            base_resume.model_dump(mode="json"),
            jd_analysis.model_dump(mode="json"),
            evidence_alignment.model_dump(mode="json"),
            tailored_resume.model_dump(mode="json"),
            safety_review.model_dump(mode="json"),
            target_role=target_role,
        ),
    )
    return TailoredResumeGeneration.model_validate(parsed)


def _clean_label_items(
    items: list[str],
    *,
    max_words: int,
    max_items: int,
) -> list[str]:
    cleaned_items: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, str):
            continue
        cleaned = " ".join(item.replace("\n", " ").split()).strip(" -•\t")
        cleaned = cleaned.strip("\"'`")
        cleaned = cleaned.rstrip(".,;:")
        if not cleaned:
            continue
        if any(punct in cleaned for punct in ".!?"):
            continue
        if len(cleaned.split()) > max_words:
            continue
        normalized = cleaned.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned_items.append(cleaned)
        if len(cleaned_items) >= max_items:
            break
    return cleaned_items


def _trim_strategy_text(strategy: str | None) -> str | None:
    if not isinstance(strategy, str):
        return None
    cleaned = " ".join(strategy.split()).strip()
    if not cleaned:
        return None
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    shortened = " ".join(sentences[:3]).strip()
    return shortened[:320].rstrip()


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = " ".join(item.split()).strip()
        if not cleaned:
            continue
        normalized = cleaned.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(cleaned)
    return deduped


def _is_logistics_gap_item(item: str) -> bool:
    lowered = item.casefold()
    logistics_markers = (
        "availability",
        "graduation",
        "graduate date",
        "expected graduation",
        "currently enrolled",
        "start date",
        "summer 2026",
    )
    return any(marker in lowered for marker in logistics_markers)


def _normalize_missing_requirements(items: list[str]) -> list[str]:
    cleaned = _clean_label_items(items, max_words=6, max_items=10)
    return [item for item in cleaned if not _is_logistics_gap_item(item)]


def _normalize_keywords_emphasized(items: list[str]) -> list[str]:
    return _clean_label_items(items, max_words=4, max_items=12)


def _normalize_skill_groups(groups: list[ResumeSkillsGroup]) -> list[ResumeSkillsGroup]:
    allowed_multiword_tools = {
        "power bi",
        "google cloud",
        "amazon web services",
        "microsoft excel",
    }
    capability_items_to_move: list[str] = []
    normalized_groups: list[ResumeSkillsGroup] = []

    for group in groups:
        label = group.label.strip()
        items = _dedupe_preserve_order(group.items)
        label_lower = label.casefold()
        is_tool_group = "programming" in label_lower or "tool" in label_lower
        if is_tool_group:
            kept_items: list[str] = []
            moved_items: list[str] = []
            for item in items:
                normalized = item.casefold()
                if " " in normalized and normalized not in allowed_multiword_tools:
                    moved_items.append(item)
                else:
                    kept_items.append(item)
            capability_items_to_move.extend(moved_items)
            items = kept_items
        if items:
            normalized_groups.append(ResumeSkillsGroup(label=label, items=items))

    if capability_items_to_move:
        capability_label_index = next(
            (
                index
                for index, group in enumerate(normalized_groups)
                if any(token in group.label.casefold() for token in ("machine learning", "data science", "analytics"))
            ),
            None,
        )
        if capability_label_index is None:
            normalized_groups.append(
                ResumeSkillsGroup(
                    label="Machine Learning & Data Science",
                    items=_dedupe_preserve_order(capability_items_to_move),
                )
            )
        else:
            merged_items = _dedupe_preserve_order(
                normalized_groups[capability_label_index].items + capability_items_to_move
            )
            normalized_groups[capability_label_index] = ResumeSkillsGroup(
                label=normalized_groups[capability_label_index].label,
                items=merged_items,
            )

    for index, group in enumerate(normalized_groups):
        label_lower = group.label.casefold()
        if any(token in label_lower for token in ("machine learning", "data science", "analytics")):
            specific_items = [
                item
                for item in group.items
                if item.casefold() not in {"machine learning", "software development", "collaboration"}
            ]
            if len(specific_items) >= 2:
                normalized_groups[index] = ResumeSkillsGroup(
                    label=group.label,
                    items=specific_items,
                )

    return normalized_groups


def _build_activity_support_index(record: dict[str, Any]) -> dict[tuple[str, str], bool]:
    support_index: dict[tuple[str, str], bool] = {}
    for activity in record.get("activities", []):
        if not isinstance(activity, dict):
            continue
        role = str(activity.get("role", "")).strip().casefold()
        organization = str(activity.get("organization", "")).strip().casefold()
        descriptions = activity.get("description", [])
        has_description = isinstance(descriptions, list) and any(
            isinstance(item, str) and item.strip() for item in descriptions
        )
        support_index[(role, organization)] = has_description
    return support_index


def _prune_unsupported_activity_bullets(
    *,
    record: dict[str, Any],
    resume: TailoredResumeGeneration,
) -> None:
    support_index = _build_activity_support_index(record)
    for entry in resume.resume.activities:
        role = entry.title.strip().casefold()
        organization = (entry.subtitle or "").strip().casefold()
        has_source_description = support_index.get((role, organization))
        if has_source_description is False:
            entry.bullets = []


def _sanitize_tailored_resume_generation(
    *,
    record: dict[str, Any],
    generation: TailoredResumeGeneration,
) -> TailoredResumeGeneration:
    sanitized = TailoredResumeGeneration.model_validate(generation.model_dump(mode="json"))
    sanitized.strategy = _trim_strategy_text(sanitized.strategy)
    sanitized.keywords_emphasized = _normalize_keywords_emphasized(sanitized.keywords_emphasized)
    sanitized.missing_requirements = _normalize_missing_requirements(sanitized.missing_requirements)
    sanitized.resume.skills = _normalize_skill_groups(sanitized.resume.skills)
    _prune_unsupported_activity_bullets(record=record, resume=sanitized)
    return sanitized


def generate_general_resume_from_record(
    record: dict[str, Any],
    *,
    target_role: str | None = None,
    api_key_override: str | None = None,
) -> GeneralResumeGeneration:
    client = create_client(api_key_override)
    parsed = _parse_chat_completion(
        client=client,
        response_model=GeneralResumeGeneration,
        messages=build_general_resume_messages(record, target_role=target_role),
    )
    return GeneralResumeGeneration.model_validate(parsed)


def tailor_resume_to_job_description_baseline(
    record: dict[str, Any],
    job_description: str,
    *,
    target_role: str | None = None,
    api_key_override: str | None = None,
    base_resume: GeneralResumeGeneration | dict[str, Any] | None = None,
) -> TailoredResumeGeneration:
    cleaned_job_description = (job_description or "").strip()
    if not cleaned_job_description:
        raise ValueError("`job_description` is required for resume tailoring.")

    client = create_client(api_key_override)
    base_resume_model = _resolve_base_resume(
        client=client,
        record=record,
        target_role=target_role,
        base_resume=base_resume,
    )

    parsed = _parse_chat_completion(
        client=client,
        response_model=TailoredResumeGeneration,
        messages=build_tailored_resume_baseline_messages(
            record,
            base_resume_model.model_dump(mode="json"),
            cleaned_job_description,
            target_role=target_role,
        ),
    )
    return _sanitize_tailored_resume_generation(
        record=record,
        generation=TailoredResumeGeneration.model_validate(parsed),
    )


def run_tailored_resume_pipeline(
    record: dict[str, Any],
    job_description: str,
    *,
    target_role: str | None = None,
    api_key_override: str | None = None,
    base_resume: GeneralResumeGeneration | dict[str, Any] | None = None,
) -> TailoredResumePipelineArtifacts:
    cleaned_job_description = (job_description or "").strip()
    if not cleaned_job_description:
        raise ValueError("`job_description` is required for resume tailoring.")

    client = create_client(api_key_override)
    base_resume_model = _resolve_base_resume(
        client=client,
        record=record,
        target_role=target_role,
        base_resume=base_resume,
    )
    jd_analysis = _analyze_job_description(
        client=client,
        job_description=cleaned_job_description,
        target_role=target_role,
    )
    evidence_alignment = _align_candidate_evidence(
        client=client,
        record=record,
        base_resume=base_resume_model,
        jd_analysis=jd_analysis,
    )
    initial_resume = _draft_tailored_resume(
        client=client,
        record=record,
        base_resume=base_resume_model,
        jd_analysis=jd_analysis,
        evidence_alignment=evidence_alignment,
        target_role=target_role,
    )
    initial_resume = _sanitize_tailored_resume_generation(
        record=record,
        generation=initial_resume,
    )
    initial_safety_review = _review_tailored_resume_with_client(
        client=client,
        record=record,
        job_description=cleaned_job_description,
        jd_analysis=jd_analysis,
        evidence_alignment=evidence_alignment,
        tailored_resume=initial_resume,
    )

    final_resume = initial_resume
    final_safety_review = initial_safety_review
    needs_revision = (
        not initial_safety_review.passes_safety
        or bool(initial_safety_review.unsupported_claims)
        or bool(initial_safety_review.empty_bullets)
        or bool(initial_safety_review.missing_gap_items)
    )
    if needs_revision:
        final_resume = _revise_tailored_resume(
            client=client,
            record=record,
            base_resume=base_resume_model,
            jd_analysis=jd_analysis,
            evidence_alignment=evidence_alignment,
            tailored_resume=initial_resume,
            safety_review=initial_safety_review,
            target_role=target_role,
        )
        final_resume = _sanitize_tailored_resume_generation(
            record=record,
            generation=final_resume,
        )
        final_safety_review = _review_tailored_resume_with_client(
            client=client,
            record=record,
            job_description=cleaned_job_description,
            jd_analysis=jd_analysis,
            evidence_alignment=evidence_alignment,
            tailored_resume=final_resume,
        )

    return TailoredResumePipelineArtifacts(
        base_resume=base_resume_model,
        jd_analysis=jd_analysis,
        evidence_alignment=evidence_alignment,
        initial_resume=initial_resume,
        initial_safety_review=initial_safety_review,
        final_resume=final_resume,
        final_safety_review=final_safety_review,
    )


def tailor_resume_to_job_description(
    record: dict[str, Any],
    job_description: str,
    *,
    target_role: str | None = None,
    api_key_override: str | None = None,
    base_resume: GeneralResumeGeneration | dict[str, Any] | None = None,
) -> TailoredResumeGeneration:
    artifacts = run_tailored_resume_pipeline(
        record,
        job_description,
        target_role=target_role,
        api_key_override=api_key_override,
        base_resume=base_resume,
    )
    return artifacts.final_resume


def judge_generated_resume(
    record: dict[str, Any],
    job_description: str,
    generated_resume: GeneralResumeGeneration | TailoredResumeGeneration | dict[str, Any],
    *,
    expected_missing_requirements: list[str] | None = None,
    api_key_override: str | None = None,
) -> ResumeJudgeEvaluation:
    if isinstance(generated_resume, (GeneralResumeGeneration, TailoredResumeGeneration)):
        generated_payload = generated_resume.model_dump(mode="json")
    else:
        generated_payload = generated_resume

    client = create_client(api_key_override)
    parsed = _parse_chat_completion(
        client=client,
        response_model=ResumeJudgeEvaluation,
        messages=build_resume_judge_messages(
            record,
            job_description,
            generated_payload,
            expected_missing_requirements or [],
        ),
    )
    return ResumeJudgeEvaluation.model_validate(parsed)


def _compact_parts(parts: list[str | None]) -> str | None:
    cleaned = [part.strip() for part in parts if isinstance(part, str) and part.strip()]
    return " | ".join(cleaned) if cleaned else None


def _render_section_entries(entries: list[ResumeSectionEntry]) -> list[str]:
    lines: list[str] = []
    for entry in entries:
        lines.append(entry.title)
        detail_line = _compact_parts([entry.subtitle, entry.location, entry.date_range])
        if detail_line:
            lines.append(detail_line)
        for bullet in entry.bullets:
            bullet_text = bullet.strip()
            if bullet_text:
                lines.append(f"- {bullet_text}")
        lines.append("")
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _render_skills_groups(groups: list[ResumeSkillsGroup]) -> list[str]:
    lines: list[str] = []
    for group in groups:
        items = [item.strip() for item in group.items if isinstance(item, str) and item.strip()]
        if items:
            lines.append(f"{group.label}: {', '.join(items)}")
    return lines


def render_resume_document(document: GeneratedResumeDocument) -> str:
    lines = [document.header.full_name]

    contact_line = _compact_parts(
        [
            document.header.email,
            document.header.location,
            " | ".join(document.header.links) if document.header.links else None,
        ]
    )
    if contact_line:
        lines.append(contact_line)

    def append_section(title: str, body_lines: list[str]) -> None:
        if not body_lines:
            return
        lines.extend(["", title])
        lines.extend(body_lines)

    append_section("SUMMARY", [f"- {item}" for item in document.summary if item.strip()])
    append_section("EDUCATION", _render_section_entries(document.education))
    append_section("PROFESSIONAL EXPERIENCE", _render_section_entries(document.professional_experience))
    append_section("SKILLS", _render_skills_groups(document.skills))
    append_section("ACTIVITIES", _render_section_entries(document.activities))

    return "\n".join(lines).strip()
