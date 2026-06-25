"""Indexacion persistente de FAQ y manual en ChromaDB."""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from . import config


logger = logging.getLogger("proyecto_base.indexing")

STOPWORDS = {
    "algo", "como", "con", "cual", "cuando", "del", "desde", "donde", "dos",
    "esta", "este", "esto", "hay", "las", "los", "mas", "para", "pero", "por",
    "porque", "que", "sin", "sobre", "sus", "una", "uno",
}
TERMINOS_GENERICOS = {
    "internet", "movistar", "router", "smart", "tipo", "wifi", "wifi6",
}


@lru_cache(maxsize=1)
def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model=config.EMBEDDING_MODEL,
        base_url=config.OLLAMA_BASE_URL,
    )


@lru_cache(maxsize=2)
def _get_store(collection_name: str) -> Chroma:
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=config.PERSIST_DIR,
        collection_metadata={"hnsw:space": "cosine"},
    )


def get_store_n1() -> Chroma:
    return _get_store(config.FAQ_COLLECTION)


def get_store_n2() -> Chroma:
    return _get_store(config.MANUAL_COLLECTION)


def indexar() -> dict[str, int]:
    """Indexa las dos fuentes sin duplicar vectores en cada arranque."""
    faq = _preparar_faq(config.FAQ_PDF_PATH)
    manual = _preparar_documentos(
        config.MANUAL_PDF_PATH,
        nivel="N2",
        chunk_size=config.MANUAL_CHUNK_SIZE,
    )
    _sincronizar_store(get_store_n1(), faq, "faq")
    _sincronizar_store(get_store_n2(), manual, "manual")
    resumen = {
        "fragmentos_faq_n1": len(faq),
        "fragmentos_manual_n2": len(manual),
    }
    logger.info(
        "Chroma listo: %d fragmentos N1 y %d fragmentos N2",
        len(faq),
        len(manual),
    )
    return resumen


def resumen_indexacion() -> dict[str, int]:
    return {
        "fragmentos_faq_n1": _collection_count(get_store_n1()),
        "fragmentos_manual_n2": _collection_count(get_store_n2()),
    }


def buscar_n1(pregunta: str) -> list[tuple[Document, float]]:
    return get_store_n1().similarity_search_with_relevance_scores(
        pregunta, k=config.TOP_K_N1
    )


def buscar_n2(pregunta: str) -> list[tuple[Document, float]]:
    return get_store_n2().similarity_search_with_relevance_scores(
        pregunta, k=config.TOP_K_N2
    )


def coincidencias_utiles(pregunta: str, documentos: list[Document]) -> set[str]:
    tokens_pregunta = set(_tokenizar(pregunta))
    tokens_contexto = {
        token
        for documento in documentos
        for token in _tokenizar(documento.page_content)
    }
    return {
        token
        for token in tokens_pregunta & tokens_contexto
        if token not in TERMINOS_GENERICOS
    }


def fuentes_resumidas(resultados: list[tuple[Document, float]]) -> list[str]:
    fuentes: list[str] = []
    for documento, _ in resultados:
        pagina = int(documento.metadata.get("page", 0)) + 1
        etiqueta = f"{documento.metadata.get('source_label', 'Documento')}, pagina {pagina}"
        if etiqueta not in fuentes:
            fuentes.append(etiqueta)
    return fuentes


def _preparar_documentos(
    path: Path, *, nivel: str, chunk_size: int
) -> list[Document]:
    if not path.exists():
        raise FileNotFoundError(f"No se encuentra la fuente RAG: {path}")

    paginas = PyPDFLoader(str(path)).load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    documentos = splitter.split_documents(paginas)
    firma = _firma_fuente(path, chunk_size)
    source_label = (
        "FAQ Smart WiFi 6" if nivel == "N1"
        else "Manual de configuracion Smart WiFi 6"
    )
    for indice, documento in enumerate(documentos):
        documento.metadata.update(
            {
                "nivel": nivel,
                "source": path.name,
                "source_label": source_label,
                "index_signature": firma,
                "chunk": indice,
            }
        )
    return documentos


