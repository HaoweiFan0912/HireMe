from pydantic import BaseModel, Field


class ExtractedLink(BaseModel):
    label: str | None = None
    url: str | None = None


class ExtractedAddress(BaseModel):
    city: str | None = None
    state_or_province: str | None = None
    country: str | None = None
    postal_code: str | None = None
    phone: str | None = None


class ExtractedBasics(BaseModel):
    full_name: str | None = None
    email: str | None = None
    links: list[ExtractedLink] = Field(default_factory=list)
    permanent_address: ExtractedAddress | None = None
    current_address: ExtractedAddress | None = None


class ExtractedEducationEntry(BaseModel):
    institution: str | None = None
    city: str | None = None
    state_or_province: str | None = None
    country: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    degree: str | None = None
    majors_or_programs: list[str] = Field(default_factory=list)
    courses: list[str] = Field(default_factory=list)
    gpa: str | None = None
    honors: list[str] = Field(default_factory=list)


class ExtractedExperienceEntry(BaseModel):
    company: str | None = None
    city: str | None = None
    state_or_province: str | None = None
    country: str | None = None
    job_title: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool | None = None
    content: list[str] = Field(default_factory=list)
    method: list[str] = Field(default_factory=list)
    result: list[str] = Field(default_factory=list)


class ExtractedSkills(BaseModel):
    languages: list[str] = Field(default_factory=list)
    computer: list[str] = Field(default_factory=list)


class ExtractedActivityEntry(BaseModel):
    role: str | None = None
    organization: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    description: list[str] = Field(default_factory=list)


class ExtractedResumeSchema(BaseModel):
    basics: ExtractedBasics | None = None
    education: list[ExtractedEducationEntry] = Field(default_factory=list)
    professional_experience: list[ExtractedExperienceEntry] = Field(default_factory=list)
    skills: ExtractedSkills | None = None
    activities: list[ExtractedActivityEntry] = Field(default_factory=list)


class ExperienceEvidenceItem(BaseModel):
    entry_index: int
    content_segment_ids: list[int] = Field(default_factory=list)
    method_segment_ids: list[int] = Field(default_factory=list)
    result_segment_ids: list[int] = Field(default_factory=list)


class ExperienceEvidenceSelection(BaseModel):
    items: list[ExperienceEvidenceItem] = Field(default_factory=list)


class ExperienceRewriteItem(BaseModel):
    entry_index: int
    content: str | None = None
    method: str | None = None
    result: str | None = None


class ExperienceRewriteSelection(BaseModel):
    items: list[ExperienceRewriteItem] = Field(default_factory=list)


class EducationLocationLookupItem(BaseModel):
    entry_index: int
    city: str | None = None
    state_or_province: str | None = None
    country: str | None = None
    campus_name: str | None = None


class EducationLocationLookupSelection(BaseModel):
    items: list[EducationLocationLookupItem] = Field(default_factory=list)


class EntityFullNameLookupItem(BaseModel):
    entry_type: str
    entry_index: int
    full_name: str | None = None


class EntityFullNameLookupSelection(BaseModel):
    items: list[EntityFullNameLookupItem] = Field(default_factory=list)


class EducationHonorsRewriteItem(BaseModel):
    entry_index: int
    honors: list[str] = Field(default_factory=list)


class EducationHonorsRewriteSelection(BaseModel):
    items: list[EducationHonorsRewriteItem] = Field(default_factory=list)


class EducationCoursesRewriteItem(BaseModel):
    entry_index: int
    courses: list[str] = Field(default_factory=list)


class EducationCoursesRewriteSelection(BaseModel):
    items: list[EducationCoursesRewriteItem] = Field(default_factory=list)


class ExperienceLocationLookupItem(BaseModel):
    entry_index: int
    city: str | None = None
    state_or_province: str | None = None
    country: str | None = None
    location_name: str | None = None


class ExperienceLocationLookupSelection(BaseModel):
    items: list[ExperienceLocationLookupItem] = Field(default_factory=list)


class SkillInferenceSelection(BaseModel):
    languages: list[str] = Field(default_factory=list)
    computer: list[str] = Field(default_factory=list)


class SkillDeduplicationSelection(BaseModel):
    keep_indexes: list[int] = Field(default_factory=list)


class ObjectMatchSelection(BaseModel):
    match_index: int | None = None
