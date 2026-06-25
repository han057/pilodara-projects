"""Grafo LangGraph completo para N1, N2 y soporte humano.

Flujo normal:

START -> Entrada LLM -> Clasificador de intención
                         | conversación general -> Recepción (Nivel 0) -> END
                         | consulta sobre router
                         v
                      RAG N1 -> Soporte N1 -> Clasificador N1
                                      | escalar
                                      v
                         RAG N2 -> Soporte N2 -> Clasificador N2
                                                        | escalar
                                                        v
                                              Asistente humano -> END

Los intentos solicitados por el usuario pueden entrar directamente en N2 o en
soporte humano, pero siempre atraviesan el mismo grafo compilado.
"""

from __future__ import annotations

import logging
from typing import Any, Literal, TypedDict

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph

from . import config
from .indexing import (
    buscar_n1,
    buscar_n2,
    coincidencias_utiles,
    fuentes_resumidas,
)


logger = logging.getLogger("proyecto_base.graph")

MARCA_ESCALAR_N2 = "ESCALAR_N2"
MARCA_ESCALAR_HUMANO = "ESCALAR_HUMANO"


class EstadoSoporte(TypedDict, total=False):
    pregunta: str
    nivel_entrada: int
    contexto_n1: list[tuple[Document, float]]
    contexto_n2: list[tuple[Document, float]]
    respuesta: str
    es_router: bool
    intencion: Literal["ROUTER", "SOCIAL", "FUERA_TEMA"]
    nivel: Literal["Entrada", "Recepción", "N1", "N2", "Humano"]
    destino: Literal["fin", "n2", "humano"]
    escalado: bool
    motivo: str
    pasos: list[dict[str, Any]]
    fuentes: list[str]
    confianza_n1: float
    confianza_n2: float


llm = ChatOllama(
    model=config.LLM_MODEL,
    base_url=config.OLLAMA_BASE_URL,
    temperature=config.TEMPERATURE,
    num_predict=700,
)

prompt_clasificador = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Clasifica el mensaje del cliente en una sola categoría:

- ROUTER: contiene una consulta, problema o petición relacionada con el Router
  Smart WiFi 6, la conexión, Internet, WiFi, instalación o configuración.
- SOCIAL: saludos, presentaciones, agradecimientos o despedidas sin una consulta.
- FUERA_TEMA: preguntas o conversación sobre cualquier asunto que no sea el
  Router Smart WiFi 6, por ejemplo clima, recetas, deportes, viajes o noticias.

Responde EXACTAMENTE con ROUTER, SOCIAL o FUERA_TEMA. No añadas explicaciones.""",
        ),
        ("human", "Mensaje del cliente: {pregunta}\n\nCategoría:"),
    ]
)

prompt_nivel1 = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Eres Soporte N1 del Router Smart WiFi 6 de Movistar.
Responde ÚNICAMENTE con la información de las preguntas frecuentes incluidas en
el contexto. No uses conocimientos propios, no completes datos y no cites las
fuentes al cliente.

Omite siempre los metadatos internos de la FAQ: dificultad, tiempo estimado,
necesidad de soporte o técnico y estado documental. No los menciones ni los
resumas en la respuesta.

Si el contexto no contiene una respuesta explícita y suficiente, responde
EXACTAMENTE con {marca}. Si responde, hazlo en español de España, de forma clara
y breve.""",
        ),
        (
            "human",
            "CONTEXTO FAQ:\n{contexto}\n\nPREGUNTA:\n{pregunta}\n\nRESPUESTA:",
        ),
    ]
)

prompt_nivel2 = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Eres Soporte N2 del Router Smart WiFi 6 de Movistar.
Responde ÚNICAMENTE con la información del manual técnico incluido en el
contexto. No uses conocimientos propios, no inventes menús o características y
no cites las fuentes al cliente.

