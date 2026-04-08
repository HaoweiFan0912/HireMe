import os
import re
from typing import Any


MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1")
MERGE_MATCH_MODEL_NAME = os.getenv("OPENAI_MERGE_MODEL", "gpt-4.1-mini")

KNOWN_LINK_LABELS = {
    "linkedin.com": "LinkedIn",
    "github.com": "GitHub",
    "gitlab.com": "GitLab",
    "bitbucket.org": "Bitbucket",
    "x.com": "X",
    "twitter.com": "Twitter",
    "facebook.com": "Facebook",
    "instagram.com": "Instagram",
    "medium.com": "Medium",
    "substack.com": "Substack",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "scholar.google.com": "Google Scholar",
    "orcid.org": "ORCID",
    "researchgate.net": "ResearchGate",
    "huggingface.co": "Hugging Face",
    "kaggle.com": "Kaggle",
    "leetcode.com": "LeetCode",
    "codeforces.com": "Codeforces",
    "personal": "Personal Website",
}

SKILL_ALIASES = {
    "llm": "large language model",
    "llms": "large language model",
    "nlp": "natural language processing",
    "ml": "machine learning",
    "dl": "deep learning",
    "rl": "reinforcement learning",
    "dqn": "deep q-network",
    "ddqn": "double deep q-network",
    "ppo": "proximal policy optimization",
    "rag": "retrieval-augmented generation",
    "cnn": "convolutional neural network",
    "rnn": "recurrent neural network",
    "lstm": "long short-term memory",
    "sql": "structured query language",
    "nosql": "non-relational database",
    "api": "application programming interface",
    "apis": "application programming interface",
    "aws": "Amazon Web Services",
    "gcp": "Google Cloud Platform",
}

ENTITY_NAME_CONNECTORS = {"of", "the", "and", "for", "at", "in", "on", "to", "a", "an"}


def normalize_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""

    normalized = value.lower()
    replacements = {
        "jan": "january",
        "feb": "february",
        "mar": "march",
        "apr": "april",
        "jun": "june",
        "jul": "july",
        "aug": "august",
        "sep": "september",
        "sept": "september",
        "oct": "october",
        "nov": "november",
        "dec": "december",
    }
    for short, full in replacements.items():
        normalized = re.sub(rf"\b{short}\b", full, normalized)

    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return " ".join(normalized.split())


def normalize_lookup_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def clean_entity_name(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip(" ,;:|")


def compact_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def entity_name_variants(value: Any) -> set[str]:
    normalized = normalize_text(value)
    tokens = normalized.split()
    if not tokens:
        return set()

    variants = {
        "".join(tokens),
        "".join(token[0] for token in tokens if token),
    }
    non_connector_tokens = [token for token in tokens if token not in ENTITY_NAME_CONNECTORS]
    if non_connector_tokens:
        variants.add("".join(token[0] for token in non_connector_tokens if token))

    mixed_parts: list[str] = []
    for token in tokens:
        if token in {"of", "and", "for", "the"}:
            mixed_parts.append(token)
        else:
            mixed_parts.append(token[0])
    variants.add("".join(mixed_parts))
    return {variant for variant in variants if variant}


def entity_name_acronym_matches(left: Any, right: Any) -> bool:
    left_compact = compact_text(clean_entity_name(left))
    right_compact = compact_text(clean_entity_name(right))
    if not left_compact or not right_compact:
        return False
    return left_compact in entity_name_variants(right) or right_compact in entity_name_variants(left)


def title_case_domain_label(domain: str) -> str:
    value = re.sub(r"[-_]+", " ", domain).strip()
    return " ".join(part.capitalize() for part in value.split())


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def split_rewritten_text(value: Any) -> list[str]:
    if not isinstance(value, str):
        return []
    parts = re.split(r"(?<=[.!?。！？；;])\s+", value.strip())
    return [part.strip() for part in parts if part.strip()]


def token_set(value: Any) -> set[str]:
    text = normalize_text(value)
    return {token for token in text.split() if len(token) > 1}


def text_similarity(left: Any, right: Any) -> float:
    left_text = normalize_text(left)
    right_text = normalize_text(right)
    if not left_text or not right_text:
        return 0.0
    if left_text == right_text:
        return 1.0
    if entity_name_acronym_matches(left, right):
        return 0.9
    if left_text in right_text or right_text in left_text:
        return 0.92

    left_tokens = token_set(left_text)
    right_tokens = token_set(right_text)
    if not left_tokens or not right_tokens:
        return 0.0

    smaller_tokens, larger_tokens = (
        (left_tokens, right_tokens)
        if len(left_tokens) <= len(right_tokens)
        else (right_tokens, left_tokens)
    )
    if smaller_tokens and smaller_tokens.issubset(larger_tokens):
        return 0.9

    intersection = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    if union == 0:
        return 0.0
    return intersection / union


def join_rewritten_sentences(sentences: list[str]) -> str:
    cleaned_parts: list[str] = []
    seen_norms: list[str] = []

    for sentence in sentences:
        if not isinstance(sentence, str):
            continue

        cleaned = " ".join(sentence.split()).strip()
        if not cleaned:
            continue

        normalized = normalize_text(cleaned)
        if any(text_similarity(normalized, seen) >= 0.92 for seen in seen_norms):
            continue

        if cleaned[-1] not in ".!?。！？；;":
            cleaned = f"{cleaned}."
        cleaned_parts.append(cleaned)
        seen_norms.append(normalized)

    return " ".join(cleaned_parts)


def coerce_text_segments(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, str):
        return [value]
    return []


def is_non_empty_scalar(value: Any) -> bool:
    return value not in ("", None, [])


def field_relation(left: Any, right: Any, *, similarity_threshold: float = 0.78) -> tuple[int, float]:
    if not is_non_empty_scalar(left) and not is_non_empty_scalar(right):
        return 0, 0.0
    if not is_non_empty_scalar(left) or not is_non_empty_scalar(right):
        return 0, 0.0

    similarity = text_similarity(left, right)
    if similarity >= similarity_threshold:
        return 1, similarity
    return -1, similarity


def list_overlap_score(left_items: list[Any], right_items: list[Any]) -> float:
    left_values = [item for item in left_items if isinstance(item, str) and item.strip()]
    right_values = [item for item in right_items if isinstance(item, str) and item.strip()]
    if not left_values or not right_values:
        return 0.0

    best = 0.0
    for left in left_values:
        for right in right_values:
            best = max(best, text_similarity(left, right))
    return best


def preview_match_text(value: Any, *, limit: int = 220) -> str:
    if not isinstance(value, str):
        return ""
    cleaned = " ".join(value.split()).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def preview_match_list(value: Any, *, limit: int = 6, item_limit: int = 160) -> list[str]:
    if not isinstance(value, list):
        return []

    preview: list[str] = []
    for item in value:
        cleaned = preview_match_text(item, limit=item_limit)
        if not cleaned:
            continue
        preview.append(cleaned)
        if len(preview) >= limit:
            break
    return preview


def prune_match_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if value not in ("", None, [], {})
    }
