---
skill:
  name: travelplanner-agents
  description: Desarrollo y mantenimiento de agentes LangGraph (Planner, Search, Itinerary)
---

# TravelPlanner Agents

## Agentes implementados

| Agente | Archivo | Método principal | Salida |
|--------|---------|-----------------|--------|
| PlannerAgent | `agents/planner_agent.py` | `plan_trip(dest, days)` | `{destination, duration_days, summary, status, mock}` |
| SearchAgent | `agents/search_agent.py` | `search_options(query)` | `list[str]` |
| ItineraryAgent | `agents/itinerary_agent.py` | `build_itinerary(dest, days)` | `{destination, days, itinerary}` |

## Grafo LangGraph (`graph/graph.py`)
- Flujo lineal: `planner → searcher → itinerary`
- `TravelState`: destination, days, planner_summary, search_options, itinerary_final
- Lazy initialization: los agentes se crean bajo demanda

## Prompts
- Ubicación: `prompts/*.txt`
- Formato: ChatPromptTemplate de LangChain
- Variables: `{destination}`, `{days}`, `{duration_days}`, `{query}`

## Reglas
- Los agentes NO deben instanciar ChatOllama a nivel de módulo (usar lazy init)
- Cada agente debe tener test unitario que valide estructura de salida
- Los agentes deben ser importables sin efectos secundarios
