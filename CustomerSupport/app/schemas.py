"""Modelos Pydantic compartidos por FastAPI y Streamlit."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


EstadoPaso = Literal["pendiente", "completado", "escalado", "omitido", "final"]
TipoPaso = Literal["entrada", "rag", "agente", "clasificador", "humano", "fin"]
NivelSoporte = Literal["Entrada", "Recepción", "N1", "N2", "Humano"]


class PasoRecorrido(BaseModel):
    id: str
    nombre: str
    tipo: TipoPaso
    estado: EstadoPaso
    detalle: str
    fuentes: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    mensaje: str = Field(min_length=1)
    session_id: str | None = None
    feedback: Literal["satisfecho", "insatisfecho"] | None = None


class ChatResponse(BaseModel):
    session_id: str
    nivel: NivelSoporte
    respuesta: str
    destino: Literal["fin", "n2", "humano"]
    escalado: bool
    motivo: str
    pasos: list[PasoRecorrido] = Field(default_factory=list)
    fuentes: list[str] = Field(default_factory=list)
    confianza_n1: float = 0.0
    confianza_n2: float = 0.0


class FinalizarResponse(BaseModel):
    session_id: str
    mensaje: str
    turnos: int


class HealthResponse(BaseModel):
    status: str
    modelo_llm: str
    modelo_embeddings: str
    fragmentos_faq_n1: int
    fragmentos_manual_n2: int
