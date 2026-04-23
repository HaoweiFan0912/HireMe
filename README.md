# HireMe

HireMe is a visual workspace for extracting structured resume data from uploaded documents. Users can upload resumes, transcripts, recommendation letters, internship documents, and related files, review the extracted draft in the browser, edit it manually, and save the final record to the backend.

## Features

- Visualizes a blank schema and the current saved JSON record.
- Supports PDF, DOCX, plain text, Markdown, CSV, and common image uploads.
- Extracts supported fields into a fixed resume schema with OpenAI.
- Merges repeated education, experience, activity, and skill objects across multiple uploads.
- Allows full manual editing before saving to the backend record.
- Generates a general-purpose resume draft from the saved structured profile.
- Generates a tailored resume draft from the saved structured profile plus a job description.
- Supports a browser-provided OpenAI API key while still allowing environment-based configuration.
- Renders print-ready HTML versions of generated resumes with robust null-value filtering.
- Provides instant browser pop-up previews for both general and tailored generated resumes.

## Start

From the project root:

```bash
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000`.

On macOS, you can also double-click `start.command`. It installs missing dependencies, finds an open port, starts the server, and opens the browser automatically.

## Resume Generation API

After you have a saved structured record, you can generate resume drafts through the backend API.

Generate a general resume:

```bash
curl -X POST http://127.0.0.1:8000/api/generate/general-resume \
  -H "Content-Type: application/json" \
  -d '{
    "target_role": "Data Science Intern"
  }'
```

Generate a job-tailored resume:

```bash
curl -X POST http://127.0.0.1:8000/api/generate/tailored-resume \
  -H "Content-Type: application/json" \
  -d '{
    "target_role": "Machine Learning Intern",
    "job_description": "Paste the target job description here."
  }'
```

Both endpoints also accept:

- `record`: explicit structured resume JSON. If omitted, the backend uses the saved record under `runtime/data/`.
- `openai_api_key`: optional per-request API key override.
- `base_resume`: optional general resume payload to reuse when calling `/api/generate/tailored-resume`.

Both responses return structured resume content plus a `rendered_text` field for quick inspection.

## Tailored Prompt Eval

The repo includes a fixed first-round prompt-tuning eval set under `evals/tailored_resume/`:

- `profile_maya_chen_v0.json`: frozen candidate profile
- `cases_v0.json`: 10 job-description cases split into close-fit, adjacent-fit, and stretch-fit tiers

Run the offline eval runner from the repo root:

```bash
python3 scripts/evaluate_tailored_resume.py
```

Useful options:

```bash
python3 scripts/evaluate_tailored_resume.py --skip-judge
python3 scripts/evaluate_tailored_resume.py --case-id close_fit_machine_learning_intern
python3 scripts/evaluate_tailored_resume.py --output runtime/evals/tailored_resume_eval.json
```

The current tailored pipeline uses an internal multi-step flow:

1. JD analysis
2. candidate evidence alignment
3. tailored drafting
4. safety review and optional revision

The eval runner compares:

- `general resume`
- `v0 baseline tailored resume` (single-shot prompt)
- `current tailored resume` (multi-step pipeline)

## API Key Flow

- The browser can store a user-provided OpenAI API key locally and send it only during upload requests.
- If the browser field is empty, the backend falls back to `OPENAI_API_KEY` if that environment variable is configured.
- The project includes `API_KEYS.py` and `app/config/api_keys.py` as optional local configuration points, but they no longer ship with a populated secret.

## Project Structure

```text
HireMe/
├── app/
│   ├── config/
│   │   └── api_keys.py
│   ├── core/
│   │   └── paths.py
│   ├── extraction/
│   │   ├── client.py
│   │   ├── common.py
│   │   ├── document_content.py
│   │   ├── education.py
│   │   ├── entity_resolution.py
│   │   ├── experience.py
│   │   ├── extraction_skills.py
│   │   ├── extractor.py
│   │   ├── merge.py
│   │   ├── models.py
│   │   ├── prompt_collection.py
│   │   ├── render_pdf_pages.swift
│   │   ├── schema.py
│   │   ├── schema_tools.py
│   │   └── skills_engine.py
│   ├── generation/
│   │   ├── models.py
│   │   ├── prompt_collection.py
│   │   └── service.py
│   ├── storage/
│   │   └── records.py
│   ├── web/
│   │   └── static/
│   │       ├── app.js
│   │       ├── index.html
│   │       └── styles.css
│   ├── main.py
│   └── utils.py
├── example/
├── evals/
├── runtime/
│   └── data/
├── scripts/
│   ├── evaluate_tailored_resume.py
│   └── generate_sim_example_files.py
├── API_KEYS.py
├── README.md
├── requirements.txt
└── start.command
```

