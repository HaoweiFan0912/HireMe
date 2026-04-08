PDF_TEXT_PRIMARY_EXTRACTION_SKILL = (
    "Use the extracted PDF text as the primary source. "
    "PDF page images may also be provided for visually present details such as logos, layout labels, "
    "or text that the PDF text layer misses."
)

SCANNED_PDF_EXTRACTION_SKILL = (
    "This PDF appears to be image-based or scanned. "
    "Extract only text that is visibly present on the rendered PDF pages. "
    "Do not infer, summarize, normalize, or complete missing details."
)

IMAGE_TEXT_EXTRACTION_SKILL = (
    "Extract only text that is visually present in this image. "
    "Do not infer hidden or unclear content."
)

STRICT_EXTRACTION_SYSTEM_SKILL = (
    "You are a precision extraction engine. "
    "Extract resume information into the required structure. "
    "Strict rules: "
    "1. Copy only information that is explicitly present in the document. "
    "2. Every returned string and every list item must be copied verbatim from the document. "
    "3. Do not summarize, paraphrase, normalize, translate, reformat, or combine fragments. "
    "4. Do not infer missing facts. If a field is missing, return null for scalars and [] for lists. "
    "5. Preserve capitalization, punctuation, date format, abbreviations, and wording exactly. "
    "6. For booleans, return true or false only when the document explicitly supports it; otherwise return null. "
    "7. If a list item is not explicitly present, do not invent one. "
    "8. The output must contain only extracted facts from the document and match the schema."
)

STRICT_SCHEMA_EXTRACTION_SKILL = (
    "Extract the document into the schema. "
    "Leave missing fields empty rather than guessing. "
    "For addresses, only fill the exact subfields that appear. "
    "For education entries, also fill `country`, `state_or_province`, and `city` only when those "
    "location details are explicitly stated for that school or campus. "
    "For education entries, fill `courses` only when coursework, course titles, or class lists are explicitly shown for that school or program, "
    "and keep the original course wording exactly as shown, including course codes if present. "
    "For professional experience entries, also fill `country`, `state_or_province`, and `city` only when those "
    "location details are explicitly stated for that company, office, branch, campus, or site. "
    "For links, if the document provides a URL but no explicit label, infer the label from the URL domain. "
    "Examples: linkedin.com -> LinkedIn, github.com -> GitHub, personal domain -> Personal Website or the site name. "
    "For professional experience fields, enforce strict boundaries: "
    "`content` means only what the person completed or delivered in the role; "
    "`method` means only how the person did the work, including tools, technologies, algorithms, workflows, or approaches; "
    "`result` means only the explicit outcome, impact, or effect. "
    "If a statement does not clearly satisfy one category, do not place it there. "
    "If a category is not explicitly supported, leave it empty. "
    "For recommendation or reference letters, prefer complete original sentences over fragments. "
    "If the document clearly identifies the company through visible letterhead or logo and the text "
    "describes the role as being in 'our company', you may use that visible company name as explicit evidence. "
    "For `is_current`, use true only when the role is explicitly current "
    "or the end date explicitly says Present/current; use false only when the "
    "document explicitly indicates the role ended; otherwise use null."
)

EDUCATION_LOCATION_LOOKUP_SYSTEM_SKILL = (
    "You resolve school campus locations. "
    "Return only the requested structured fields."
)

ENTITY_FULL_NAME_LOOKUP_SYSTEM_SKILL = (
    "You resolve abbreviated institution and organization names into their full official names. "
    "Return only the requested structured fields."
)

ENTITY_FULL_NAME_LOOKUP_RULES = (
    "1. Use live web search to identify the full official or widely accepted formal name for each entity.\n"
    "2. Expand abbreviations, acronyms, short forms, and partial brand names into full names whenever you can do so confidently.\n"
    "3. Use document context such as degree, role, dates, location, campus, department, email domain, letterhead, and description to disambiguate.\n"
    "4. For schools, return the full institution name. If the document only mentions a college, school, or campus within a larger university, return the full institution name that best matches the context.\n"
    "5. For companies and organizations, return the full official or widely recognized formal name. Expand abbreviations like `AWS` to `Amazon Web Services`. Do not add a legal suffix unless it is part of the standard public full name or needed for disambiguation.\n"
    "6. If the original name already appears to be the correct full name, return that full name unchanged.\n"
    "7. If you cannot determine the full name confidently, return null for that entry."
)

