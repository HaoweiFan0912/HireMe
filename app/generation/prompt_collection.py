import json
from typing import Any


GENERAL_RESUME_SYSTEM_PROMPT = (
    "You are a grounded resume-writing agent. "
    "Transform a structured candidate profile into a concise, ATS-friendly US resume. "
    "Use only facts supported by the provided profile data. "
    "Never invent employers, job titles, metrics, tools, dates, projects, awards, degrees, or skills. "
    "You may compress, reorder, and rewrite wording for clarity and stronger resume style, "
    "but every claim must remain grounded in the source profile. "
    "Keep the result slightly conservative so a later tailoring step can still re-prioritize content. "
    "Return only the requested structured output."
)

GENERAL_RESUME_USER_PROMPT = (
    "Create a general-purpose resume from the structured profile below.\n\n"
    "Rules:\n"
    "1. Keep the resume broadly useful for internships or entry-level roles; do not overfit to one employer.\n"
    "2. Preserve chronology and factual consistency across dates, employers, schools, and locations.\n"
    "3. Use concise resume bullets, not paragraphs. Each bullet must describe only supported facts.\n"
    "4. Prefer specific, evidence-backed language over generic adjectives.\n"
    "5. Include a short summary only when the profile has enough evidence to justify it; otherwise return an empty summary list.\n"
    "6. For experience bullets, prioritize strongest accomplishments and methods. Avoid repeating the same fact in multiple bullets.\n"
    "7. For education, use bullets for GPA, honors, relevant coursework, or concentration only when present.\n"
    "8. Group skills into clear categories such as Languages, Programming, Data/ML, or Tools. Do not add unsupported skills.\n"
    "9. Activities are optional; include them only when they add useful evidence for a resume.\n"
    "10. Leave room for later tailoring. Do not stuff every possible keyword into the general version.\n"
)

TAILORED_BASELINE_SYSTEM_PROMPT = (
    "You are a grounded resume-tailoring agent. "
    "Tailor a candidate's resume to a target job description using only facts supported by the profile and base resume. "
    "Never invent missing experience, projects, tools, metrics, or qualifications. "
    "You may reorder, condense, omit lower-priority details, and mirror job-description wording only when the candidate's evidence supports it. "
    "Optimize for ATS relevance, factual accuracy, and readability. "
    "Return only the requested structured output."
)

TAILORED_BASELINE_USER_PROMPT = (
    "Tailor the resume to the target job description.\n\n"
    "Rules:\n"
    "1. Preserve every underlying fact from the structured profile and base resume. Do not fabricate qualifications.\n"
    "2. Emphasize the most relevant experience, methods, metrics, coursework, and skills for the job description.\n"
    "3. Mirror important job-description terminology only when the candidate genuinely has matching evidence.\n"
    "4. If a job requirement is unsupported or weakly supported, list it under `missing_requirements` instead of inventing it.\n"
    "5. Prefer stronger ordering, tighter bullets, and better keyword alignment over adding new content.\n"
    "6. Keep summary bullets targeted to the role when possible, but grounded in the profile.\n"
    "7. Keep the result ATS-friendly and concise.\n"
    "8. Populate `keywords_emphasized` with the most important JD terms you intentionally surfaced in the resume.\n"
)

JD_ANALYSIS_SYSTEM_PROMPT = (
    "You analyze job descriptions for resume tailoring. "
    "Extract recruiter-facing requirements and ATS-significant keywords from the job description only. "
    "Do not infer candidate evidence. Return only the requested structured output."
)

JD_ANALYSIS_USER_PROMPT = (
    "Analyze this target job description for downstream resume tailoring.\n\n"
    "Rules:\n"
    "1. Extract the most important explicit requirements and prioritize them.\n"
    "2. Separate must-have signals from nice-to-have signals whenever the JD supports that distinction.\n"
    "3. Keep keywords concise, ATS-meaningful noun phrases, ideally 1-4 words each.\n"
    "4. Set `target_sections` to the resume sections where each requirement would usually be evidenced.\n"
    "5. Prefer 5-8 must-have requirements and up to 6 nice-to-have requirements.\n"
    "6. `prioritized_sections` should order the resume sections by likely importance for this role.\n"
    "7. Do not use full-sentence job responsibilities as keywords.\n"
    "8. Prefer concrete technical phrases over broad umbrella terms like `software development` or soft skills like `collaboration` when the JD provides more specific language.\n"
)

