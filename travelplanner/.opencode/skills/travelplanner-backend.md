---
skill:
  name: travelplanner-backend
  description: Desarrollo backend con FastAPI, integración de agentes LangGraph y APIs externas
---

# TravelPlanner Backend

## Stack
- FastAPI + Uvicorn
- LangGraph + LangChain
- Python 3.14+, type hints obligatorios
- ChromaDB + OllamaEmbeddings para RAG

## Endpoints activos
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/chat/{session_id}` | POST | Chat con agentes |
| `/session/create` | POST | Crear sesión |
| `/session/{id}/reset` | POST | Resetear sesión |
| `/session/{id}/history` | GET | Historial de sesión |
| `/health/` | GET | Health check |

## Convenciones
- Schemas Pydantic en `api/schemas/`
- Routers FastAPI en `api/routers/`
- Importar `ejecutar_viaje` desde `graph.graph` para invocar agentes
- Fallback a mock response si el LLM no está disponible
