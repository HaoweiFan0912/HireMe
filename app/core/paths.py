from pathlib import Path


APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent
STATIC_DIR = APP_DIR / "web" / "static"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
DATA_DIR = RUNTIME_DIR / "data"
PDF_RENDER_SCRIPT = APP_DIR / "extraction" / "render_pdf_pages.swift"