EVIDENCE_ALIGNMENT_SYSTEM_PROMPT = (
    "You align candidate evidence to job requirements. "
    "Use only the candidate profile and base resume provided. "
    "Mark support as `strong`, `partial`, or `none`. "
    "If evidence is weak or absent, do not upgrade it. Return only the requested structured output."
)

EVIDENCE_ALIGNMENT_USER_PROMPT = (
    "Map candidate evidence to the analyzed job requirements.\n\n"
    "Rules:\n"
    "1. A requirement is `strong` only when the profile provides direct, specific support.\n"
    "2. A requirement is `partial` when the evidence is related but not fully equivalent.\n"
    "3. A requirement is `none` when the profile does not safely support it.\n"
    "4. `keywords_safe_to_emphasize` may include only JD keywords backed by strong or partial evidence.\n"
    "5. `missing_requirements` should list only real gaps or materially weak areas that the tailored resume must not fake.\n"
    "6. `prioritized_experience_titles`, `prioritized_skill_items`, and `prioritized_education_items` should surface the evidence most worth moving earlier in the tailored resume.\n"
    "7. Each evidence item must quote or tightly paraphrase factual source content from the candidate profile or base resume, not generic summaries.\n"
    "8. Normalize each `missing_requirements` item into a short gap label, not a full sentence copied from the JD.\n"
    "9. Do not treat an activity title by itself as evidence of responsibilities, mentoring scope, teaching scope, or technical work.\n"
    "10. Focus `missing_requirements` on genuine technical, domain, or tooling gaps. Do not restate graduation timing or general availability when that information is already explicit in the resume.\n"
)

TAILORED_DRAFT_SYSTEM_PROMPT = (
    "You draft tailored resumes from verified evidence. "
    "Use only the candidate profile, base resume, JD analysis, and evidence alignment provided. "
    "Never introduce unsupported claims. "
    "Only mirror keywords listed in `keywords_safe_to_emphasize`. "
    "Never infer responsibilities from a title alone. "
    "Do not upgrade verbs such as `built` into `designed`, `led`, `owned`, or `tested` unless the evidence explicitly supports that wording. "
    "Prefer reordering, pruning, and tightening over expansion. "
    "Return only the requested structured output."
)

TAILORED_DRAFT_USER_PROMPT = (
    "Draft a tailored resume.\n\n"
    "Rules:\n"
    "1. Use the base resume as the starting structure, but reorder sections and entries according to the evidence alignment.\n"
    "2. Only include bullets that can be justified by the candidate profile and aligned evidence.\n"
    "3. If a JD concept is unsupported, do not force it into bullets. Keep it in `missing_requirements` instead.\n"
    "4. `keywords_emphasized` must be a subset of `keywords_safe_to_emphasize` and each keyword should be a short ATS phrase, not a sentence.\n"
    "5. Use the strongest relevant experience first. If two experiences are relevant, order the more relevant one first.\n"
    "6. Keep summary bullets targeted and brief. Do not turn the summary into unsupported positioning or broad capability claims.\n"
    "7. For summary bullets, prefer direct evidence-backed statements like degree status, domain exposure, or named methods over abstract claims such as `hands-on experience building frameworks`.\n"
    "8. If an activity has no supporting description in the candidate profile, keep the entry without bullets instead of inventing responsibilities.\n"
    "9. Preserve factual strength. Do not intensify verbs unless the evidence explicitly supports the stronger wording.\n"
    "10. `missing_requirements` must contain short gap labels, not copied JD sentences.\n"
    "11. In the skills section, keep actual languages, libraries, and tools in tool-oriented groups. Put capability phrases like `feature engineering`, `customer analytics`, or `data pipeline development` in analytics or machine-learning groups instead.\n"
    "12. Prefer specific supported methods such as `sentence embeddings`, `reranking`, or `retrieval evaluation` over broad umbrella terms like `machine learning` when both are available.\n"
    "13. Do not list availability timing as a missing requirement unless it is an explicit blocking constraint that is not already visible elsewhere in the resume.\n"
    "14. Avoid repeated bullets, stuffed keywords, or generic filler phrases.\n"
    "15. Strategy should briefly explain how the JD was matched without mentioning unsupported claims.\n"
)

