# Grafo LangGraph — TravelPlanner

Arquitectura del pipeline de planificación de viajes implementada con LangGraph.

## Flujo principal

```
┌─────────────────────────────────────┐
│           ENTRADA (usuario)         │
│  "Quiero ir a París 5 días"         │
└──────────────────┬──────────────────┘
                   │
                   ▼
        ┌──────────────────┐
        │   api/routers/   │
        │    chat.py       │
        │──────────────────│
        │ • Extrae destino │
        │ • Extrae días    │
        │ • Detecta si es  │
        │   solicitud de   │
        │   viaje o        │
        │   conversación   │
        └──────┬───────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌────────────┐   ┌─────────────────────┐
│Conversacio-│   │  LangGraph Pipeline │
│nal (LLM)   │   │  ejecutar_viaje()   │
│            │   └──────────┬──────────┘
│Preguntas   │              │
│generales,  │              ▼
│sin destino │   ┌──────────────────────┐
└────────────┘   │     1. RAG NODE      │
                 │──────────────────────│
                 │ RAGAgent             │
                 │ • Consulta ChromaDB  │
                 │ • OllamaEmbeddings   │
                 │   (nomic-embed-text) │
                 │ • Clasifica chunks   │
                 │   por categoría:     │
                 │   clima, transporte, │
                 │   eventos, barrios,  │
                 │   tips               │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │    2. PLAN NODE      │
                 │──────────────────────│
                 │ PlannerAgent         │
                 │ • LLM: qwen3:1.7b   │
                 │ • Contexto RAG +     │
                 │   historial de       │
                 │   conversación       │
                 │ • Genera introducción│
                 │   experta al destino │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │  3. ATTRACTIONS NODE │
                 │──────────────────────│
                 │ fetch_attractions    │
                 │ • RapidAPI           │
                 │   (Booking.com)      │
                 │ • Busca atracciones  │
                 │   reales del destino │
                 │ • Límite: 9 items    │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │  4. ITINERARY NODE   │
                 │──────────────────────│
                 │ ItineraryAgent       │
                 │ • LLM: qwen3:1.7b   │
                 │ • Inputs:            │
                 │   - resumen planner  │
                 │   - atracciones API  │
                 │   - contexto RAG     │
                 │ • Genera N días con  │
                 │   título, descripción│
                 │   y actividades      │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │       RESPUESTA      │
                 │ ## Destino — N días  │
                 │ [intro experta]      │
                 │ [atracciones]        │
                 │ [itinerario día a día]│
                 └──────────────────────┘
```

## Definición del grafo (LangGraph)

```python
builder = StateGraph(TravelState)

builder.add_node("rag",         rag_node)
builder.add_node("planner",     plan_node)
builder.add_node("attractions", attractions_node)
builder.add_node("itinerary",   itinerary_node)

builder.add_edge(START,         "rag")
builder.add_edge("rag",         "planner")
builder.add_edge("planner",     "attractions")
builder.add_edge("attractions", "itinerary")
builder.add_edge("itinerary",   END)
```

## Estado compartido (TravelState)

```python
class TravelState(TypedDict):
    destination:          str         # "París"
    destination_city:     str         # alias para nodos de servicios
    days:                 int         # 5
    user_message:         str         # mensaje original del usuario
    conversation_history: List[dict]  # historial reciente de la sesión
    rag_data:             dict        # {weather, transport, events, neighborhoods, tips}
    planner_summary:      str         # introducción generada por PlannerAgent
    attractions:          List[dict]  # atracciones reales de RapidAPI
    itinerary:            dict        # {summary, days: [{title, description, activities}]}
```

## Modelos y servicios externos

| Componente | Modelo / Servicio |
|---|---|
| Embeddings RAG | `nomic-embed-text` via Ollama |
| LLM planificación | `qwen3:1.7b` via Ollama |
| LLM itinerario | `qwen3:1.7b` via Ollama |
| LLM conversacional | `qwen3:1.7b` via Ollama |
| Vectorstore | ChromaDB (persistente en `rag/embeddings/`) |
| Atracciones | RapidAPI — Booking.com (`booking-com15.p.rapidapi.com`) |
| Base de datos | PostgreSQL 16 (sesiones y mensajes) |
