---
rule:
  name: workflow
  description: Flujo de trabajo del sistema multi-agente
  applies_to: all
---

# Flujo de Trabajo Multi-Agente

## Ciclo por tarea

1. **PM** define la tarea con:
   - Título y descripción
   - Criterios de aceptación (lista verificable)
   - Prioridad (P0/P1/P2/P3)
   - Asignación al agente responsable

2. **Architect** (si aplica) revisa y define:
   - Enfoque técnico
   - Archivos a modificar
   - Contratos involucrados
   - Riesgos y alternativas

3. **Developer** implementa:
   - Crear rama desde `main` con nombre descriptivo
   - Commits atómicos con prefijo
   - Auto-revisión con checklist en `docs/agents/developer.md`
   - Abrir PR hacia `main`

4. **QA** valida:
   - Ejecutar tests unitarios y de integración
   - Verificar criterios de aceptación
   - Probar flujos completo (backend + frontend si aplica)
   - Aprobar o rechazar con comentarios

5. **PM** acepta o solicita cambios:
   - Si OK: mergear PR
   - Si no: volver al paso 2 o 3 según corresponda

## Reglas de escalamiento
- Si un bloqueo técnico dura más de 15 minutos, consultar al Architect
- Si un requisito cambia, PM debe actualizar la tarea
- Si QA encuentra un bug crítico, la tarea vuelve a Developer con prioridad P0