## File Guide

### Root

- `README.md`: project overview and maintenance guide.
- `requirements.txt`: Python dependencies.
- `start.command`: local launcher for macOS.
- `API_KEYS.py`: top-level default API key entrypoint.

### `app/main.py`

- `app/main.py`: FastAPI application factory and HTTP routes.

### `app/utils.py`

- `app/utils.py`: HTML rendering utility for generating print-ready resumes with dynamic section filtering.

### `app/core/`

- `app/core/paths.py`: shared project paths used by the backend.

### `app/storage/`

- `app/storage/records.py`: load/save helpers for the current persisted record.

### `app/config/`

- `app/config/api_keys.py`: internal fallback location for an optional local OpenAI API key.

### `app/extraction/`

- `app/extraction/schema.py`: target resume schema definition.
- `app/extraction/models.py`: structured Pydantic response models used for parsing extraction and refinement calls.
- `app/extraction/schema_tools.py`: blank-template generation, blueprint generation, and normalization helpers.
- `app/extraction/document_content.py`: file reading and upload-content preparation for PDFs, DOCX files, text files, and images.
- `app/extraction/client.py`: OpenAI client creation and API key resolution.
- `app/extraction/common.py`: shared normalization, comparison, and preview helpers used across extraction modules.
- `app/extraction/entity_resolution.py`: link-label normalization, full-name lookup, and location lookup for schools and organizations.
- `app/extraction/education.py`: education-specific post-processing for honors and courses.
- `app/extraction/experience.py`: experience evidence selection and structured rewriting.
- `app/extraction/skills_engine.py`: skill inference, normalization, and GPT-based deduplication.
- `app/extraction/merge.py`: multi-file object matching and record merge behavior.
- `app/extraction/extraction_skills.py`: extraction rules and prompt-facing skills text.
- `app/extraction/prompt_collection.py`: prompt builders for extraction, lookup, matching, rewriting, and deduplication.
- `app/extraction/render_pdf_pages.swift`: scanned-PDF page rendering helper.
- `app/extraction/extractor.py`: thin orchestration layer that wires document reading, extraction, refinement, and merge-facing exports together.

### `app/generation/`

- `app/generation/models.py`: structured response models for general and job-tailored resume drafts.
- `app/generation/prompt_collection.py`: prompt builders for general resume generation and JD-based tailoring.
- `app/generation/service.py`: OpenAI orchestration and plain-text rendering helpers for generated resumes.

### `app/web/static/`

- `app/web/static/index.html`: page layout.
- `app/web/static/app.js`: browser-side schema editor, upload flow, save flow, and API key storage.
- `app/web/static/styles.css`: UI styling.

### `scripts/`

- `scripts/evaluate_tailored_resume.py`: offline evaluator for general, baseline tailored, and current tailored prompt performance.
- `scripts/generate_sim_example_files.py`: generates the simulated `.docx` documents in `example/`.

### `evals/tailored_resume/`

- `evals/tailored_resume/profile_maya_chen_v0.json`: frozen profile used for prompt tuning.
- `evals/tailored_resume/cases_v0.json`: annotated JD cases and expected signals for the first eval round.

### `example/`

- `example/SIM-University-of-California-Irvine-Transcript.docx`
- `example/SIM-Northeastern-University-Transcript.docx`
- `example/SIM-Columbia-University-Transcript.docx`
- `example/SIM-Amazon-Web-Services-Internship-Certificate.docx`
- `example/SIM-Amazon-Web-Services-Recommendation-Letter.docx`
- `example/SIM-Microsoft-Corporation-Internship-Certificate.docx`
- `example/SIM-Complete-Resume.docx`

### `runtime/data/`

- `runtime/data/current_record.json`: current saved structured record when a manual save exists.
- `runtime/data/current_record_meta.json`: metadata about the saved record.

## Reading Order

1. Start with `app/extraction/schema.py`.
2. Then read `app/main.py`.
3. Then read `app/extraction/extractor.py`.
4. For extraction internals, continue with `app/extraction/document_content.py`, `app/extraction/entity_resolution.py`, `app/extraction/education.py`, `app/extraction/experience.py`, `app/extraction/skills_engine.py`, and `app/extraction/merge.py`.
5. For persistence, read `app/storage/records.py`.
6. For UI changes, read `app/web/static/app.js` and `app/web/static/styles.css`.

## Maintenance Notes

- Only manual save updates the backend record files under `runtime/data/`.
- Uploaded extraction results stay as draft data until the user saves them.
- Simulated example files are regenerated from `scripts/generate_sim_example_files.py`.
- The extraction pipeline is intentionally split by responsibility so behavior changes should usually happen in one focused module rather than in the top-level extractor.
