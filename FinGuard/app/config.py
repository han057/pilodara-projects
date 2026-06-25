# app/config.py
# Centralized configuration for FinGuard
#
# All environment-dependent settings in one place.
# Docker sets OLLAMA_HOST=http://ollama:11434
# Local dev uses default http://127.0.0.1:11434

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)

# Ollama — reads OLLAMA_HOST env var set by docker-compose
# Falls back to localhost for local development
OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
EMBED_MODEL  = "nomic-embed-text"
LLM_MODEL    = "qwen3:8b"

# ChromaDB
CHROMA_PATH      = "./data/chroma_db"
COLLECTION_NAME  = "sec_filings"

# FMP API
FMP_API_KEY = os.getenv("FMP_API_KEY", "")
FMP_BASE_URL = "https://financialmodelingprep.com/stable"

# SEC EDGAR
SEC_HEADERS = {
    "User-Agent": "FinGuard Project nataliastekolnikova2025@gmail.com"
}
DOCS_DIR = Path("./docs")
