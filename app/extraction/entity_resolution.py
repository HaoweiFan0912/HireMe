from typing import Any
from urllib.parse import urlparse

from openai import OpenAI

from app.extraction.common import (
    KNOWN_LINK_LABELS,
    MODEL_NAME,
    clean_entity_name,
    entity_name_acronym_matches,
    normalize_lookup_key,
    normalize_text,
    title_case_domain_label,
)
from app.extraction.models import (
    EducationLocationLookupSelection,
    EntityFullNameLookupSelection,
    ExperienceLocationLookupSelection,
)
from app.extraction.prompt_collection import (
    build_education_location_lookup_fallback_messages,
    build_education_location_lookup_prompt,
    build_entity_full_name_lookup_fallback_messages,
    build_entity_full_name_lookup_prompt,
    build_experience_location_lookup_fallback_messages,
    build_experience_location_lookup_prompt,
)


def prefer_full_entity_name(current: Any, incoming: Any) -> str:
    current_clean = clean_entity_name(current)
    incoming_clean = clean_entity_name(incoming)
    if not current_clean:
        return incoming_clean
    if not incoming_clean:
        return current_clean
    if current_clean == incoming_clean:
        return current_clean

    if entity_name_acronym_matches(current_clean, incoming_clean):
        return incoming_clean if len(incoming_clean) >= len(current_clean) else current_clean

    current_normalized = normalize_text(current_clean)
    incoming_normalized = normalize_text(incoming_clean)
    if current_normalized == incoming_normalized:
        return incoming_clean if len(incoming_clean) >= len(current_clean) else current_clean

    if current_normalized and current_normalized in incoming_normalized and len(incoming_clean) > len(current_clean):
        return incoming_clean
    if incoming_normalized and incoming_normalized in current_normalized and len(current_clean) >= len(incoming_clean):
        return current_clean

    return incoming_clean


