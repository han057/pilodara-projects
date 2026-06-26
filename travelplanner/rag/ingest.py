import os
import re
import logging
from pathlib import Path

import httpx
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "documents"
CHROMA_DIR = BASE_DIR / "embeddings" / "vectorstore"

MODEL_NAME = "nomic-embed-text"

OLLAMA_URL = os.getenv("OLLAMA_API_BASE_URL", "http://localhost:11434")

# Palabras que aparecen en nombres de archivo pero NO son ciudades
_PALABRAS_NO_CIUDAD = {
    "general", "espana", "spain", "guia", "info", "datos",
    "transporte", "gastronomia", "barrios", "itinerario",
    "seguridad", "clima", "eventos", "tips", "dias", "semana",
    "semanas", "doc", "archivo", "documento",
}

LOADER_MAP = {
    ".pdf": PyPDFLoader,
    ".txt": lambda p: TextLoader(str(p), encoding="utf-8"),
    ".md": lambda p: TextLoader(str(p), encoding="utf-8"),
    ".csv": lambda p: CSVLoader(str(p), encoding="utf-8"),
}


def _ciudad_desde_nombre(nombre: str) -> str | None:
    """Extrae el nombre de ciudad de un filename o carpeta dividiéndolo por separadores
    y descartando palabras que no son ciudades (categorías, números, etc.)."""
    partes = re.split(r"[_\-\s]+", nombre.lower())
    return next(
        (p for p in partes if p and not p.isdigit() and p not in _PALABRAS_NO_CIUDAD),
        None,
    )


def extract_metadata(path: Path):
    relative = path.relative_to(DOCS_DIR)
    categoria = relative.parts[0] if len(relative.parts) > 1 else "general"
    filename = path.stem.lower()

    ciudad = _ciudad_desde_nombre(filename)

    # Fallback: intentar inferir ciudad desde la carpeta padre
    if not ciudad and len(relative.parts) > 2:
        ciudad = _ciudad_desde_nombre(relative.parts[-2])

    return {
        "categoria": categoria,
        "ciudad": ciudad,
        "filename": filename,
        "source": str(relative),
    }


def load_file(path: Path) -> list:
    ext = path.suffix.lower()
    loader_fn = LOADER_MAP.get(ext)
    if loader_fn is None:
        logger.warning("Formato no soportado: %s", ext)
        return []
    try:
        loader = loader_fn(str(path))
        docs = loader.load()
        metadata = extract_metadata(path)
        for d in docs:
            d.metadata.update(metadata)
        logger.info("Cargado %s (%d páginas/chunks)", path.name, len(docs))
        return docs
    except Exception:
        logger.exception("Error cargando %s", path)
        return []


def load_documents(docs_dir: Path | None = None):
    docs_dir = docs_dir or DOCS_DIR
    docs = []
    for root, _, files in os.walk(docs_dir):
        for f in files:
            path = Path(root) / f
            docs.extend(load_file(path))
    return docs


def split_documents(documents, chunk_size=500, chunk_overlap=100):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    return splitter.split_documents(documents)