TAILORED_SAFETY_SYSTEM_PROMPT = (
    "You audit tailored resumes for groundedness and ATS-safe honesty. "
    "Compare the drafted resume against the candidate profile, JD analysis, and evidence alignment. "
    "Flag unsupported claims, duplicate bullets, empty bullets, and missing gap disclosures. "
    "Return only the requested structured output."
)

TAILORED_SAFETY_USER_PROMPT = (
    "Review this tailored resume draft for safety and groundedness.\n\n"
    "Rules:\n"
    "1. Flag every claim that is not clearly supported by the candidate profile or aligned evidence.\n"
    "2. Flag duplicate or near-duplicate bullets if they repeat the same factual content.\n"
    "3. Flag empty bullets or placeholder-like bullets.\n"
    "4. If the JD contains important unsupported requirements that are absent from `missing_requirements`, add them under `missing_gap_items`.\n"
    "5. `passes_safety` should be false whenever there is any unsupported claim, any empty bullet, or any major missing gap item.\n"
    "6. Flag summary bullets that generalize evidence into broader unsupported capability claims.\n"
    "7. Flag any experience bullet whose action verb is materially stronger than the source evidence.\n"
    "8. Flag any activity bullet that was inferred from a title, organization, or date without supporting description text.\n"
    "9. Flag `keywords_emphasized` or `missing_requirements` items that are full sentences or long JD fragments instead of short labels.\n"
    "10. Flag skills that are placed in the wrong type of skills group, such as capability phrases listed as tools.\n"
    "11. Flag overly generic keywords or skill labels when the resume already contains more specific supported methods.\n"
    "12. `revision_instructions` should be short, concrete edits that would fix the issues.\n"
)

TAILORED_REVISION_SYSTEM_PROMPT = (
    "You revise tailored resumes after a safety audit. "
    "Resolve every listed issue while staying strictly grounded in the provided evidence. "
    "Never introduce new unsupported claims. Return only the requested structured output."
)

TAILORED_REVISION_USER_PROMPT = (
    "Revise the tailored resume to satisfy the safety review.\n\n"
    "Rules:\n"
    "1. Remove or rewrite unsupported claims instead of softening them vaguely.\n"
    "2. Merge or delete duplicate bullets.\n"
    "3. Fill `missing_requirements` with the real unsupported requirements identified by the review.\n"
    "4. Preserve the strongest relevant evidence and the role-specific ordering where still valid.\n"
    "5. Keep `keywords_emphasized` limited to supported keywords only.\n"
    "6. Rewrite summary bullets into narrow, evidence-backed statements; delete them if that is not possible.\n"
    "7. Remove any activity bullet that depends on title-only inference.\n"
    "8. Normalize `keywords_emphasized` and `missing_requirements` into short phrases rather than sentences.\n"
    "9. Replace inflated verbs with the strongest wording that is still directly supported by the source evidence.\n"
    "10. Move capability phrases out of tool groups and keep the skills section specific rather than generic.\n"
    "11. Remove availability-style gap items unless they are genuine blockers not already shown elsewhere in the resume.\n"
)

RESUME_JUDGE_SYSTEM_PROMPT = (
    "You are a strict resume evaluator. "
    "Score a generated resume against the provided job description, candidate profile, and rubric. "
    "Do not forgive unsupported claims. Return only the requested structured output."
)

RESUME_JUDGE_USER_PROMPT = (
    "Evaluate this generated resume using the rubric below.\n\n"
    "Scoring rubric:\n"
    "- groundedness: 0-5, where 5 means every claim is traceable to the profile.\n"
    "- jd_alignment: 0-5, where 5 means the resume clearly matches the most important JD requirements.\n"
    "- prioritization: 0-5, where 5 means the most relevant sections and evidence are surfaced first.\n"
    "- resume_quality: 0-5, where 5 means concise, professional, non-redundant bullets.\n"
    "- gap_handling: 0-5, where 5 means unsupported requirements are handled honestly without fabrication.\n"
    "Keep rationale short and specific.\n"
)