def _preparar_faq(path: Path) -> list[Document]:
    """Convierte cada una de las 50 preguntas del PDF en un documento."""
    if not path.exists():
        raise FileNotFoundError(f"No se encuentra la fuente RAG: {path}")

    paginas = PyPDFLoader(str(path)).load()
    firma = _firma_fuente(path, config.FAQ_CHUNK_SIZE)
    documentos: list[Document] = []
    pregunta: list[str] = []
    respuesta: list[str] = []
    pagina_inicio = 0
    dentro_listado = False
    leyendo_pregunta = False

    def guardar() -> None:
        nonlocal pregunta, respuesta
        if not pregunta or not respuesta:
            return
        numero = len(documentos) + 1
        texto = f"{' '.join(pregunta)}\n{' '.join(respuesta)}"
        documentos.append(
            Document(
                page_content=texto.strip(),
                metadata={
                    "nivel": "N1",
                    "source": path.name,
                    "source_label": "FAQ Smart WiFi 6",
                    "index_signature": firma,
                    "chunk": numero - 1,
                    "question_number": numero,
                    "page": pagina_inicio,
                },
            )
        )
        pregunta = []
        respuesta = []

    for pagina in paginas:
        numero_pagina = int(pagina.metadata.get("page", 0))
        for linea_cruda in pagina.page_content.splitlines():
            linea = linea_cruda.strip()
            if not linea:
                continue
            if "Las 50 preguntas ordenadas" in linea:
                dentro_listado = True
                continue
            if dentro_listado and linea.startswith("Tabla comparativa"):
                guardar()
                dentro_listado = False
                break
            if not dentro_listado:
                continue

            empieza_pregunta = linea.startswith("¿") or linea.startswith(
                "Si en mi instalación antigua"
            )
            if empieza_pregunta:
                guardar()
                pregunta = [linea]
                respuesta = []
                pagina_inicio = numero_pagina
                leyendo_pregunta = not linea.endswith("?")
                continue
            if leyendo_pregunta:
                pregunta.append(linea)
                leyendo_pregunta = not linea.endswith("?")
                continue
            if pregunta:
                # Los números sueltos son referencias/paginación del PDF.
                if not re.fullmatch(r"\d+\.?", linea):
                    respuesta.append(linea)

    guardar()
    if len(documentos) != 50:
        logger.warning(
            "Se esperaban 50 preguntas FAQ y se han extraido %d",
            len(documentos),
        )
    return documentos


def _sincronizar_store(
    store: Chroma, documentos: list[Document], prefijo: str
) -> None:
    existentes = store.get(include=["metadatas"])
    ids_existentes = existentes.get("ids", [])
    metadatos = existentes.get("metadatas", [])
    firma = documentos[0].metadata["index_signature"] if documentos else ""
    vigente = (
        len(ids_existentes) == len(documentos)
        and bool(metadatos)
        and all(meta.get("index_signature") == firma for meta in metadatos)
    )
    if vigente:
        return

    if ids_existentes:
        store.delete(ids=ids_existentes)
    ids = [f"{prefijo}_{indice:04d}" for indice in range(len(documentos))]
    if documentos:
        store.add_documents(documentos, ids=ids)


def _collection_count(store: Chroma) -> int:
    return len(store.get(include=[]).get("ids", []))


def _firma_fuente(path: Path, chunk_size: int) -> str:
    stat = path.stat()
    contenido = f"{path.name}:{stat.st_size}:{stat.st_mtime_ns}:{chunk_size}"
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()


def _tokenizar(texto: str) -> list[str]:
    limpio = unicodedata.normalize("NFKD", texto.lower())
    limpio = "".join(c for c in limpio if not unicodedata.combining(c))
    tokens = re.findall(r"[a-z0-9]{3,}", limpio)
    return [token for token in tokens if token not in STOPWORDS]
