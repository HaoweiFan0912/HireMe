from pydantic import BaseModel, Field


class ResumeHeader(BaseModel):
    full_name: str
    email: str | None = None
    location: str | None = None
    links: list[str] = Field(default_factory=list)


class ResumeSectionEntry(BaseModel):
    title: str
    subtitle: str | None = None
    location: str | None = None
    date_range: str | None = None
    bullets: list[str] = Field(default_factory=list)


class ResumeSkillsGroup(BaseModel):
    label: str
    items: list[str] = Field(default_factory=list)


class GeneratedResumeDocument(BaseModel):
    header: ResumeHeader
    summary: list[str] = Field(default_factory=list)
    education: list[ResumeSectionEntry] = Field(default_factory=list)
    professional_experience: list[ResumeSectionEntry] = Field(default_factory=list)
    skills: list[ResumeSkillsGroup] = Field(default_factory=list)
    activities: list[ResumeSectionEntry] = Field(default_factory=list)


class GeneralResumeGeneration(BaseModel):
    strategy: str | None = None
    resume: GeneratedResumeDocument


class TailoredResumeGeneration(BaseModel):
    strategy: str | None = None
    keywords_emphasized: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    resume: GeneratedResumeDocument


class JDRequirementItem(BaseModel):
    requirement_id: str
    requirement_text: str
    importance: str
    keywords: list[str] = Field(default_factory=list)
    target_sections: list[str] = Field(default_factory=list)


class JDRequirementAnalysis(BaseModel):
    role_title: str | None = None
    company_name: str | None = None
    role_summary: str | None = None
    must_have_requirements: list[JDRequirementItem] = Field(default_factory=list)
    nice_to_have_requirements: list[JDRequirementItem] = Field(default_factory=list)
    top_keywords: list[str] = Field(default_factory=list)
    prioritized_sections: list[str] = Field(default_factory=list)


class EvidenceReference(BaseModel):
    source_section: str
    source_label: str
    evidence_text: str


class RequirementEvidenceAlignment(BaseModel):
    requirement_id: str
    requirement_text: str
    support_level: str
    matched_keywords: list[str] = Field(default_factory=list)
    target_sections: list[str] = Field(default_factory=list)
    evidence: list[EvidenceReference] = Field(default_factory=list)
    note: str | None = None


class EvidenceAlignmentSelection(BaseModel):
    aligned_requirements: list[RequirementEvidenceAlignment] = Field(default_factory=list)
    keywords_safe_to_emphasize: list[str] = Field(default_factory=list)
    prioritized_experience_titles: list[str] = Field(default_factory=list)
    prioritized_skill_items: list[str] = Field(default_factory=list)
    prioritized_education_items: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    tailoring_focus: list[str] = Field(default_factory=list)


class UnsupportedClaimItem(BaseModel):
    claim_text: str
    reason: str


class TailoredResumeSafetyReview(BaseModel):
    passes_safety: bool = True
    unsupported_claims: list[UnsupportedClaimItem] = Field(default_factory=list)
    duplicate_bullets: list[str] = Field(default_factory=list)
    empty_bullets: list[str] = Field(default_factory=list)
    missing_gap_items: list[str] = Field(default_factory=list)
    revision_instructions: list[str] = Field(default_factory=list)


class ResumeJudgeEvaluation(BaseModel):
    groundedness: int
    jd_alignment: int
    prioritization: int
    resume_quality: int
    gap_handling: int
    rationale: str
