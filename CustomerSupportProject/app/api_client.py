"""Cliente HTTP minimo usado exclusivamente por la interfaz Streamlit."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from . import config
from .schemas import ChatResponse, HealthResponse


class ApiError(RuntimeError):
    pass


def consultar(
    mensaje: str,
    *,
    session_id: str | None = None,
    feedback: str | None = None,
) -> ChatResponse:
    payload: dict[str, Any] = {
        "mensaje": mensaje,
        "session_id": session_id,
        "feedback": feedback,
    }
    data = _request_json("/chat", method="POST", payload=payload)
    return ChatResponse.model_validate(data)


def comprobar_api() -> HealthResponse:
    return HealthResponse.model_validate(_request_json("/health"))


def finalizar_sesion(session_id: str) -> None:
    _request_json(f"/session/{session_id}/finalizar", method="POST", payload={})


def _request_json(
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{config.API_BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(
            request, timeout=config.TIMEOUT_SECONDS
        ) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode("utf-8", errors="replace")
        try:
            mensaje = json.loads(detalle).get("detail", detalle)
        except json.JSONDecodeError:
            mensaje = detalle
        raise ApiError(str(mensaje)) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ApiError(
            f"No se puede conectar con la API en {config.API_BASE_URL}."
        ) from exc
    except json.JSONDecodeError as exc:
        raise ApiError("La API ha devuelto una respuesta no válida.") from exc
