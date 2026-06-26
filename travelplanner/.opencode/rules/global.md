---
rule:
  name: global
  description: Reglas globales del proyecto TravelPlanner
  applies_to: all
---

# Reglas Globales — TravelPlanner

## Comunicación
- Todos los mensajes y documentación en español
- Las respuestas deben ser concisas y directas
- No usar emojis a menos que el usuario lo pida explícitamente

## Calidad
- Todo el código debe pasar type checking antes de commitear
- Los tests deben ejecutarse sin errores antes de abrir un PR
- Está prohibido hacer push directo a main (salvo merges autorizados)
- Las ramas deben seguir el patrón: `feature/`, `fix/`, `refactor/`, `test/`, `docs/`

## Seguridad
- No committear secrets, API keys o tokens
- Usar `.env.example` para documentar variables necesarias
- Las variables sensibles van en `.env` (no versionado)

## Dependencias
- Al añadir una dependencia, actualizar `requirements.txt` y documentar por qué
- Preferir librerías con typing soportado
- No duplicar funcionalidad ya existente en el proyecto

## Archivos
- Máximo 200 líneas por archivo de Python (excepciones justificadas)
- Los prompts de agentes van en `prompts/` con extensión `.txt`
- Los tests reflejan la estructura del proyecto: `tests/` espeja a `src/`
