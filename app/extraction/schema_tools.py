from typing import Any, get_args, get_origin

from pydantic import BaseModel

from app.extraction.schema import ResumeSchema


def unwrap_optional(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is None:
        return annotation
    if origin in (list, dict):
        return annotation
    args = [arg for arg in get_args(annotation) if arg is not type(None)]
    if len(args) == 1:
        return args[0]
    return annotation


def is_model(annotation: Any) -> bool:
    return isinstance(annotation, type) and issubclass(annotation, BaseModel)


def build_blank_from_annotation(annotation: Any) -> Any:
    annotation = unwrap_optional(annotation)
    origin = get_origin(annotation)

    if is_model(annotation):
        return {
            field_name: build_blank_from_annotation(field_info.annotation)
            for field_name, field_info in annotation.model_fields.items()
        }
    if origin is list:
        return []
    if annotation is bool:
        return None
    return ""


def build_blueprint_from_annotation(annotation: Any, *, title: str | None = None) -> dict[str, Any]:
    annotation = unwrap_optional(annotation)
    origin = get_origin(annotation)

    if is_model(annotation):
        return {
            "kind": "object",
            "title": title or annotation.__name__,
            "fields": [
                {
                    "name": field_name,
                    "blueprint": build_blueprint_from_annotation(
                        field_info.annotation,
                        title=field_name,
                    ),
                }
                for field_name, field_info in annotation.model_fields.items()
            ],
        }

    if origin is list:
        item_annotation = get_args(annotation)[0]
        return {
            "kind": "list",
            "title": title,
            "item_blueprint": build_blueprint_from_annotation(item_annotation, title=title),
            "item_template": build_blank_from_annotation(item_annotation),
        }

    if annotation is bool:
        return {
            "kind": "boolean",
            "title": title,
        }

    return {
        "kind": "string",
        "title": title,
    }


def build_resume_template() -> dict[str, Any]:
    return build_blank_from_annotation(ResumeSchema)


def build_resume_blueprint() -> dict[str, Any]:
    return build_blueprint_from_annotation(ResumeSchema, title="ResumeSchema")


def is_blank_normalized_value(value: Any) -> bool:
    if isinstance(value, dict):
        return all(is_blank_normalized_value(item) for item in value.values())
    if isinstance(value, list):
        return len(value) == 0
    return value in ("", None)


def normalize_data_to_blueprint(data: Any, blueprint: dict[str, Any]) -> Any:
    kind = blueprint["kind"]

    if kind == "object":
        source = data if isinstance(data, dict) else {}
        return {
            field["name"]: normalize_data_to_blueprint(source.get(field["name"]), field["blueprint"])
            for field in blueprint["fields"]
        }

    if kind == "list":
        if not isinstance(data, list):
            return []
        item_blueprint = blueprint["item_blueprint"]
        normalized_items = [
            normalize_data_to_blueprint(item, item_blueprint)
            for item in data
        ]
        return [item for item in normalized_items if not is_blank_normalized_value(item)]

    if kind == "boolean":
        return data if isinstance(data, bool) else None

    if data is None:
        return ""
    return data if isinstance(data, str) else str(data)


def seed_data_from_blueprint(blueprint: dict[str, Any]) -> Any:
    kind = blueprint["kind"]

    if kind == "object":
        return {
            field["name"]: seed_data_from_blueprint(field["blueprint"])
            for field in blueprint["fields"]
        }
    if kind == "list":
        return []
    if kind == "boolean":
        return None
    return ""


def is_blank_object(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return all(
        (
            not item
            if isinstance(item, list)
            else item in ("", None)
            if not isinstance(item, dict)
            else is_blank_object(item)
        )
        for item in value.values()
    )


def identity_fields_for_path(path: tuple[str, ...]) -> tuple[str, ...]:
    identity_map = {
        ("basics", "links"): ("url", "label"),
        ("education",): ("institution", "degree", "start_date", "end_date"),
        ("activities",): ("organization", "role", "start_date", "end_date"),
    }
    return identity_map.get(path, ())
