"""Configuración central del soporte del Router Smart WiFi 6."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
load_dotenv(BASE_DIR / ".env")

# Modelos locales servidos por Ollama.
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "gemma3:4b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "180"))

# FastAPI es la unica puerta de entrada a la logica de negocio.
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_BASE_URL = os.getenv("API_BASE_URL", f"http://{API_HOST}:{API_PORT}")

# Fuentes RAG incluidas dentro del proyecto.
FAQ_PDF_PATH = DATA_DIR / (
    "Las 50 preguntas más frecuentes sobre el router Smart WiFi 6 de Movistar.pdf"
)
MANUAL_PDF_PATH = DATA_DIR / "manual-de-configuracion-del-router-movistar_compress.pdf"

# ChromaDB persistente. Cada nivel tiene su propia coleccion para impedir que N1
# recupere contenido tecnico del manual.
PERSIST_DIR = str(BASE_DIR / "chroma_db")
FAQ_COLLECTION = "router_smart_wifi6_faq_n1"
MANUAL_COLLECTION = "router_smart_wifi6_manual_n2"

TOP_K_N1 = 4
TOP_K_N2 = 5
FAQ_CHUNK_SIZE = 1400
MANUAL_CHUNK_SIZE = 1900
CHUNK_OVERLAP = 180

# Los scores de Chroma se combinan con coincidencias lexicas no genericas. Esto
# evita responder sobre piezas o caracteristicas que no aparecen en los PDFs.
N1_MIN_RELEVANCE = float(os.getenv("N1_MIN_RELEVANCE", "0.30"))
N2_MIN_RELEVANCE = float(os.getenv("N2_MIN_RELEVANCE", "0.26"))

HUMAN_PHONE = os.getenv("HUMAN_PHONE", "900 123 456")
HUMAN_EMAIL = os.getenv(
    "HUMAN_EMAIL", "soporte.smartwifi6@example.com"
)