EDUCATION_LOCATION_LOOKUP_RULES = (
    "1. Use live web search to identify the school's location.\n"
    "2. If the document explicitly indicates a campus, college, or branch, resolve that campus.\n"
    "3. If the campus is not explicitly given, use the institution's primary or main campus.\n"
    "4. Always return `campus_name` when you can identify the campus you used. If campus is unspecified, "
    "return the main campus name.\n"
    "5. Return only `city`, `state_or_province`, `country`, and `campus_name`.\n"
    "6. Use full state or province names, not abbreviations.\n"
    "7. If you cannot determine the school confidently, leave all fields null for that entry."
)

EXPERIENCE_LOCATION_LOOKUP_SYSTEM_SKILL = (
    "You resolve work-experience office locations. "
    "Return only the requested structured fields."
)

OBJECT_MATCH_SYSTEM_SKILL = (
    "You compare extracted resume objects and decide whether the incoming entry is the same "
    "real-world object as one of the provided candidates. "
    "Return only the requested structured output."
)

OBJECT_MATCH_BASE_RULES = (
    "1. Compare the incoming entry against the numbered candidate entries.\n"
    "2. Return `match_index` with exactly one candidate index only when you are confident the incoming entry refers to the same real-world object.\n"
    "3. Return `null` when none of the candidates is clearly the same object or when the evidence is ambiguous.\n"
    "4. Treat differences in wording, abbreviation, capitalization, campus suffixes, location formatting, and date precision as non-blocking when the underlying object is clearly the same.\n"
    "5. Treat clearly different schools, employers, organizations, roles, programs, or time windows as different objects.\n"
    "6. Use only the provided candidate entries and incoming entry. Do not invent missing facts.\n"
    "7. Prefer precision over recall. If you are unsure, return `null`."
)

EDUCATION_OBJECT_MATCH_RULES = (
    "Education entries can match even when one source is a transcript and the other is a resume.\n"
    "Use institution name, degree, majors or programs, dates, GPA, honors, course overlap, and location clues together.\n"
    "If one entry is clearly a shorter or more detailed version of the same school record, match it.\n"
    "If the institution is different, do not match.\n"
    "If the institution is the same but the degree, program, or time window clearly indicates a separate education stint, do not match."
)

EXPERIENCE_OBJECT_MATCH_RULES = (
    "Professional experience entries can match even when one source is a resume bullet set and the other is a recommendation letter or transcript-like summary.\n"
    "Use company name, job title, dates, location, and work content together.\n"
    "If the role, employer, and approximate time window point to the same job or internship, match it.\n"
    "If the employer or role is clearly different, do not match.\n"
    "If the employer is the same but the dates or responsibilities clearly indicate a different role, do not match."
)

ACTIVITY_OBJECT_MATCH_RULES = (
    "Activity entries can match even when one source is shorter or uses slightly different organization wording.\n"
    "Use organization name, role, dates, and description together.\n"
    "If they clearly refer to the same organization involvement, match them.\n"
    "If the organization, role, or time window clearly points to a different activity, do not match."
)

EXPERIENCE_LOCATION_LOOKUP_RULES = (
    "1. Use live web search to identify the company's or organization's work location.\n"
    "2. If the document explicitly indicates an office, branch, campus, lab, or site, resolve that location.\n"
    "3. If the specific office or site is not explicitly given, use the company's primary office or headquarters.\n"
    "4. Always return `location_name` when you can identify the office, branch, site, campus, or headquarters used.\n"
    "5. Return only `city`, `state_or_province`, `country`, and `location_name`.\n"
    "6. Use full state or province names, not abbreviations.\n"
    "7. If you cannot determine the location confidently, leave all fields null for that entry."
)

EDUCATION_HONORS_SYSTEM_SKILL = (
    "You normalize education honors. "
    "Return only the requested structured output."
)

EDUCATION_HONORS_RULES = (
    "1. Work entry by entry.\n"
    "2. Keep only honors that are already in `current_honors` or directly supported by the provided honor lines.\n"
    "3. Remove duplicates when the honor text and time are the same.\n"
    "4. If the same honor appears with different explicit times, keep separate items.\n"
    "5. If an honor has an explicit date, term, or semester, format it as `Honor (Time)`.\n"
    "6. Use the exact honor wording and the exact time wording from the source lines; only rearrange into the `Honor (Time)` format.\n"
    "7. If an honor has no explicit time, keep it as plain honor text.\n"
    "8. Preserve order of first appearance.\n"
    "9. Do not invent honors or times."
)

EDUCATION_COURSES_SYSTEM_SKILL = (
    "You identify and normalize education course names. "
    "Return only the requested structured output."
)

EDUCATION_COURSES_RULES = (
    "1. Work entry by entry.\n"
    "2. Include only courses that are explicitly listed in the document and can be attributed to that education entry.\n"
    "3. Copy the original course wording exactly as shown in the document.\n"
    "4. Keep course codes when they are present. Do not strip codes such as `MAT223H1`.\n"
    "5. Do not expand abbreviations, rewrite titles, normalize capitalization, or convert short forms into full names.\n"
    "6. Remove only exact duplicates for the same entry.\n"
    "7. Do not treat majors, minors, degrees, departments, honors, or general skills as courses unless the document presents them as course titles.\n"
    "8. Preserve order of first appearance as much as possible."
)