def _json_block(label: str, value: Any) -> str:
    return f"{label}:\n{json.dumps(value, ensure_ascii=False, indent=2)}"


def build_candidate_evidence_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    basics = record.get("basics", {})
    education = record.get("education", [])
    experience = record.get("professional_experience", [])
    activities = record.get("activities", [])
    skills = record.get("skills", {})

    return {
        "basics": {
            "full_name": basics.get("full_name", ""),
            "email": basics.get("email", ""),
            "links": [
                f"{item.get('label', '').strip()}: {item.get('url', '').strip()}"
                for item in basics.get("links", [])
                if isinstance(item, dict)
            ],
            "locations": [
                " | ".join(
                    part
                    for part in [
                        address.get("city", ""),
                        address.get("state_or_province", ""),
                        address.get("country", ""),
                    ]
                    if isinstance(part, str) and part.strip()
                )
                for address in [basics.get("current_address", {}), basics.get("permanent_address", {})]
                if isinstance(address, dict)
            ],
        },
        "education": [
            {
                "entry_name": entry.get("institution", ""),
                "degree": entry.get("degree", ""),
                "date_range": " - ".join(
                    part for part in [entry.get("start_date", ""), entry.get("end_date", "")] if isinstance(part, str) and part.strip()
                ),
                "majors_or_programs": entry.get("majors_or_programs", []),
                "courses": entry.get("courses", []),
                "honors": entry.get("honors", []),
                "gpa": entry.get("gpa", ""),
            }
            for entry in education
            if isinstance(entry, dict)
        ],
        "professional_experience": [
            {
                "entry_name": entry.get("company", ""),
                "job_title": entry.get("job_title", ""),
                "date_range": " - ".join(
                    part for part in [entry.get("start_date", ""), entry.get("end_date", "")] if isinstance(part, str) and part.strip()
                ),
                "evidence": [
                    text
                    for text in [entry.get("content", ""), entry.get("method", ""), entry.get("result", "")]
                    if isinstance(text, str) and text.strip()
                ],
            }
            for entry in experience
            if isinstance(entry, dict)
        ],
        "skills": {
            "languages": skills.get("languages", []),
            "computer": skills.get("computer", []),
        },
        "activities": [
            {
                "entry_name": entry.get("organization", ""),
                "role": entry.get("role", ""),
                "date_range": " - ".join(
                    part for part in [entry.get("start_date", ""), entry.get("end_date", "")] if isinstance(part, str) and part.strip()
                ),
                "description": entry.get("description", []),
            }
            for entry in activities
            if isinstance(entry, dict)
        ],
    }


def build_general_resume_messages(
    record: dict[str, Any],
    target_role: str | None = None,
) -> list[dict[str, str]]:
    prompt_parts = [GENERAL_RESUME_USER_PROMPT]
    if isinstance(target_role, str) and target_role.strip():
        prompt_parts.append(f"Optional focus role:\n{target_role.strip()}\n")
    prompt_parts.append(_json_block("Structured candidate profile", record))
    return [
        {"role": "system", "content": GENERAL_RESUME_SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(prompt_parts)},
    ]


def build_tailored_resume_baseline_messages(
    record: dict[str, Any],
    base_resume: dict[str, Any],
    job_description: str,
    target_role: str | None = None,
) -> list[dict[str, str]]:
    prompt_parts = [TAILORED_BASELINE_USER_PROMPT]
    if isinstance(target_role, str) and target_role.strip():
        prompt_parts.append(f"Target role:\n{target_role.strip()}\n")
    prompt_parts.extend(
        [
            f"Job description:\n{job_description.strip()}",
            _json_block("Structured candidate profile", record),
            _json_block("Base resume", base_resume),
        ]
    )
    return [
        {"role": "system", "content": TAILORED_BASELINE_SYSTEM_PROMPT},
        {"role": "user", "content": "\n\n".join(prompt_parts)},
    ]


