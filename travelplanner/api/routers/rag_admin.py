import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter()

DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "rag" / "documents"


@router.get("/documents")
def list_indexed_documents(include_stats: bool = False):
    try:
        from rag.ingest import list_documents, get_collection_stats
        docs = list_documents()
        result = {"documents": docs}
        if include_stats:
            result["stats"] = get_collection_stats()
        else:
            result["stats"] = {"total_chunks": 0, "documents": [d["path"] for d in docs]}
        return result
    except Exception as exc:
        logger.exception("Error listing documents")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/stats")
def get_stats():
    try:
        from rag.ingest import get_collection_stats
        return get_collection_stats()
    except Exception as exc:
        logger.exception("Error getting stats")
        return {"total_chunks": 0, "documents": []}


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    category: str = Form("general"),
    city: str | None = Form(None),
):
    allowed = {".pdf", ".txt", ".md", ".csv"}
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Formato no permitido: {ext}. Usa: {', '.join(allowed)}")

    target_dir = DOCS_DIR / category
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / file.filename

    try:
        content = file.file.read()
        if not content.strip():
            raise HTTPException(status_code=400, detail="Archivo vacío")
        with open(dest, "wb") as f:
            f.write(content)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error guardando archivo: {exc}")

    try:
        from rag.ingest import index_file
        result = index_file(dest)
        return {"status": "uploaded", "path": str(dest.relative_to(DOCS_DIR)), "size": len(content), "chunks": result["chunks"]}
    except Exception as exc:
        logger.exception("Error indexando archivo tras subida")
        raise HTTPException(status_code=500, detail=f"Archivo guardado pero error al indexar: {exc}")


@router.post("/reindex")
def reindex():
    try:
        from rag.ingest import index_all
        result = index_all()
        return result
    except Exception as exc:
        logger.exception("Error during reindex")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/query")
def test_query(query: str = Form(...), k: int = Form(5), category: str | None = Form(None)):
    try:
        from rag.rag_query import RAGQuery
        rag = RAGQuery()
        filtro = {"categoria": category} if category else None
        results = rag.search(query, k=k, metadata_filter=filtro)
        return {"results": results}
    except Exception as exc:
        logger.exception("Error querying RAG")
        return {"results": [], "error": str(exc)}


@router.delete("/document")
def delete_document(path: str):
    full_path = DOCS_DIR / path
    if not full_path.exists() or not full_path.is_relative_to(DOCS_DIR):
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    full_path.unlink()
    return {"status": "deleted", "path": path}
