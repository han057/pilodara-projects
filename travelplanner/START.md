**START — feature/agents**

- **Propósito:** Poner en marcha la rama `feature/agents` y dejar instrucciones mínimas para desarrollar los agentes (`agents/`).

- **Checklist rápida:**
  - `git pull origin feature/agents`.
  - Entorno virtual: `python -m venv .venv` → `.\\.venv\\Scripts\\Activate.ps1`.
  - `pip install -r requirements.txt`.

- **Áreas a trabajar (archivos):**
  - `agents/planner_agent.py` — implementar `plan_trip(destination, days)` con lógica básica.
  - `agents/search_agent.py` — `search_options(query)` integrando `integrations/` mocks.
  - `agents/itinerary_agent.py` — `build_itinerary(destination, days)`.

- **Tareas iniciales:**
  1. Escribir funciones con interfaces claras y tipos (typing).
  2. Añadir tests en `tests/test_agents.py` para cada agente.
  3. Documentar en `prompts/` los prompts iniciales a usar por cada agente.

- **Comprobaciones locales:**
  - Ejecutar `python -c "from agents.planner_agent import PlannerAgent; print(PlannerAgent().plan_trip('Paris',3))"` para sanity check.

- **Notas de colaboración:**
  - Mantener PRs pequeños por agente.
