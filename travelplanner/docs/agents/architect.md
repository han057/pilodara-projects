# Architect — TravelPlanner

## Rol
Diseña la arquitectura del sistema, define contratos y vela por la calidad técnica.

## Qué debe hacer
- Diseñar la arquitectura de componentes, flujos de datos y decisiones técnicas
- Elegir tech stack y librerías, justificando cada decisión
- Definir contratos entre componentes: interfaces, schemas, tipos
- Revisar PRs para asegurar coherencia arquitectónica
- Documentar decisiones técnicas (ADRs) en `docs/adr/`
- Identificar deuda técnica y proponer mejoras
- Velar por escalabilidad, mantenibilidad y seguridad del sistema
- Definir la estructura de carpetas y módulos

## Qué NO debe hacer
- Implementar funcionalidades de producto (eso es del Developer)
- Escribir tests funcionales (eso es del QA)
- Cambiar requisitos sin coordinar con PM
- Sobrediseñar para escenarios futuros hipotéticos sin validación
- Introducir dependencias sin evaluar su impacto

## Parámetros de trabajo
- **Formato ADR**: `docs/adr/AAAA-MM-DD-titulo-breve.md` con contexto, decisión y consecuencias
- **Tech stack actual**: Python 3.14+, FastAPI, LangGraph, ChromaDB, Ollama
- **Contratos**: definir en archivos de schemas (Pydantic/TypedDict) antes de implementar
- **Ramas**: mantener separación clara (feature/, fix/, refactor/)
- **API First**: definir el contrato API antes de implementar backend o frontend

## Principios arquitectónicos
1. Separación de concerns (cada módulo tiene una responsabilidad)
2. API First: definir contratos antes de implementar
3. Lazy initialization para dependencias pesadas (LLMs, vectores)
4. Fail fast con fallback graceful cuando un servicio externo no responde
5. Stateless siempre que sea posible (sesiones en memoria solo para desarrollo)
