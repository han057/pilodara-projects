"""API FastAPI del soporte del Router Smart WiFi 6."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from . import config, indexing, sessions
from .graph import construir_grafo
from .schemas import (
    ChatRequest,
    ChatResponse,
    FinalizarResponse,
    HealthResponse,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("proyecto_base")
RECURSOS: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Indexando FAQ y manual en ChromaDB...")
    RECURSOS["indexacion"] = indexing.indexar()
    logger.info("Compilando el grafo LangGraph...")
    RECURSOS["grafo"] = construir_grafo()
    logger.info("API preparada.")
    yield
    RECURSOS.clear()


app = FastAPI(
    title="Soporte Router Smart WiFi 6",
    description="API N1, N2 y escalado humano con LangGraph y ChromaDB.",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/")
def index():
    return {
        "servicio": "Soporte Router Smart WiFi 6",
        "interfaz": "Streamlit",
        "documentacion_api": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
def health():
    resumen = RECURSOS.get("indexacion") or indexing.resumen_indexacion()
    return HealthResponse(
        status="ok",
        modelo_llm=config.LLM_MODEL,
        modelo_embeddings=config.EMBEDDING_MODEL,
        **resumen,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    session_id = req.session_id or sessions.crear_sesion()
    sesion = sessions.get_sesion(session_id)
    if sesion is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if not sesion["activa"]:
        raise HTTPException(status_code=409, detail="La sesión ya está finalizada")
    if "grafo" not in RECURSOS:
        raise HTTPException(status_code=503, detail="El grafo aún no está preparado")

    if req.feedback == "insatisfecho":
        sessions.escalar(session_id, "feedback del usuario")

    estado_inicial = {
        "pregunta": req.mensaje,
        "nivel_entrada": sesion["nivel"],
        "motivo": sesion.get("motivo_escalado", ""),
        "pasos": [],
    }
    try:
        resultado = RECURSOS["grafo"].invoke(estado_inicial)
    except Exception as exc:
        logger.exception("Error procesando la consulta")
        raise HTTPException(
            status_code=503,
            detail=(
                "No se ha podido completar la consulta. Comprueba Ollama, "
                f"{config.LLM_MODEL} y {config.EMBEDDING_MODEL}."
            ),
        ) from exc

    nivel_sesion = {"N1": 1, "N2": 2, "Humano": 3}.get(
        resultado["nivel"], sesion["nivel"]
    )
    sessions.fijar_nivel(
        session_id,
        nivel_sesion,
        resultado.get("motivo", ""),
    )
    sessions.registrar_turno(
        session_id,
        req.mensaje,
        resultado["respuesta"],
        resultado["nivel"],
        req.feedback,
    )

    return ChatResponse(
        session_id=session_id,
        nivel=resultado["nivel"],
        respuesta=resultado["respuesta"],
        destino=resultado.get("destino", "fin"),
        escalado=resultado.get("escalado", False),
        motivo=resultado.get("motivo", ""),
        pasos=resultado.get("pasos", []),
        fuentes=resultado.get("fuentes", []),
        confianza_n1=resultado.get("confianza_n1", 0.0),
        confianza_n2=resultado.get("confianza_n2", 0.0),
    )


@app.post(
    "/session/{session_id}/finalizar",
    response_model=FinalizarResponse,
)
def finalizar(session_id: str):
    sesion = sessions.finalizar(session_id)
    if sesion is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return FinalizarResponse(
        session_id=session_id,
        mensaje="Sesión finalizada. Gracias por usar el soporte.",
        turnos=len(sesion["historial"]),
    )


@app.get("/session/{session_id}")
def estado_sesion(session_id: str):
    sesion = sessions.get_sesion(session_id)
    if sesion is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return sesion
