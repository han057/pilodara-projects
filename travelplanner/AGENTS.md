# Sistema Multi-Agente — TravelPlanner

## Indice

- [Docs de cada agente](docs/agents/)
  - [PM](docs/agents/pm.md)
  - [Architect](docs/agents/architect.md)
  - [Developer](docs/agents/developer.md)
  - [QA](docs/agents/qa.md)
- [Reglas globales](.opencode/rules/global.md)
- [Flujo de trabajo](.opencode/rules/workflow.md)
- [Skills del proyecto](.opencode/skills/)

## Roles

| Rol | Responsabilidad | Documento |
|-----|----------------|-----------|
| PM | Requisitos, priorización, validación | [docs/agents/pm.md](docs/agents/pm.md) |
| Architect | Arquitectura, contratos, tech stack | [docs/agents/architect.md](docs/agents/architect.md) |
| Developer | Implementación, tests unitarios | [docs/agents/developer.md](docs/agents/developer.md) |
| QA | Tests de integración, validación | [docs/agents/qa.md](docs/agents/qa.md) |

## Flujo de trabajo

```
PM ──define──> Architect ──diseña──> Developer ──implementa──> QA ──valida──> PM (acepta)
         ^                                                            |
         └──────────────────── feedback ──────────────────────────────┘
```

Ver detalles en [.opencode/rules/workflow.md](.opencode/rules/workflow.md).

## Stack técnico

| Componente | Tecnología |
|------------|-----------|
| Backend | Python 3.14+, FastAPI, Uvicorn |
| Agentes | LangGraph, LangChain, Ollama (qwen3:1.7b) |
| RAG | ChromaDB, OllamaEmbeddings |
| Frontend | HTML + CSS + JS vanilla |
| APIs externas | RapidAPI (booking-com15) |
| Infra | Docker, docker-compose |
| Testing | pytest |

## Skills del proyecto

| Skill | Descripción |
|-------|-------------|
| [Backend](.opencode/skills/travelplanner-backend.md) | FastAPI, endpoints, integración de agentes |
| [Agentes](.opencode/skills/travelplanner-agents.md) | LangGraph, Planner, Search, Itinerary |
| [Testing](.opencode/skills/travelplanner-testing.md) | pytest, estructura de tests |

## Reglas globales

Ver [.opencode/rules/global.md](.opencode/rules/global.md) para las reglas completas.
