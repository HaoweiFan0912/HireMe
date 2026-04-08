import os

from openai import OpenAI

from app.config.api_keys import openai_api


def resolve_api_key(api_key_override: str | None = None) -> str:
    if isinstance(api_key_override, str) and api_key_override.strip():
        return api_key_override.strip()
    return os.getenv("OPENAI_API_KEY") or openai_api


def create_client(api_key_override: str | None = None) -> OpenAI:
    api_key = resolve_api_key(api_key_override)
    if not api_key:
        raise ValueError("No OpenAI API key was found.")
    return OpenAI(api_key=api_key)
