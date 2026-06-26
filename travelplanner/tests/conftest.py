import pytest
from config import OLLAMA_URL, OLLAMA_MODEL


def ollama_disponible() -> bool:
    try:
        import requests
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def modelo_disponible() -> bool:
    if not ollama_disponible():
        return False
    try:
        import requests
        r = requests.post(
            f"{OLLAMA_URL}/api/show",
            json={"name": OLLAMA_MODEL},
            timeout=2,
        )
        return r.status_code == 200
    except Exception:
        return False


pytestmark_agentes = pytest.mark.skipif(
    not modelo_disponible(),
    reason=f"Requiere Ollama con modelo {OLLAMA_MODEL} (ollama pull {OLLAMA_MODEL})",
)