EXPERIENCE_EVIDENCE_SELECTION_SYSTEM_SKILL = (
    "You are an evidence selector. "
    "Use only the provided numbered source segments. "
    "Do not rewrite, summarize, paraphrase, or invent."
)

EXPERIENCE_EVIDENCE_SELECTION_RULES = (
    "1. `content_segment_ids`: choose only segments that explicitly state what the person completed, built, "
    "implemented, developed, analyzed, wrote, designed, delivered, or otherwise finished in the role. "
    "Do not choose segments that are only about tools, processes, praise, or outcomes.\n"
    "2. `method_segment_ids`: choose only segments that explicitly state how the work was done, including "
    "tools, technologies, algorithms, frameworks, workflows, approaches, or procedures used. "
    "Do not choose segments that only say what was completed or what result happened.\n"
    "3. `result_segment_ids`: choose only segments that explicitly state a result, impact, metric, efficiency gain, "
    "business effect, team benefit, or other outcome caused by the work. "
    "Do not choose personality praise or vague positive comments without an explicit outcome.\n"
    "4. If a segment does not clearly satisfy a category boundary, do not include it in that category.\n"
    "5. Ignore greetings, recommendation intent, closing lines, and contact details unless they explicitly "
    "describe work content.\n"
    "6. Use ids only from the provided segment list.\n"
    "7. A segment may appear in multiple categories only if it explicitly contains each category's evidence.\n"
    "8. Prefer strict category boundaries over broad coverage. If unsure, leave it out."
)

EXPERIENCE_REWRITE_SYSTEM_SKILL = (
    "You rewrite work experience content into polished resume language. "
    "Preserve every factual detail from the source segments. "
    "Do not invent new facts. "
    "Write in the same language as the source material."
)

EXPERIENCE_REWRITE_RULES = (
    "1. Each field must be a single string, not a list.\n"
    "2. Keep strict category boundaries. Do not move method details into `content`, and do not move outcomes into `content` or `method`.\n"
    "3. If multiple source segments exist, merge them into one coherent text and separate covered ideas with periods.\n"
    "4. Cover all factual content from the source segments for that category only.\n"
    "5. You may rewrite for clarity and fluency, but you must not add new facts.\n"
    "6. If a field has no source segments, return an empty string."
)

SKILL_INFERENCE_SYSTEM_SKILL = (
    "You infer resume skills from evidence. "
    "Return only the requested structured output."
)

SKILL_DEDUPLICATION_SYSTEM_SKILL = (
    "You compare skill items and remove duplicates or near-duplicates. "
    "Return only the requested structured output."
)

SKILL_DEDUPLICATION_RULES = (
    "1. Compare only the provided skill items. Do not invent any new skill labels.\n"
    "2. Treat acronym/full-name pairs, singular/plural variants, punctuation variants, case variants, and minor wording variants as duplicates when they clearly refer to the same skill.\n"
    "3. Keep exactly one representative item for each distinct skill.\n"
    "4. Prefer the clearest and most standard English label that already appears in the input list.\n"
    "5. When one item is a longer descriptive phrase and another item is the standard base skill name, keep the standard base skill name. Example: keep `linear regression` instead of `linear regression modeling`.\n"
    "6. Do not merge different skills just because they are related or belong to the same topic area.\n"
    "7. Prefer precision over recall. If two items might be different skills, keep both.\n"
    "8. Return the indexes of the items to keep."
)

SKILL_INFERENCE_RULES = (
    "1. Include only skills that are directly supported by the document text or extracted experience, education, activities, or existing skills.\n"
    "2. Infer skills the person used or clearly demonstrates, even if they were not listed in a dedicated skills section.\n"
    "3. Use full names instead of acronyms whenever possible. Examples: `large language model` instead of `LLM`, "
    "`natural language processing` instead of `NLP`, `reinforcement learning` instead of `RL`.\n"
    "4. Put spoken or human languages in `languages`.\n"
    "5. Put programming languages, software tools, cloud platforms, frameworks, libraries, algorithms, research areas, "
    "and technical methods in `computer`.\n"
    "6. Do not include soft skills, personality traits, or vague qualities.\n"
    "7. Do not invent unsupported skills. If the evidence is weak or indirect, leave the skill out.\n"
    "8. Do not repeat skills that already exist, including acronym/full-name duplicates.\n"
    "9. Prefer concise canonical skill names, one skill per item."
)
