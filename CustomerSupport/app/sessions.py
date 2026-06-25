"""Almacen sencillo de sesiones para la API.

Se conserva el diccionario en memoria del proyecto base. El nivel activo indica
por donde debe entrar el siguiente intento: 1 (FAQ), 2 (manual) o 3 (humano).
"""

from __future__ import annotations

import uuid
from typing import Any


SESIONES: dict[str, dict[str, Any]] = {}


def crear_sesion() -> str:
    session_id = uuid.uuid4().hex
    SESIONES[session_id] = {
        "nivel": 1,
        "historial": [],
        "activa": True,
    }
    return session_id


def get_sesion(session_id: str) -> dict[str, Any] | None:
    return SESIONES.get(session_id)


def escalar(session_id: str, motivo: str) -> None:
    sesion = SESIONES.get(session_id)
    if sesion is None:
        return
    sesion["nivel"] = min(int(sesion.get("nivel", 1)) + 1, 3)
    sesion["motivo_escalado"] = motivo


def fijar_nivel(session_id: str, nivel: int, motivo: str = "") -> None:
    sesion = SESIONES.get(session_id)
    if sesion is None:
        return
    sesion["nivel"] = max(1, min(nivel, 3))
    if motivo:
        sesion["motivo_escalado"] = motivo


def registrar_turno(
    session_id: str,
    pregunta: str,
    respuesta: str,
    nivel: str,
    feedback: str | None = None,
) -> None:
    sesion = SESIONES.get(session_id)
    if sesion is not None:
        sesion["historial"].append(
            {
                "pregunta": pregunta,
                "respuesta": respuesta,
                "nivel": nivel,
                "feedback": feedback,
            }
        )


def finalizar(session_id: str) -> dict[str, Any] | None:
    sesion = SESIONES.get(session_id)
    if sesion is not None:
        sesion["activa"] = False
    return sesion