def infer_link_label_from_url(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        return ""

    candidate = url.strip()
    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    host = (parsed.netloc or parsed.path).lower().strip()
    host = host.split("@")[-1].split(":")[0]
    if not host:
        return ""

    if host.startswith("www."):
        host = host[4:]

    for known_host, label in KNOWN_LINK_LABELS.items():
        if host == known_host or host.endswith(f".{known_host}"):
            return label

    parts = [part for part in host.split(".") if part]
    if not parts:
        return ""

    if len(parts) >= 3 and len(parts[-1]) == 2 and len(parts[-2]) <= 3:
        root = parts[-3]
    elif len(parts) >= 2:
        root = parts[-2]
    else:
        root = parts[0]

    if root in {"me", "site", "web", "home"}:
        return KNOWN_LINK_LABELS["personal"]
    return title_case_domain_label(root)


def normalize_links(extracted: dict[str, Any]) -> dict[str, Any]:
    basics = extracted.get("basics")
    if not isinstance(basics, dict):
        return extracted

    links = basics.get("links")
    if not isinstance(links, list):
        return extracted

    normalized_links: list[dict[str, Any]] = []
    for item in links:
        if not isinstance(item, dict):
            continue

        url = item.get("url")
        label = item.get("label")
        if (not isinstance(label, str) or not label.strip()) and isinstance(url, str) and url.strip():
            item["label"] = infer_link_label_from_url(url)
        normalized_links.append(item)

    basics["links"] = normalized_links
    extracted["basics"] = basics
    return extracted


def format_city_with_location(city: str, location_name: Any) -> str:
    cleaned_city = " ".join(city.split()).strip()
    if not cleaned_city:
        return ""

    if not isinstance(location_name, str) or not location_name.strip():
        return cleaned_city

    cleaned_location = " ".join(location_name.split()).strip().strip("()")
    if not cleaned_location:
        return cleaned_city

    if normalize_lookup_key(cleaned_location) in normalize_lookup_key(cleaned_city):
        return cleaned_city

    return f"{cleaned_city} ({cleaned_location})"


def lookup_entity_full_names_with_gpt(
    client: OpenAI,
    document_text: str | None,
    extracted: dict[str, Any],
) -> dict[str, Any]:
    lookup_payload: list[dict[str, Any]] = []

    education = extracted.get("education")
    if isinstance(education, list):
        for index, item in enumerate(education):
            if not isinstance(item, dict):
                continue
            institution = item.get("institution")
            if isinstance(institution, str) and institution.strip():
                lookup_payload.append(
                    {
                        "entry_type": "education",
                        "entry_index": index,
                        "current_name": institution,
                        "degree": item.get("degree"),
                        "start_date": item.get("start_date"),
                        "end_date": item.get("end_date"),
                        "city": item.get("city"),
                        "state_or_province": item.get("state_or_province"),
                        "country": item.get("country"),
                        "majors_or_programs": item.get("majors_or_programs") or [],
                    }
                )

    experiences = extracted.get("professional_experience")
    if isinstance(experiences, list):
        for index, item in enumerate(experiences):
            if not isinstance(item, dict):
                continue
            company = item.get("company")
            if isinstance(company, str) and company.strip():
                lookup_payload.append(
                    {
                        "entry_type": "professional_experience",
                        "entry_index": index,
                        "current_name": company,
                        "job_title": item.get("job_title"),
                        "start_date": item.get("start_date"),
                        "end_date": item.get("end_date"),
                        "city": item.get("city"),
                        "state_or_province": item.get("state_or_province"),
                        "country": item.get("country"),
                    }
                )

    activities = extracted.get("activities")
    if isinstance(activities, list):
        for index, item in enumerate(activities):
            if not isinstance(item, dict):
                continue
            organization = item.get("organization")
            if isinstance(organization, str) and organization.strip():
                lookup_payload.append(
                    {
                        "entry_type": "activities",
                        "entry_index": index,
                        "current_name": organization,
                        "role": item.get("role"),
                        "start_date": item.get("start_date"),
                        "end_date": item.get("end_date"),
                        "description": item.get("description") or [],
                    }
                )

    if not lookup_payload:
        return extracted

    prompt = build_entity_full_name_lookup_prompt(lookup_payload, document_text)

    parsed_lookup: EntityFullNameLookupSelection | None = None
    try:
        lookup_response = client.responses.parse(
            model=MODEL_NAME,
            temperature=0,
            tools=[
                {
                    "type": "web_search_preview",
                    "search_context_size": "medium",
                    "user_location": {
                        "type": "approximate",
                        "country": "US",
                        "region": "New York",
                        "timezone": "America/New_York",
                    },
                }
            ],
            input=prompt,
            text_format=EntityFullNameLookupSelection,
        )
        parsed_lookup = lookup_response.output_parsed
    except Exception:
        parsed_lookup = None

    if parsed_lookup is None:
        try:
            fallback_completion = client.chat.completions.parse(
                model=MODEL_NAME,
                temperature=0,
                messages=build_entity_full_name_lookup_fallback_messages(prompt),
                response_format=EntityFullNameLookupSelection,
            )
            fallback_message = fallback_completion.choices[0].message
            if getattr(fallback_message, "refusal", None) is None:
                parsed_lookup = fallback_message.parsed
        except Exception:
            parsed_lookup = None

    if parsed_lookup is None:
        return extracted

    lookup_by_key = {(item.entry_type, item.entry_index): item for item in parsed_lookup.items}
    field_map = {
        "education": ("education", "institution"),
        "professional_experience": ("professional_experience", "company"),
        "activities": ("activities", "organization"),
    }

    for entry_type, (section_name, field_name) in field_map.items():
        section = extracted.get(section_name)
        if not isinstance(section, list):
            continue

        for index, item in enumerate(section):
            if not isinstance(item, dict):
                continue

            lookup_item = lookup_by_key.get((entry_type, index))
            if lookup_item is None:
                continue

            full_name = clean_entity_name(lookup_item.full_name)
            if not full_name:
                continue

            item[field_name] = prefer_full_entity_name(item.get(field_name), full_name)

    return extracted


def lookup_education_locations_with_gpt(
    client: OpenAI,
    document_text: str | None,
    extracted: dict[str, Any],
) -> dict[str, Any]:
    education = extracted.get("education")
    if not isinstance(education, list):
        return extracted

    lookup_payload: list[dict[str, Any]] = []
    normalized_entries: list[dict[str, Any]] = []
    for index, item in enumerate(education):
        if not isinstance(item, dict):
            continue

        institution = item.get("institution")
        if isinstance(institution, str) and institution.strip():
            has_missing_location = any(
                not isinstance(item.get(field_name), str) or not item.get(field_name).strip()
                for field_name in ("city", "state_or_province", "country")
            )
            if has_missing_location:
                lookup_payload.append(
                    {
                        "entry_index": index,
                        "institution": institution,
                        "city": item.get("city"),
                        "state_or_province": item.get("state_or_province"),
                        "country": item.get("country"),
                        "degree": item.get("degree"),
                        "start_date": item.get("start_date"),
                        "end_date": item.get("end_date"),
                        "majors_or_programs": item.get("majors_or_programs") or [],
                    }
                )

        normalized_entries.append(item)

    if not lookup_payload:
        extracted["education"] = normalized_entries
        return extracted

    prompt = build_education_location_lookup_prompt(lookup_payload, document_text)

    parsed_lookup: EducationLocationLookupSelection | None = None
    try:
        lookup_response = client.responses.parse(
            model=MODEL_NAME,
            temperature=0,
            tools=[
                {
                    "type": "web_search_preview",
                    "search_context_size": "medium",
                    "user_location": {
                        "type": "approximate",
                        "country": "US",
                        "region": "New York",
                        "timezone": "America/New_York",
                    },
                }
            ],
            input=prompt,
            text_format=EducationLocationLookupSelection,
        )
        parsed_lookup = lookup_response.output_parsed
    except Exception:
        parsed_lookup = None

    if parsed_lookup is None:
        try:
            fallback_completion = client.chat.completions.parse(
                model=MODEL_NAME,
                temperature=0,
                messages=build_education_location_lookup_fallback_messages(prompt),
                response_format=EducationLocationLookupSelection,
            )
            fallback_message = fallback_completion.choices[0].message
            if getattr(fallback_message, "refusal", None) is None:
                parsed_lookup = fallback_message.parsed
        except Exception:
            parsed_lookup = None

    if parsed_lookup is None:
        extracted["education"] = normalized_entries
        return extracted

    lookup_by_index = {item.entry_index: item for item in parsed_lookup.items}
    for index, item in enumerate(normalized_entries):
        lookup_item = lookup_by_index.get(index)
        if lookup_item is None:
            continue

        current_city = item.get("city")
        resolved_city = None
        if isinstance(current_city, str) and current_city.strip():
            resolved_city = current_city.strip()
        elif isinstance(lookup_item.city, str) and lookup_item.city.strip():
            resolved_city = lookup_item.city.strip()

        if resolved_city:
            item["city"] = format_city_with_location(resolved_city, lookup_item.campus_name)

        for field_name in ("state_or_province", "country"):
            current_value = item.get(field_name)
            looked_up_value = getattr(lookup_item, field_name)
            if (
                (not isinstance(current_value, str) or not current_value.strip())
                and isinstance(looked_up_value, str)
                and looked_up_value.strip()
            ):
                item[field_name] = looked_up_value.strip()

    extracted["education"] = normalized_entries
    return extracted


def lookup_experience_locations_with_gpt(
    client: OpenAI,
    document_text: str | None,
    extracted: dict[str, Any],
) -> dict[str, Any]:
    experiences = extracted.get("professional_experience")
    if not isinstance(experiences, list):
        return extracted

    lookup_payload: list[dict[str, Any]] = []
    normalized_entries: list[dict[str, Any]] = []
    for index, item in enumerate(experiences):
        if not isinstance(item, dict):
            continue

        company = item.get("company")
        if isinstance(company, str) and company.strip():
            has_missing_location = any(
                not isinstance(item.get(field_name), str) or not item.get(field_name).strip()
                for field_name in ("city", "state_or_province", "country")
            )
            if has_missing_location:
                lookup_payload.append(
                    {
                        "entry_index": index,
                        "company": company,
                        "job_title": item.get("job_title"),
                        "city": item.get("city"),
                        "state_or_province": item.get("state_or_province"),
                        "country": item.get("country"),
                        "start_date": item.get("start_date"),
                        "end_date": item.get("end_date"),
                        "is_current": item.get("is_current"),
                    }
                )

        normalized_entries.append(item)

    if not lookup_payload:
        extracted["professional_experience"] = normalized_entries
        return extracted

    prompt = build_experience_location_lookup_prompt(lookup_payload, document_text)

    parsed_lookup: ExperienceLocationLookupSelection | None = None
    try:
        lookup_response = client.responses.parse(
            model=MODEL_NAME,
            temperature=0,
            tools=[
                {
                    "type": "web_search_preview",
                    "search_context_size": "medium",
                    "user_location": {
                        "type": "approximate",
                        "country": "US",
                        "region": "New York",
                        "timezone": "America/New_York",
                    },
                }
            ],
            input=prompt,
            text_format=ExperienceLocationLookupSelection,
        )
        parsed_lookup = lookup_response.output_parsed
    except Exception:
        parsed_lookup = None

    if parsed_lookup is None:
        try:
            fallback_completion = client.chat.completions.parse(
                model=MODEL_NAME,
                temperature=0,
                messages=build_experience_location_lookup_fallback_messages(prompt),
                response_format=ExperienceLocationLookupSelection,
            )
            fallback_message = fallback_completion.choices[0].message
            if getattr(fallback_message, "refusal", None) is None:
                parsed_lookup = fallback_message.parsed
        except Exception:
            parsed_lookup = None

    if parsed_lookup is None:
        extracted["professional_experience"] = normalized_entries
        return extracted

    lookup_by_index = {item.entry_index: item for item in parsed_lookup.items}
    for index, item in enumerate(normalized_entries):
        lookup_item = lookup_by_index.get(index)
        if lookup_item is None:
            continue

        current_city = item.get("city")
        resolved_city = None
        if isinstance(current_city, str) and current_city.strip():
            resolved_city = current_city.strip()
        elif isinstance(lookup_item.city, str) and lookup_item.city.strip():
            resolved_city = lookup_item.city.strip()

        if resolved_city:
            item["city"] = format_city_with_location(resolved_city, lookup_item.location_name)

        for field_name in ("state_or_province", "country"):
            current_value = item.get(field_name)
            looked_up_value = getattr(lookup_item, field_name)
            if (
                (not isinstance(current_value, str) or not current_value.strip())
                and isinstance(looked_up_value, str)
                and looked_up_value.strip()
            ):
                item[field_name] = looked_up_value.strip()

    extracted["professional_experience"] = normalized_entries
    return extracted