Si el manual no contiene una respuesta explícita y suficiente, responde
EXACTAMENTE con {marca}. Si responde, explica los pasos con claridad y avisa si
alguna acción puede interrumpir la conexión.""",
        ),
        (
            "human",
            "CONTEXTO DEL MANUAL:\n{contexto}\n\nPREGUNTA:\n{pregunta}\n\nRESPUESTA:",
        ),
    ]
)


def entrada_llm_node(state: EstadoSoporte) -> dict[str, Any]:
    paso = _paso(
        "entrada_llm",
        "Entrada LLM",
        "entrada",
        "completado",
        "La consulta entra al flujo de soporte.",
    )
    return {
        "pregunta": state["pregunta"].strip(),
        "pasos": [paso],
        "respuesta": "",
        "nivel": "Entrada",
        "destino": "fin",
        "escalado": False,
        "fuentes": [],
        "confianza_n1": 0.0,
        "confianza_n2": 0.0,
    }


def clasificador_entrada_node(state: EstadoSoporte) -> dict[str, Any]:
    pregunta = state["pregunta"]
    if _es_conversacion_cordial(pregunta):
        etiqueta = "SOCIAL"
    else:
        chain = prompt_clasificador | llm
        etiqueta = _contenido(chain.invoke({"pregunta": pregunta})).upper()
    if etiqueta not in {"ROUTER", "SOCIAL", "FUERA_TEMA"}:
        etiqueta = "FUERA_TEMA"
    es_router = etiqueta.startswith("ROUTER")
    return {
        "es_router": es_router,
        "intencion": etiqueta,
        "pasos": state["pasos"]
        + [
            _paso(
                "clasificador_entrada",
                "Clasificador de intención",
                "clasificador",
                "completado",
                (
                    "El mensaje contiene una consulta sobre el router."
                    if es_router
                    else (
                        "El mensaje corresponde a conversación cordial."
                        if etiqueta == "SOCIAL"
                        else "El mensaje no está relacionado con el router."
                    )
                ),
            )
        ],
    }


def decidir_tema(state: EstadoSoporte) -> str:
    if not state.get("es_router"):
        return "recepcion"
    nivel = int(state.get("nivel_entrada", 1))
    if nivel >= 3:
        return "humano"
    if nivel == 2:
        return "rag_n2"
    return "rag_n1"


def recepcion_node(state: EstadoSoporte) -> dict[str, Any]:
    intencion = state.get("intencion", "FUERA_TEMA")
    respuesta = _respuesta_recepcion(state["pregunta"], intencion)
    return {
        "respuesta": respuesta,
        "nivel": "Recepción",
        "destino": "fin",
        "escalado": False,
        "motivo": (
            "Conversación cordial"
            if intencion == "SOCIAL"
            else "Consulta fuera de temática"
        ),
        "fuentes": [],
        "pasos": state["pasos"]
        + [
            _paso(
                "recepcion",
                "Recepción",
                "agente",
                "final",
                (
                    "Recepción atiende el mensaje cordial sin consultar el RAG."
                    if intencion == "SOCIAL"
                    else "Recepción reconduce la conversación hacia el soporte del router."
                ),
            )
        ],
    }


def rag_n1_node(state: EstadoSoporte) -> dict[str, Any]:
    resultados = buscar_n1(state["pregunta"])
    confianza = resultados[0][1] if resultados else 0.0
    suficiente = _contexto_suficiente(
        state["pregunta"],
        resultados,
        config.N1_MIN_RELEVANCE,
    )
    return {
        "contexto_n1": resultados,
        "confianza_n1": confianza,
        "pasos": state["pasos"]
        + [
            _paso(
                "rag_n1",
                "RAG N1",
                "rag",
                "completado" if suficiente else "escalado",
                _detalle_rag(resultados, config.N1_MIN_RELEVANCE),
                fuentes_resumidas(resultados),
            )
        ],
    }


def soporte_n1_node(state: EstadoSoporte) -> dict[str, Any]:
    resultados = state.get("contexto_n1", [])
    suficiente = _contexto_suficiente(
        state["pregunta"],
        resultados,
        config.N1_MIN_RELEVANCE,
    )
    respuesta = MARCA_ESCALAR_N2
    if suficiente:
        chain = prompt_nivel1 | llm
        respuesta = _contenido(
            chain.invoke(
                {
                    "contexto": _contexto_texto(resultados),
                    "pregunta": state["pregunta"],
                    "marca": MARCA_ESCALAR_N2,
                }
            )
        )
        respuesta = _limpiar_metadatos_respuesta(respuesta)
        if not respuesta:
            respuesta = MARCA_ESCALAR_N2
    escala = _empieza_por(respuesta, MARCA_ESCALAR_N2)
    return {
        "respuesta": respuesta,
        "nivel": "N1",
        "pasos": state["pasos"]
        + [
            _paso(
                "soporte_n1",
                "Soporte N1",
                "agente",
                "escalado" if escala else "completado",
                (
                    "N1 no tiene una respuesta segura en las preguntas frecuentes."
                    if escala
                    else "N1 prepara una respuesta usando solo las preguntas frecuentes."
                ),
                fuentes_resumidas(resultados),
            )
        ],
    }


def clasificador_n1_node(state: EstadoSoporte) -> dict[str, Any]:
    escala = _empieza_por(state.get("respuesta", ""), MARCA_ESCALAR_N2)
    return {
        "destino": "n2" if escala else "fin",
        "escalado": escala,
        "motivo": (
            "La FAQ no contiene una respuesta suficiente"
            if escala
            else "FAQ suficiente"
        ),
        "fuentes": fuentes_resumidas(state.get("contexto_n1", [])),
        "pasos": state["pasos"]
        + [
            _paso(
                "clasificador_n1",
                "Clasificador N1",
                "clasificador",
                "escalado" if escala else "final",
                (
                    "La consulta necesita una revisión técnica en N2."
                    if escala
                    else "La respuesta de N1 es suficiente."
                ),
            )
        ],
    }


def decidir_tras_n1(state: EstadoSoporte) -> str:
    return "rag_n2" if state.get("destino") == "n2" else END


def rag_n2_node(state: EstadoSoporte) -> dict[str, Any]:
    resultados = buscar_n2(state["pregunta"])
    confianza = resultados[0][1] if resultados else 0.0
    suficiente = _contexto_suficiente(
        state["pregunta"],
        resultados,
        config.N2_MIN_RELEVANCE,
    )
    return {
        "contexto_n2": resultados,
        "confianza_n2": confianza,
        "pasos": state["pasos"]
        + [
            _paso(
                "rag_n2",
                "RAG N2",
                "rag",
                "completado" if suficiente else "escalado",
                _detalle_rag(resultados, config.N2_MIN_RELEVANCE),
                fuentes_resumidas(resultados),
            )
        ],
    }


def soporte_n2_node(state: EstadoSoporte) -> dict[str, Any]:
    resultados = state.get("contexto_n2", [])
    suficiente = _contexto_suficiente(
        state["pregunta"],
        resultados,
        config.N2_MIN_RELEVANCE,
    )
    respuesta = MARCA_ESCALAR_HUMANO
    if suficiente:
        chain = prompt_nivel2 | llm
        respuesta = _contenido(
            chain.invoke(
                {
                    "contexto": _contexto_texto(resultados),
                    "pregunta": state["pregunta"],
                    "marca": MARCA_ESCALAR_HUMANO,
                }
            )
        )
    escala = _empieza_por(
        respuesta, MARCA_ESCALAR_HUMANO
    ) or _respuesta_sin_informacion(respuesta)
    if escala:
        respuesta = MARCA_ESCALAR_HUMANO
    return {
        "respuesta": respuesta,
        "nivel": "N2",
        "escalado": escala,
        "pasos": state["pasos"]
        + [
            _paso(
                "soporte_n2",
                "Soporte N2",
                "agente",
                "escalado" if escala else "completado",
                (
                    "N2 no localiza una respuesta segura en el manual."
                    if escala
                    else "N2 prepara una respuesta usando solo el manual técnico."
                ),
                fuentes_resumidas(resultados),
            )
        ],
    }


def clasificador_n2_node(state: EstadoSoporte) -> dict[str, Any]:
    escala = _empieza_por(state.get("respuesta", ""), MARCA_ESCALAR_HUMANO)
    return {
        "destino": "humano" if escala else "fin",
        "motivo": (
            "El manual no contiene una respuesta suficiente"
            if escala
            else "Manual tecnico suficiente"
        ),
        "fuentes": fuentes_resumidas(state.get("contexto_n2", [])),
        "pasos": state["pasos"]
        + [
            _paso(
                "clasificador_n2",
                "Clasificador N2",
                "clasificador",
                "escalado" if escala else "final",
                (
                    "La consulta necesita atención humana."
                    if escala
                    else "La respuesta tecnica es suficiente."
                ),
            )
        ],
    }


def decidir_tras_n2(state: EstadoSoporte) -> str:
    return "humano" if state.get("destino") == "humano" else END


def humano_node(state: EstadoSoporte) -> dict[str, Any]:
    respuesta = (
        "No dispongo de información suficiente para responder con seguridad a "
        "tu consulta. Para ayudarte correctamente, voy a derivarla a nuestro "
        "servicio técnico.\n\n"
        f"**Teléfono:** {config.HUMAN_PHONE}  \n"
        f"**Correo electrónico:** {config.HUMAN_EMAIL}"
    )
    return {
        "respuesta": respuesta,
        "nivel": "Humano",
        "destino": "humano",
        "escalado": True,
        "motivo": state.get("motivo") or "Atención humana solicitada",
        "fuentes": [],
        "pasos": state["pasos"]
        + [
            _paso(
                "humano",
                "Asistente Humano",
                "humano",
                "final",
                f"Teléfono {config.HUMAN_PHONE} - {config.HUMAN_EMAIL}",
            )
        ],
    }


def construir_grafo():
    builder = StateGraph(EstadoSoporte)
    builder.add_node("entrada_llm", entrada_llm_node)
    builder.add_node("clasificador_entrada", clasificador_entrada_node)
    builder.add_node("recepcion", recepcion_node)
    builder.add_node("rag_n1", rag_n1_node)
    builder.add_node("soporte_n1", soporte_n1_node)
    builder.add_node("clasificador_n1", clasificador_n1_node)
    builder.add_node("rag_n2", rag_n2_node)
    builder.add_node("soporte_n2", soporte_n2_node)
    builder.add_node("clasificador_n2", clasificador_n2_node)
    builder.add_node("humano", humano_node)

    builder.add_edge(START, "entrada_llm")
    builder.add_edge("entrada_llm", "clasificador_entrada")
    builder.add_conditional_edges(
        "clasificador_entrada",
        decidir_tema,
        {
            "recepcion": "recepcion",
            "rag_n1": "rag_n1",
            "rag_n2": "rag_n2",
            "humano": "humano",
        },
    )
    builder.add_edge("recepcion", END)
    builder.add_edge("rag_n1", "soporte_n1")
    builder.add_edge("soporte_n1", "clasificador_n1")
    builder.add_conditional_edges(
        "clasificador_n1",
        decidir_tras_n1,
        {"rag_n2": "rag_n2", END: END},
    )
    builder.add_edge("rag_n2", "soporte_n2")
    builder.add_edge("soporte_n2", "clasificador_n2")
    builder.add_conditional_edges(
        "clasificador_n2",
        decidir_tras_n2,
        {"humano": "humano", END: END},
    )
    builder.add_edge("humano", END)
    return builder.compile()


def _contexto_suficiente(
    pregunta: str,
    resultados: list[tuple[Document, float]],
    umbral: float,
) -> bool:
    if not resultados or resultados[0][1] < umbral:
        return False
    documentos = [documento for documento, _ in resultados[:3]]
    return bool(coincidencias_utiles(pregunta, documentos))


def _contexto_texto(resultados: list[tuple[Document, float]]) -> str:
    bloques: list[str] = []
    for posicion, (documento, _) in enumerate(resultados, start=1):
        pagina = int(documento.metadata.get("page", 0)) + 1
        bloques.append(
            f"[Fragmento {posicion}, pagina {pagina}]\n{documento.page_content}"
        )
    return "\n\n---\n\n".join(bloques)


def _detalle_rag(
    resultados: list[tuple[Document, float]], umbral: float
) -> str:
    if not resultados:
        return "No se han recuperado fragmentos relevantes."
    return (
        f"Se recuperan {len(resultados)} fragmentos. "
        f"Mejor relevancia: {resultados[0][1]:.2f}. Umbral: {umbral:.2f}."
    )


def _paso(
    paso_id: str,
    nombre: str,
    tipo: str,
    estado: str,
    detalle: str,
    fuentes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": paso_id,
        "nombre": nombre,
        "tipo": tipo,
        "estado": estado,
        "detalle": detalle,
        "fuentes": fuentes or [],
    }


def _contenido(respuesta: Any) -> str:
    contenido = respuesta.content
    if isinstance(contenido, str):
        return contenido.strip()
    return str(contenido).strip()


def _empieza_por(respuesta: str, marca: str) -> bool:
    return respuesta.strip().upper().startswith(marca)


def _limpiar_metadatos_respuesta(respuesta: str) -> str:
    """Elimina campos editoriales de la FAQ antes de responder al cliente."""
    normalizada = respuesta.casefold()
    marcadores = (
        "dificultad:",
        "tiempo estimado:",
        "soporte/técnico:",
        "soporte / técnico:",
        "soporte/técnico :",
        "estado documental:",
    )
    posiciones = [
        normalizada.find(marcador)
        for marcador in marcadores
        if normalizada.find(marcador) >= 0
    ]
    if posiciones:
        respuesta = respuesta[: min(posiciones)]
    return respuesta.rstrip(" \n\t.;,:-")


def _respuesta_sin_informacion(respuesta: str) -> bool:
    """Detecta negativas del modelo aunque no respete el marcador exacto."""
    normalizada = respuesta.casefold()
    expresiones = (
        "no proporciona información",
        "no proporciona informacion",
        "no contiene información",
        "no contiene informacion",
        "no dispongo de información",
        "no dispongo de informacion",
        "no hay información",
        "no hay informacion",
        "no se especifica",
        "no está especificado",
        "no esta especificado",
        "no puedo responder",
    )
    return any(expresion in normalizada for expresion in expresiones)


def _es_conversacion_cordial(pregunta: str) -> bool:
    """Evita llamar al LLM para mensajes sociales inequívocos."""
    normalizada = " ".join(
        pregunta.casefold()
        .replace("¿", "")
        .replace("?", "")
        .replace("¡", "")
        .replace("!", "")
        .split()
    )
    mensajes = {
        "hola",
        "buenas",
        "buenos días",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "qué tal",
        "que tal",
        "gracias",
        "muchas gracias",
        "de acuerdo gracias",
        "vale gracias",
        "adiós",
        "adios",
        "hasta luego",
        "nos vemos",
    }
    return normalizada in mensajes


def _respuesta_recepcion(
    pregunta: str, intencion: Literal["SOCIAL", "FUERA_TEMA"]
) -> str:
    """Respuestas cerradas para impedir conversación ajena al router."""
    normalizada = " ".join(
        pregunta.casefold()
        .replace("¿", "")
        .replace("?", "")
        .replace("¡", "")
        .replace("!", "")
        .split()
    )
    if intencion == "FUERA_TEMA":
        return (
            "Lo siento, este servicio solo puede ayudarte con consultas "
            "relacionadas con el Router Smart WiFi 6. Puedes preguntarme sobre "
            "su instalación, la conexión WiFi o la configuración del router."
        )
    if normalizada in {
        "gracias",
        "muchas gracias",
        "de acuerdo gracias",
        "vale gracias",
    }:
        return (
            "Gracias a ti. Cuando lo necesites, puedo ayudarte con cualquier "
            "consulta sobre el Router Smart WiFi 6."
        )
    if normalizada in {"adiós", "adios", "hasta luego", "nos vemos"}:
        return (
            "Hasta luego. Estaremos disponibles para ayudarte con tu Router "
            "Smart WiFi 6."
        )
    return (
        "Hola, bienvenido al soporte del Router Smart WiFi 6. Cuéntame qué "
        "necesitas saber sobre su instalación, conexión WiFi o configuración."
    )
