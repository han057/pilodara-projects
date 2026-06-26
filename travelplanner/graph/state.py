from typing import TypedDict, List


class TravelState(TypedDict):
    destination: str
    destination_city: str
    days: int

    # Mensaje original del usuario (para contexto en agentes)
    user_message: str

    # Historial de conversación reciente
    conversation_history: List[dict]

    # RAG context (de RAGAgent)
    rag_data: dict

    # Plan del PlannerAgent
    planner_summary: str

    # Atracciones reales (de fetch_attractions_node via RapidAPI)
    attractions: List[dict]

    # Itinerario final (de ItineraryAgent)
    itinerary: dict
