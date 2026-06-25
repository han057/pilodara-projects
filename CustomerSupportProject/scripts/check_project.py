"""Comprobaciones rápidas de estructura e importaciones del proyecto."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    required_modules = (
        "streamlit",
        "fastapi",
        "langchain",
        "langchain_chroma",
        "langchain_text_splitters",
        "chromadb",
        "cryptography",
        "langchain_community",
        "langchain_ollama",
        "langgraph",
        "langgraph_api",
        "langgraph_cli",
        "pydantic",
        "pypdf",
        "dotenv",
        "uvicorn",
    )
    missing: list[str] = []
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(module_name)

    if missing:
        print("Faltan dependencias: " + ", ".join(missing))
        return 1

    from app import config
    from app.graph import construir_grafo

    sources = (config.FAQ_PDF_PATH, config.MANUAL_PDF_PATH)
    missing_sources = [str(path) for path in sources if not path.is_file()]
    if missing_sources:
        print("Faltan documentos RAG:")
        for path in missing_sources:
            print(f"  - {path}")
        return 1

    for path in sources:
        if PROJECT_ROOT not in path.parents:
            print(f"La fuente está fuera del proyecto: {path}")
            return 1

    construir_grafo()
    print("Proyecto validado correctamente.")
    print(f"FAQ: {config.FAQ_PDF_PATH.name}")
    print(f"Manual: {config.MANUAL_PDF_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
