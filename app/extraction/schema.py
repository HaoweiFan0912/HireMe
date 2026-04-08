from pydantic import BaseModel


class Link(BaseModel):
    label: str  # Link label, such as LinkedIn, GitHub, or a personal website
    url: str  # Link URL


class Address(BaseModel):
    city: str  # City
    state_or_province: str  # State or province
    country: str  # Country
    postal_code: str  # Postal code
    phone: str  # Phone number for the location


class Basics(BaseModel):
    full_name: str  # Full name
    email: str  # Email address
    links: list[Link]  # List of links
    permanent_address: Address  # Permanent address
    current_address: Address  # Current address


class EducationEntry(BaseModel):
    institution: str  # School or institution name
    city: str  # City
    state_or_province: str  # State or province
    country: str  # Country
    start_date: str  # Start date
    end_date: str  # Actual or expected end date
    degree: str  # Degree name
    majors_or_programs: list[str]  # Major or program names
    courses: list[str]  # Courses
    gpa: str  # GPA
    honors: list[str]  # Honors


class ExperienceEntry(BaseModel):
    company: str  # Company name
    city: str  # City
    state_or_province: str  # State or province
    country: str  # Country
    job_title: str  # Job title
    start_date: str  # Start date
    end_date: str  # Actual or expected end date; use "Present" if current
    is_current: bool  # Whether this is the current role
    content: str  # What was completed in the experience
    method: str  # The method, tools, process, or technology used
    result: str  # The explicit outcome or impact


class Skills(BaseModel):
    languages: list[str]  # Languages
    computer: list[str]  # Technical or computer skills


class ActivityEntry(BaseModel):
    role: str  # Role
    organization: str  # Organization name
    start_date: str  # Start date
    end_date: str  # Actual or expected end date
    description: list[str]  # Activity description


class ResumeSchema(BaseModel):
    basics: Basics  # Basic information
    education: list[EducationEntry]  # Education history
    professional_experience: list[ExperienceEntry]  # Professional experience
    skills: Skills  # Skills
    activities: list[ActivityEntry]  # Activities
