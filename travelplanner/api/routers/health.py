import os

import requests
from fastapi import APIRouter
from sqlalchemy import text

from api.deps.database import get_session

router = APIRouter()

OLLAMA_URL = os.getenv("OLLAMA_API_BASE_URL", "http://localhost:11434")


@router.get("/")
def health():
    db_ok = False
    try:
        db = get_session()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        db_ok = False
    ollama_ok = _check_ollama()
    return {
        "status": "ok" if (db_ok and ollama_ok) else "degraded",
        "database": "connected" if db_ok else "unavailable",
        "ollama": "connected" if ollama_ok else "unavailable",
    }


@router.get("/ollama")
def ollama_health():
    return {"status": "connected" if _check_ollama() else "unavailable"}


def _check_ollama() -> bool:
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False
