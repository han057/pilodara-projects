import logging

from langgraph.graph import StateGraph, START, END
from graph.state import TravelState

logger = logging.getLogger(__name__)


def _get_agents():
    from agents.planner_agent import PlannerAgent
    from agents.rag_agent import RAGAgent
    return PlannerAgent(), RAGAgent().run


def _get_nodes():
    from graph.nodes import fetch_attractions_node
    return fetch_attractions_node,


def _synthesize_rag_context(rag_data: dict) -> str:
    parts = []
    if rag_data.get("weather"):
        parts.append(f"Clima: {rag_data['weather']}")
    if rag_data.get("transport"):
        parts.append(f"Transporte: {rag_data['transport']}")
    if rag_data.get("tips"):
        parts.append(f"Consejos: {'; '.join(rag_data['tips'][:3])}")
    if rag_data.get("events"):
        parts.append(f"Eventos: {'; '.join(rag_data['events'][:3])}")
    if rag_data.get("neighborhoods"):
        parts.append(f"Barrios: {'; '.join(rag_data['neighborhoods'][:3])}")
    return "\n".join(parts) if parts else ""


def _build_graph():
    planner, rag_runner = _get_agents()
    fetch_attractions = _get_nodes()[0]

    def rag_node(state: TravelState):
        logger.info("Consultando RAG para '%s'", state["destination"])
        try:
            enriched = rag_runner({"destination_city": state["destination"]})
            return {"rag_data": enriched.get("rag_data", {})}
        except Exception:
            logger.warning("RAG no disponible, continuando sin contexto")
            return {"rag_data": {}}

    def plan_node(state: TravelState):
        logger.info("Planificando viaje a '%s'", state["destination"])
        context = _synthesize_rag_context(state.get("rag_data", {}))
        respuesta = planner.plan_trip(
            destination=state["destination"],
            days=state["days"],
            context=context,
            conversation_history=state.get("conversation_history", []),
        )
        return {"planner_summary": respuesta["summary"]}

    def attractions_node(state: TravelState):
        logger.info("Buscando atracciones para '%s'", state["destination"])
        try:
            result = fetch_attractions({
                "destination_city": state["destination"],
                "attractions_limit": 9,
            })
            return {"attractions": result.get("attractions", [])}
        except Exception:
            logger.warning("No se pudieron obtener atracciones para '%s'", state["destination"])
            return {"attractions": []}

    def itinerary_node(state: TravelState):
        logger.info("Generando itinerario con IA para '%s'", state["destination"])
        destino = state["destination"]
        dias = state["days"]
        try:
            from agents.itinerary_agent import ItineraryAgent
            agent = ItineraryAgent()
            result = agent.build_itinerary(
                destination=destino,
                days=dias,
                planner_summary=state.get("planner_summary", ""),
                attractions=state.get("attractions", []),
                rag_data=state.get("rag_data", {}),
            )
            return {
                "itinerary": {
                    "summary": state.get("planner_summary", f"Plan de {dias} días en {destino}"),
                    "days": result.get("itinerary", []),
                    "attractions": state.get("attractions", []),
                }
            }
        except Exception:
            logger.exception("ItineraryAgent falló para '%s'", destino)
            return {
                "itinerary": {
                    "summary": f"Plan de {dias} días en {destino}",
                    "days": [
                        {
                            "title": f"Día {i+1} en {destino}",
                            "description": f"Exploración del día {i+1} en {destino}.",
                            "suggested_activities": [],
                        }
                        for i in range(dias)
                    ],
                    "attractions": [],
                }
            }

    builder = StateGraph(TravelState)
    builder.add_node("rag", rag_node)
    builder.add_node("planner", plan_node)
    builder.add_node("attractions", attractions_node)
    builder.add_node("itinerary", itinerary_node)

    builder.add_edge(START, "rag")
    builder.add_edge("rag", "planner")
    builder.add_edge("planner", "attractions")
    builder.add_edge("attractions", "itinerary")
    builder.add_edge("itinerary", END)

    return builder.compile()


_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = _build_graph()
    return _graph


def ejecutar_viaje(destino: str, dias: int, conversation_history: list | None = None) -> dict:
    try:
        graph = _get_graph()
        estado_inicial = {
            "destination": destino,
            "destination_city": destino,
            "days": dias,
            "conversation_history": conversation_history or [],
            "user_message": "",
        }
        resultado = graph.invoke(estado_inicial)
        itinerary = resultado.get("itinerary", {})
        return {
            "destino": destino,
            "dias": dias,
            "mensaje_motivacional": resultado.get("planner_summary") or f"Plan de {dias} días en {destino}.",
            "opciones_busqueda": resultado.get("attractions", []),
            "itinerario": itinerary,
        }
    except Exception:
        logger.exception("ejecutar_viaje falló para destino='%s'", destino)
        return {
            "destino": destino,
            "dias": dias,
            "mensaje_motivacional": f"Plan de {dias} días en {destino}.",
            "opciones_busqueda": [],
            "itinerario": {
                "summary": f"Plan de {dias} días en {destino}",
                "days": [
                    {"title": f"Día {i+1}", "description": f"Exploración en {destino}", "suggested_activities": []}
                    for i in range(dias)
                ],
            },
        }
