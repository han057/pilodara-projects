import asyncio
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from api.chat_schema import ChatRequest
from api.deps.session_manager import SessionManager
from agents.utils import format_history, ThinkingStreamFilter
from config import OLLAMA_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)
router = APIRouter()

_executor = ThreadPoolExecutor(max_workers=4)

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


# ─── Helpers de extracción ────────────────────────────────────────────────────

def _extract_destination(message: str) -> str | None:
    stop_words = {"para", "por", "durante", "en", "de", "con", "desde",
                  "hasta", "un", "una", "el", "la", "los", "las", "del"}
    patrones = [
        r"(?:viajar\s+a|visit(?:ar)?\s+|ir\s+a|destino\s+|viaje\s+a)\s*(.+?)(?=\s+(?:para|por|durante|de|con|desde|hasta)\s|\s*\d|\Z)",
        r"\b(?:a|hacia)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñA-ZÁÉÍÓÚÑ\s]{2,30})(?=\s+(?:para|por|durante|en|\d)|\Z)",
    ]
    for pat in patrones:
        match = re.search(pat, message, re.IGNORECASE)
        if match:
            raw = match.group(1).strip()
            parts = raw.split()
            filtered = [p for p in parts if p.lower() not in stop_words]
            if filtered:
                return " ".join(filtered[:3]).title()

    words = message.split()
    question_words = {"qué", "que", "quien", "quienes", "cual", "cuales",
                      "como", "cómo", "donde", "dónde", "cuando", "cuándo",
                      "dame", "necesito", "quiero", "busco", "información",
                      "tengo", "hay", "puedo", "debo", "vale", "hola"}
    capitalized = [
        w.strip(",.!?¿¡:;") for w in words
        if w.strip(",.!?¿¡:;")[:1].isupper()
        and w.strip(",.!?¿¡:;").lower() not in stop_words | question_words
        and not w.strip(",.!?¿¡:;").isdigit()
    ]
    if capitalized:
        return " ".join(capitalized[:3])

    return None


def _extract_days(message: str) -> int:
    match = re.search(r"(\d+)\s*(?:d[ií]as?|semanas?)", message, re.IGNORECASE)
    if match:
        val = int(match.group(1))
        if "semana" in match.group(0).lower():
            val *= 7
        return max(1, min(val, 30))
    return 3


def _is_trip_request(message: str) -> bool:
    trip_keywords = [
        r"viajar\s+a", r"ir\s+a", r"visitar\s+", r"viaje\s+a",
        r"\d+\s*d[ií]as?", r"semanas?\s+en", r"planif",
        r"itinerario", r"quiero\s+ir", r"quiero\s+viajar",
    ]
    msg_lower = message.lower()
    return any(re.search(kw, msg_lower) for kw in trip_keywords)


_DESTINOS_FUERA_ESPANA = {
    "paris", "parís", "roma", "rome", "london", "londres",
    "tokio", "tokyo", "nueva york", "new york", "berlin", "berlín",
    "amsterdam", "dubai", "bangkok", "sydney", "buenos aires",
    "ciudad de mexico", "ciudad de méxico", "mexico", "méxico",
    "miami", "los angeles", "chicago", "toronto", "moscu", "moscú",
    "beijing", "pekín", "pekin", "shanghai", "hong kong",
    "singapur", "singapore", "cairo", "el cairo", "nairobi",
    "marrakech", "marrakesh", "lisboa", "lisbon", "oporto", "porto",
    "niza", "nice", "venecia", "venice", "florencia", "florence",
    "milan", "milán", "napoles", "nápoles", "naples",
    "viena", "vienna", "praga", "prague", "budapest",
    "varsovia", "warsaw", "estocolmo", "stockholm", "oslo",
    "copenhague", "copenhagen", "helsinki", "dublin", "edimburgo",
    "edinburgh", "atenas", "athens", "estambul", "istanbul",
    "rio de janeiro", "río de janeiro", "sao paulo", "são paulo",
    "bogota", "bogotá", "lima", "santiago", "caracas",
    "nueva delhi", "new delhi", "mumbai", "bombay",
    "kuala lumpur", "jakarta", "manila", "seul", "seúl", "seoul",
    "japon", "japón", "china", "india", "brasil", "brazil",
    "argentina", "colombia", "chile", "peru", "perú",
    "marruecos", "morocco", "egipto", "egypt",
    "tailandia", "thailand", "indonesia", "vietnam",
    "estados unidos", "usa", "reino unido", "uk",
    "alemania", "germany", "francia", "france",
    "italia", "italy", "portugal", "holanda", "netherlands",
    "belgica", "bélgica", "belgium", "suiza", "switzerland", "austria",
    "grecia", "greece", "turquia", "turquía", "turkey",
    "canada", "australia", "nueva zelanda", "new zealand",
    "sudafrica", "sudáfrica", "south africa", "nigeria", "kenya",
}


