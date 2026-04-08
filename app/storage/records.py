import json

from app.core.paths import DATA_DIR
from app.extraction.extractor import (
    build_resume_blueprint,
    build_resume_template,
    normalize_data_to_blueprint,
)


RECORD_FILE = DATA_DIR / "current_record.json"
RECORD_META_FILE = DATA_DIR / "current_record_meta.json"


def _load_record_meta() -> dict:
    if not RECORD_META_FILE.exists():
        return {}

    try:
        payload = json.loads(RECORD_META_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def load_saved_record() -> tuple[dict, bool]:
    blueprint = build_resume_blueprint()
    blank = build_resume_template()
    meta = _load_record_meta()

    if meta.get("saved_by") != "manual":
        return blank, False
    if not RECORD_FILE.exists():
        return blank, False

    try:
        payload = json.loads(RECORD_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return blank, False

    return normalize_data_to_blueprint(payload, blueprint), True


def save_record(record: dict) -> dict:
    blueprint = build_resume_blueprint()
    normalized = normalize_data_to_blueprint(record, blueprint)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RECORD_FILE.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    RECORD_META_FILE.write_text(
        json.dumps({"saved_by": "manual"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return normalized
