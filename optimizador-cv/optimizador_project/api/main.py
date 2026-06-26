"""
FastAPI backend para el Optimizador de Currículums.
Proporciona API REST y sirve la interfaz web.
"""

import logging
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response

from optimizador.config import LLM_CONFIG
from optimizador.utils.pdf_loader import load_document
from optimizador.graph.workflow import create_workflow
from optimizador.rag.offer_store import get_offer_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Optimizador de Currículums", version="2.0.0")

# Servir archivos estáticos (HTML, CSS, JS)
STATIC_DIR = Path(__file__).parent.parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_frontend():
    """Sirve la página principal."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend no encontrado")
    return FileResponse(str(index_path))


@app.on_event("startup")
async def startup_event():
    """Preload job offers into ChromaDB on startup. Rebuilds if file count changed."""
    try:
        from optimizador.config import OFERTAS_DIR
        logger.info("Precargando ofertas de empleo...")

        # Check if we need to rebuild (file count mismatch)
        file_count = len(list(OFERTAS_DIR.glob("*.txt"))) + len(list(OFERTAS_DIR.glob("*.pdf")))
        store = get_offer_store()
        indexed_count = len(store.list_offers())

        if indexed_count < file_count:
            logger.info(f"Detectadas nuevas ofertas ({indexed_count} indexadas vs {file_count} archivos). Reconstruyendo índice...")
            from optimizador.rag.offer_store import reset_offer_store
            reset_offer_store()
            store = get_offer_store(force_rebuild=True)
            indexed_count = len(store.list_offers())

        logger.info(f"Ofertas cargadas: {indexed_count} ofertas indexadas")
    except Exception as e:
        logger.warning(f"No se pudieron precargar ofertas: {e}")


@app.post("/api/optimize")
async def optimize_cv(
    cv_file: UploadFile = File(..., description="Archivo del CV (PDF o TXT)"),
):
    """
    Endpoint principal: recibe solo el CV, busca la oferta más compatible
    automáticamente y devuelve el CV optimizado con puntuaciones ATS.
    """
    # ---- 1. Cargar CV ----
    try:
        cv_text = await _read_upload(cv_file)
        if not cv_text or len(cv_text.strip()) < 20:
            raise HTTPException(status_code=400, detail="El CV está vacío o es demasiado corto")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error leyendo el CV: {str(e)}")

    # ---- 2. Ejecutar workflow (match + optimización) ----
    try:
        logger.info("Iniciando workflow de optimización...")
        workflow = create_workflow()
        final_state = workflow.invoke(cv_text)

        # Verificar errores
        if final_state.errors:
            return JSONResponse(
                status_code=200,
                content={"success": False, "errors": final_state.errors},
            )

        # Construir respuesta
        result = {
            "success": True,
            "ats_score": None,
            "found_keywords": final_state.found_keywords or [],
            "missing_keywords": final_state.missing_keywords or [],
            "changes_made": final_state.changes_made or [],
            "improvements_applied": final_state.improvements_applied or [],
            "recommendations": final_state.ats_recommendations or [],
            "keywords_added": final_state.keywords_added or [],
            "match_score": final_state.match_score or 0,
            "final_cv": final_state.final_cv or "",
            "matched_offer": {
                "filename": final_state.matched_offer_filename,
                "similarity_score": final_state.offer_match_score,
            },
        }

        if final_state.ats_score:
            result["ats_score"] = {
                "keyword_match": final_state.ats_score.keyword_match,
                "format_score": final_state.ats_score.format_score,
                "completeness": final_state.ats_score.completeness,
                "overall_score": final_state.ats_score.overall_score,
            }

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error en workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error durante la optimización: {str(e)}. "
                   f"Verifica que Ollama esté corriendo y los modelos descargados."
        )


@app.get("/api/health")
async def health_check():
    """Verifica que el servidor y Ollama estén funcionando."""
    import requests

    ollama_ok = False
    ollama_base_url = LLM_CONFIG["base_url"].rstrip("/")
    try:
        resp = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
        ollama_ok = resp.status_code == 200
        models = [m["name"] for m in resp.json().get("models", [])] if ollama_ok else []
    except Exception:
        models = []

    return {
        "status": "ok",
        "ollama_base_url": ollama_base_url,
        "ollama_running": ollama_ok,
        "available_models": models,
        "llm_ready": any(LLM_CONFIG["model"] in m for m in models),
        "embeddings_ready": any("nomic" in m for m in models),
    }


@app.get("/api/offers")
async def list_offers():
    """Lista las ofertas de empleo indexadas en el sistema."""
    try:
        store = get_offer_store()
        offers = store.list_offers()
        return {"count": len(offers), "offers": offers}
    except Exception as e:
        return {"count": 0, "offers": [], "error": str(e)}


@app.get("/api/offers/{filename}")
async def get_offer_detail(filename: str):
    """Obtiene el texto completo de una oferta específica."""
    try:
        store = get_offer_store()
        text = store.get_offer_text(filename)
        if text is None:
            raise HTTPException(status_code=404, detail="Oferta no encontrada")
        meta = store._parse_metadata(text)
        return {"filename": filename, "full_text": text, **meta}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _read_upload(file: UploadFile) -> str:
    """
    Lee un archivo subido y extrae su texto.
    Guarda temporalmente para usar PyPDFLoader con PDFs.
    """
    suffix = Path(file.filename).suffix.lower() if file.filename else ".txt"

    if suffix == ".pdf":
        # PyPDFLoader necesita un archivo en disco
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp.flush()
            text = load_document(tmp.name)
        Path(tmp.name).unlink(missing_ok=True)
        return text
    elif suffix in (".txt", ".md"):
        content = await file.read()
        return content.decode("utf-8")
    else:
        raise ValueError(f"Formato no soportado: {suffix}. Usa PDF o TXT.")


@app.post("/api/download-pdf")
async def download_cv_pdf(cv_text: str = Form(..., description="Texto del CV a convertir en PDF")):
    """
    Convierte el texto del CV optimizado en un archivo PDF descargable.
    """
    from fpdf import FPDF

    class CVPdf(FPDF):
        def header(self):
            pass

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    pdf = CVPdf()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)

    def safe_text(text: str) -> str:
        """Sanitiza texto para fpdf2 (latin-1 compatible)."""
        # Reemplazar caracteres problemáticos
        replacements = {
            '\u2022': '-',     # bullet •
            '\u2013': '-',     # en dash –
            '\u2014': '-',     # em dash —
            '\u2018': "'",     # left single quote
            '\u2019': "'",     # right single quote
            '\u201c': '"',     # left double quote
            '\u201d': '"',     # right double quote
            '\u2026': '...',   # ellipsis
            '\u00b0': 'deg',   # degree symbol
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        # Eliminar cualquier caracter fuera de latin-1
        return text.encode('latin-1', errors='replace').decode('latin-1')

    for line in cv_text.split("\n"):
        stripped = line.strip()

        if not stripped:
            pdf.ln(4)
            continue

        stripped = safe_text(stripped)

        # Detectar secciones (títulos en mayúsculas o con ---)
        is_section = (
            stripped.isupper() and len(stripped) > 3
            or stripped.startswith("---") and stripped.endswith("---")
        )

        if is_section:
            cleaned = stripped.replace("---", "").strip()
            if cleaned:
                pdf.ln(3)
                pdf.set_font("Helvetica", "B", 13)
                pdf.set_text_color(40, 40, 40)
                pdf.cell(0, 8, cleaned, ln=True)
                pdf.set_draw_color(60, 60, 60)
                pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
                pdf.ln(3)
        elif stripped.startswith("-") or stripped.startswith("*"):
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            bullet_text = stripped.lstrip("-* ")
            pdf.cell(5, 5, "-")
            pdf.multi_cell(0, 5, f" {bullet_text}")
            pdf.ln(1)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(0, 5, stripped)
            pdf.ln(1)

    pdf_bytes = pdf.output()
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=cv_optimizado.pdf"},
    )