def build_jd_analysis_messages(
    job_description: str,
    target_role: str | None = None,
) -> list[dict[str, str]]:
    prompt_parts = [JD_ANALYSIS_USER_PROMPT]
    if isinstance(target_role, str) and target_role.strip():
        prompt_parts.append(f"Stated target role:\n{target_role.strip()}\n")
    prompt_parts.append(f"Job description:\n{job_description.strip()}")
    return [
        {"role": "system", "content": JD_ANALYSIS_SYSTEM_PROMPT},
        {"role": "user", "content": "\n\n".join(prompt_parts)},
    ]


def build_evidence_alignment_messages(
    record: dict[str, Any],
    base_resume: dict[str, Any],
    jd_analysis: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": EVIDENCE_ALIGNMENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "\n\n".join(
                [
                    EVIDENCE_ALIGNMENT_USER_PROMPT,
                    _json_block("JD analysis", jd_analysis),
                    _json_block("Candidate evidence snapshot", build_candidate_evidence_snapshot(record)),
                    _json_block("Base resume", base_resume),
                ]
            ),
        },
    ]


def build_tailored_draft_messages(
    record: dict[str, Any],
    base_resume: dict[str, Any],
    jd_analysis: dict[str, Any],
    evidence_alignment: dict[str, Any],
    target_role: str | None = None,
) -> list[dict[str, str]]:
    prompt_parts = [TAILORED_DRAFT_USER_PROMPT]
    if isinstance(target_role, str) and target_role.strip():
        prompt_parts.append(f"Target role:\n{target_role.strip()}\n")
    prompt_parts.extend(
        [
            _json_block("JD analysis", jd_analysis),
            _json_block("Evidence alignment", evidence_alignment),
            _json_block("Candidate evidence snapshot", build_candidate_evidence_snapshot(record)),
            _json_block("Base resume", base_resume),
        ]
    )
    return [
        {"role": "system", "content": TAILORED_DRAFT_SYSTEM_PROMPT},
        {"role": "user", "content": "\n\n".join(prompt_parts)},
    ]


def build_tailored_safety_messages(
    record: dict[str, Any],
    job_description: str,
    jd_analysis: dict[str, Any],
    evidence_alignment: dict[str, Any],
    tailored_resume: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": TAILORED_SAFETY_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "\n\n".join(
                [
                    TAILORED_SAFETY_USER_PROMPT,
                    f"Job description:\n{job_description.strip()}",
                    _json_block("JD analysis", jd_analysis),
                    _json_block("Evidence alignment", evidence_alignment),
                    _json_block("Candidate evidence snapshot", build_candidate_evidence_snapshot(record)),
                    _json_block("Tailored resume draft", tailored_resume),
                ]
            ),
        },
    ]


def build_tailored_revision_messages(
    record: dict[str, Any],
    base_resume: dict[str, Any],
    jd_analysis: dict[str, Any],
    evidence_alignment: dict[str, Any],
    tailored_resume: dict[str, Any],
    safety_review: dict[str, Any],
    target_role: str | None = None,
) -> list[dict[str, str]]:
    prompt_parts = [TAILORED_REVISION_USER_PROMPT]
    if isinstance(target_role, str) and target_role.strip():
        prompt_parts.append(f"Target role:\n{target_role.strip()}\n")
    prompt_parts.extend(
        [
            _json_block("JD analysis", jd_analysis),
            _json_block("Evidence alignment", evidence_alignment),
            _json_block("Candidate evidence snapshot", build_candidate_evidence_snapshot(record)),
            _json_block("Base resume", base_resume),
            _json_block("Tailored resume draft", tailored_resume),
            _json_block("Safety review", safety_review),
        ]
    )
    return [
        {"role": "system", "content": TAILORED_REVISION_SYSTEM_PROMPT},
        {"role": "user", "content": "\n\n".join(prompt_parts)},
    ]


def build_resume_judge_messages(
    record: dict[str, Any],
    job_description: str,
    generated_resume: dict[str, Any],
    expected_missing_requirements: list[str],
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": RESUME_JUDGE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "\n\n".join(
                [
                    RESUME_JUDGE_USER_PROMPT,
                    f"Job description:\n{job_description.strip()}",
                    _json_block("Candidate evidence snapshot", build_candidate_evidence_snapshot(record)),
                    _json_block("Expected missing requirements", expected_missing_requirements),
                    _json_block("Generated resume", generated_resume),
                ]
            ),
        },
    ]
