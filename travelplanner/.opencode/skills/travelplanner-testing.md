---
skill:
  name: travelplanner-testing
  description: Testing con pytest, tests unitarios, de integración y E2E
---

# TravelPlanner Testing

## Estructura
```
tests/
├── test_agents.py          # Tests unitarios de agentes
├── test_api.py             # Tests de endpoints API
├── test_rag.py             # Tests de RAG (embeddings, vectorstore)
├── conftest.py             # Fixtures globales y skips condicionales
├── integration/
│   └── test_itinerary_flow.py
├── nodes/
│   ├── test_fetch_attractions_node.py
│   ├── test_fetch_flights_node.py
│   └── test_enrich_itinerary_node.py
├── rag/
│   └── test_rag_agent.py
└── services/
    ├── test_attractions_fetcher.py
    ├── test_attractions_service.py
    ├── test_flight_destination_service.py
    ├── test_flight_fetcher.py
    ├── test_location_service.py
    └── test_search_flights_service.py
```

## Ejecución
```powershell
python -m pytest tests/ -v
python -m pytest tests/test_agents.py -v
python -m pytest tests/test_api.py -v
```

## Convenciones
- Tests que requieren Ollama se skippean automáticamente si no está disponible
- Usar TestClient de FastAPI para tests de endpoints
- Nombrar tests como `test_<funcionalidad>`
- Cada agente/lógica nueva debe tener test unitario
