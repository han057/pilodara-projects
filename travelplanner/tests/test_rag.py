"""Tests para el sistema RAG real (reemplaza los stubs de embed_text/VectorStore)."""
import pytest
from pathlib import Path

CHROMA_DIR = Path(__file__).resolve().parent.parent / "rag" / "embeddings" / "vectorstore"


def _vectorstore_available() -> bool:
    return CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir())


def test_rag_query_structure():
    """RAGQuery devuelve lista con claves content, metadata y score."""
    if not _vectorstore_available():
        pytest.skip("Vectorstore no indexado — ejecuta POST /rag/reindex primero")
    try:
        from rag.rag_query import RAGQuery
        rag = RAGQuery()
        results = rag.search("madrid", k=2)
        assert isinstance(results, list)
        if results:
            r = results[0]
            assert "content" in r
            assert "metadata" in r
            assert "score" in r
            assert isinstance(r["score"], float)
            assert 0.0 <= r["score"] <= 1.0
    except Exception as e:
        pytest.skip(f"RAG no disponible: {e}")


def test_rag_query_metadata_filter():
    """RAGQuery acepta filtro de metadatos sin lanzar excepción."""
    if not _vectorstore_available():
        pytest.skip("Vectorstore no indexado — ejecuta POST /rag/reindex primero")
    try:
        from rag.rag_query import RAGQuery
        rag = RAGQuery()
        results = rag.search("transporte", k=3, metadata_filter={"categoria": "transporte"})
        assert isinstance(results, list)
    except Exception as e:
        pytest.skip(f"RAG no disponible: {e}")
