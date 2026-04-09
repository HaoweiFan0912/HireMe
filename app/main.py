import json

from fastapi import Body, FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.paths import STATIC_DIR
from app.extraction.extractor import (
    build_resume_blueprint,
    build_resume_template,
    extract_resume_from_bytes,
    merge_resume_data,
    normalize_data_to_blueprint,
)
from app.generation.service import (
    generate_general_resume_from_record,
    render_resume_document,
    tailor_resume_to_job_description,
)
from app.storage.records import load_saved_record, save_record


def create_app() -> FastAPI:
    application = FastAPI(title="Resume Schema Extractor")
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return application


app = create_app()


def _resolve_generation_record(record: dict | None) -> dict:
    if isinstance(record, dict) and record:
        return record
    return load_saved_record()[0]


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)


@app.get("/api/schema")
async def get_schema() -> dict:
    data, has_saved_record = load_saved_record()
    return {
        "blueprint": build_resume_blueprint(),
        "blank_data": build_resume_template(),
        "data": data,
        "has_saved_record": has_saved_record,
    }


@app.put("/api/record")
async def update_record(record: dict = Body(...)) -> dict:
    return {
        "data": save_record(record),
    }


@app.post("/api/extract")
async def extract_resume(
    file: UploadFile = File(...),
    current_data: str | None = Form(default=None),
    openai_api_key: str | None = Form(default=None),
) -> dict:
    try:
        existing_data = json.loads(current_data) if current_data else load_saved_record()[0]
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="`current_data` is not valid JSON.") from exc

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    try:
        extracted = extract_resume_from_bytes(
            filename=file.filename or "uploaded-file",
            content_type=file.content_type,
            file_bytes=file_bytes,
            api_key_override=openai_api_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - network/runtime failure
        raise HTTPException(status_code=500, detail=f"Extraction failed: {exc}") from exc

    blueprint = build_resume_blueprint()
    merged = merge_resume_data(existing_data, extracted, blueprint, api_key_override=openai_api_key)
    normalized = normalize_data_to_blueprint(merged, blueprint)

    return {
        "filename": file.filename,
        "data": normalized,
        "newly_extracted": extracted,
    }


@app.post("/api/generate/general-resume")
async def generate_general_resume(payload: dict = Body(...)) -> dict:
    record = _resolve_generation_record(payload.get("record"))
    target_role = payload.get("target_role")
    openai_api_key = payload.get("openai_api_key")

    try:
        generated = generate_general_resume_from_record(
            record,
            target_role=target_role,
            api_key_override=openai_api_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - network/runtime failure
        raise HTTPException(status_code=500, detail=f"Resume generation failed: {exc}") from exc

    return {
        **generated.model_dump(mode="json"),
        "rendered_text": render_resume_document(generated.resume),
    }


@app.post("/api/generate/tailored-resume")
async def generate_tailored_resume(payload: dict = Body(...)) -> dict:
    record = _resolve_generation_record(payload.get("record"))
    job_description = payload.get("job_description")
    target_role = payload.get("target_role")
    openai_api_key = payload.get("openai_api_key")
    base_resume = payload.get("base_resume")

    try:
        tailored = tailor_resume_to_job_description(
            record,
            job_description=job_description,
            target_role=target_role,
            api_key_override=openai_api_key,
            base_resume=base_resume,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - network/runtime failure
        raise HTTPException(status_code=500, detail=f"Resume tailoring failed: {exc}") from exc

    return {
        **tailored.model_dump(mode="json"),
        "rendered_text": render_resume_document(tailored.resume),
    }