def _es_destino_espanol(destination: str) -> bool:
    return destination.lower().strip() not in _DESTINOS_FUERA_ESPANA


# ─── Funciones de contexto (síncronas, corren en thread pool) ────────────────

def _run_rag(destino: str) -> dict:
    try:
        from agents.rag_agent import RAGAgent
        result = RAGAgent().run({"destination_city": destino})
        return result.get("rag_data", {})
    except Exception:
        logger.warning("RAG no disponible para '%s'", destino)
        return {}


def _run_attractions(destino: str) -> list:
    try:
        from graph.nodes import fetch_attractions_node
        result = fetch_attractions_node({
            "destination_city": destino,
            "attractions_limit": 9,
        })
        return result.get("attractions", [])
    except Exception:
        logger.warning("Atracciones no disponibles para '%s'", destino)
        return []


def _build_rag_context(rag_data: dict) -> str:
    parts = []
    if rag_data.get("weather"):
        parts.append(f"Clima: {rag_data['weather'][:150]}")
    if rag_data.get("transport"):
        parts.append(f"Transporte: {rag_data['transport'][:150]}")
    if rag_data.get("tips"):
        parts.append(f"Consejos: {'; '.join(rag_data['tips'][:2])}")
    if rag_data.get("neighborhoods"):
        parts.append(f"Barrios: {'; '.join(rag_data['neighborhoods'][:2])}")
    return "\n".join(parts) if parts else "Usa tu conocimiento general del destino."


def _build_attractions_text(attractions: list) -> str:
    if not attractions:
        return "Sin atracciones específicas — usa tu conocimiento del destino."
    lines = [
        f"- {a.get('name', a.get('nombre', str(a)))}"
        for a in attractions[:6]
        if isinstance(a, dict) and (a.get("name") or a.get("nombre"))
    ]
    return "\n".join(lines) if lines else "Usa tu conocimiento del destino."


def _make_llm(temperature: float = 0.65, timeout: int = 120) -> ChatOllama:
    return ChatOllama(
        model=OLLAMA_MODEL,
        temperature=temperature,
        num_predict=-1,
        base_url=OLLAMA_URL,
        client_kwargs={"timeout": timeout},
    )


# ─── Generadores SSE ──────────────────────────────────────────────────────────