class _BatchedEmbeddings:
    """Embedding function que llama a Ollama en lotes pequeños para evitar timeouts."""

    def __init__(self, model: str, base_url: str, batch_size: int = 32, timeout: int = 120):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.batch_size = batch_size
        self.timeout = timeout

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        r = httpx.post(
            f"{self.base_url}/api/embed",
            json={"model": self.model, "input": texts},
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()["embeddings"]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        total = len(texts)
        for i in range(0, total, self.batch_size):
            batch = texts[i: i + self.batch_size]
            logger.info("Embeddings lote %d–%d / %d", i + 1, min(i + self.batch_size, total), total)
            all_embeddings.extend(self._embed_batch(batch))
        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        return self._embed_batch([text])[0]


def index_file(path: Path, chroma_dir: Path | None = None) -> dict:
    """Indexa un único archivo y lo añade al vectorstore existente sin reindexar los demás."""
    chroma_dir = chroma_dir or CHROMA_DIR
    docs = load_file(path)
    if not docs:
        return {"status": "empty", "chunks": 0}

    chunks = split_documents(docs)
    filename = path.stem.lower()
    ids = [f"{filename}_{i}" for i in range(len(chunks))]
    embeddings = _BatchedEmbeddings(model=MODEL_NAME, base_url=OLLAMA_URL)

    logger.info("Indexando '%s': %d chunks", path.name, len(chunks))
    try:
        if chroma_dir.exists():
            db = Chroma(persist_directory=str(chroma_dir), embedding_function=embeddings)
            db.add_documents(documents=chunks, ids=ids)
        else:
            Chroma.from_documents(
                documents=chunks, embedding=embeddings,
                ids=ids, persist_directory=str(chroma_dir),
            )
        logger.info("Indexación de '%s' completada", path.name)
        return {"status": "ok", "chunks": len(chunks)}
    except Exception:
        logger.exception("Error indexando '%s'", path.name)
        raise


def build_vectorstore(chunks, chroma_dir: Path | None = None):
    chroma_dir = chroma_dir or CHROMA_DIR
    embeddings = _BatchedEmbeddings(model=MODEL_NAME, base_url=OLLAMA_URL)
    ids = [f"{chunk.metadata.get('filename', 'doc')}_{i}" for i, chunk in enumerate(chunks)]
    try:
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            ids=ids,
            persist_directory=str(chroma_dir),
        )
        return vectordb
    except Exception:
        logger.exception("Error construyendo vectorstore")
        raise


def get_collection_stats(chroma_dir: Path | None = None) -> dict:
    chroma_dir = chroma_dir or CHROMA_DIR
    try:
        embeddings = OllamaEmbeddings(
            model=MODEL_NAME,
            base_url=OLLAMA_URL,
            client_kwargs={"timeout": 60},
        )
        db = Chroma(
            persist_directory=str(chroma_dir),
            embedding_function=embeddings,
        )
        collection = db.get()
        return {
            "total_chunks": len(collection.get("ids", [])),
            "documents": list(set(
                m.get("source", "unknown")
                for m in collection.get("metadatas", [])
                if m
            )),
        }
    except Exception:
        logger.exception("Error obteniendo estadísticas")
        return {"total_chunks": 0, "documents": []}


def index_all(docs_dir: Path | None = None, chroma_dir: Path | None = None):
    logger.info("=== INICIO DE INDEXACIÓN ===")
    documents = load_documents(docs_dir)
    logger.info("Documentos cargados: %d", len(documents))
    if not documents:
        logger.warning("No hay documentos que indexar")
        return {"status": "empty", "documents": 0, "chunks": 0}
    chunks = split_documents(documents)
    logger.info("Chunks generados: %d", len(chunks))
    build_vectorstore(chunks, chroma_dir)
    logger.info("=== INDEXACIÓN COMPLETA ===")
    return {"status": "ok", "documents": len(documents), "chunks": len(chunks)}


def list_documents(docs_dir: Path | None = None) -> list[dict]:
    docs_dir = docs_dir or DOCS_DIR
    result = []
    for root, _, files in os.walk(docs_dir):
        category = Path(root).relative_to(docs_dir).parts[0] if root != str(docs_dir) else "general"
        for f in files:
            path = Path(root) / f
            ext = path.suffix.lower()
            if ext not in LOADER_MAP:
                continue
            metadata = extract_metadata(path)
            result.append({
                "name": f,
                "path": str(path.relative_to(docs_dir)),
                "category": metadata["categoria"],
                "city": metadata["ciudad"],
                "size": path.stat().st_size,
            })
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = index_all()
    print(f"\nResultado: {result}")
    stats = get_collection_stats()
    print(f"Stats: {stats}")