async def _stream_trip(session_id: str, destino: str, dias: int, history: list):
    """Streaming real: curiosidades visibles durante el thinking, tokens reales después."""
    loop = asyncio.get_running_loop()

    # Fase 1: RAG + Attractions en paralelo
    try:
        rag_data, attractions = await asyncio.gather(
            loop.run_in_executor(_executor, _run_rag, destino),
            loop.run_in_executor(_executor, _run_attractions, destino),
        )
    except Exception:
        logger.warning("Error obteniendo contexto para '%s'", destino)
        rag_data, attractions = {}, []

    rag_context = _build_rag_context(rag_data)
    attractions_text = _build_attractions_text(attractions)
    history_section = format_history(history, max_turns=2)
    max_words = 200 + dias * 180

    with open("prompts/unified_itinerary.txt", "r", encoding="utf-8") as f:
        prompt_text = f.read()

    llm = _make_llm(timeout=180)
    chain = ChatPromptTemplate.from_template(prompt_text) | llm

    # Fase 2: Generar respuesta completa — las curiosidades permanecen visibles mientras el modelo trabaja
    try:
        response = await chain.ainvoke({
            "destination": destino,
            "days": dias,
            "rag_context": rag_context,
            "attractions_text": attractions_text,
            "history_section": history_section,
            "max_words": max_words,
        })
        from agents.utils import strip_thinking
        body = strip_thinking(response.content).strip()
    except Exception:
        logger.exception("Error generando itinerario para '%s'", destino)
        body = "No se pudo generar el itinerario. Por favor, inténtalo de nuevo."

    # Fase 3: Streaming palabra a palabra (~20 palabras/s) para dar sensación natural
    header = f"## {destino} — {dias} {'día' if dias == 1 else 'días'}\n\n"
    full_text = header + body

    yield f"data: {json.dumps({'token': header})}\n\n"
    for word in body.split(" "):
        yield f"data: {json.dumps({'token': word + ' '})}\n\n"
        await asyncio.sleep(0.05)

    yield "data: [DONE]\n\n"
    SessionManager.append_message(session_id, "bot", full_text)


async def _stream_conversational(session_id: str, user_message: str, history: list):
    """Respuesta conversacional de Marco en streaming."""
    try:
        with open("prompts/conversational.txt", "r", encoding="utf-8") as f:
            prompt_text = f.read()
    except Exception:
        fallback = "¡Hola! Soy Marco, tu consultor de viajes por España. ¿A qué destino quieres ir?"
        yield f"data: {json.dumps({'token': fallback})}\n\n"
        yield "data: [DONE]\n\n"
        SessionManager.append_message(session_id, "bot", fallback)
        return

    history_text = format_history(history, max_turns=3)
    llm = _make_llm(temperature=0.7, timeout=90)
    chain = ChatPromptTemplate.from_template(prompt_text) | llm

    full_text = ""
    tf = ThinkingStreamFilter()
    try:
        async for chunk in chain.astream({
            "user_message": user_message,
            "history_section": history_text,
        }):
            text = tf.feed(chunk.content)
            if text:
                full_text += text
                yield f"data: {json.dumps({'token': text})}\n\n"

        remaining = tf.flush()
        if remaining:
            full_text += remaining
            yield f"data: {json.dumps({'token': remaining})}\n\n"

    except Exception:
        logger.exception("Error en stream conversacional")
        fallback = "¡Hola! Soy Marco. ¿A qué destino español te gustaría viajar?"
        full_text = fallback
        yield f"data: {json.dumps({'token': fallback})}\n\n"

    yield "data: [DONE]\n\n"
    SessionManager.append_message(session_id, "bot", full_text)


async def _stream_rejection(session_id: str, destino: str):
    msg = (
        f"Lo siento, solo puedo ayudarte a planificar viajes por **España**. "
        f"{destino} queda fuera de mi área de especialización. "
        f"¿Te animas a descubrir algún destino español? Puedo prepararte un itinerario "
        f"para Madrid, Barcelona, Sevilla, Granada, Valencia, San Sebastián y muchos más."
    )
    yield f"data: {json.dumps({'token': msg})}\n\n"
    yield "data: [DONE]\n\n"
    SessionManager.append_message(session_id, "bot", msg)


# ─── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/{session_id}")
async def chat(session_id: str, request: ChatRequest):
    if not SessionManager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    SessionManager.append_message(session_id, "user", request.message)
    history = SessionManager.get_history(session_id)

    destino = _extract_destination(request.message)
    dias = _extract_days(request.message)
    is_trip = _is_trip_request(request.message)

    if destino and is_trip and not _es_destino_espanol(destino):
        generator = _stream_rejection(session_id, destino)
    elif destino and is_trip:
        generator = _stream_trip(session_id, destino, dias, history[:-1])
    else:
        generator = _stream_conversational(session_id, request.message, history[:-1])

    return StreamingResponse(generator, media_type="text/event-stream", headers=_SSE_HEADERS)
