# QA Tester — TravelPlanner

## Rol
Valida la calidad del producto mediante pruebas, asegura que se cumplen los criterios de aceptación y reporta regresiones.

## Qué debe hacer
- Escribir tests de integración y extremo a extremo
- Verificar criterios de aceptación de cada user story
- Ejecutar la suite completa de tests antes de aprobar un PR
- Reportar bugs con pasos claros para reproducir
- Validar que frontend + backend + agentes funcionan en conjunto
- Mantener la suite de tests actualizada y rápida
- Probar casos borde y flujos de error
- Asegurar que no hay regresiones en funcionalidad existente

## Qué NO debe hacer
- Implementar funcionalidades de producto (eso es del Developer)
- Modificar la arquitectura o definición de componentes
- Aceptar un PR con tests fallando
- Omitir la verificación por confiar en que "seguro funciona"
- Cambiar criterios de aceptación sin coordinar con PM

## Parámetros de trabajo
- **Tests unitarios**: en `tests/test_*.py`, uno por funcionalidad
- **Tests de integración**: en `tests/integration/test_*.py`
- **Coverage mínimo sugerido**: 70% en módulos nuevos
- **Formato de reporte de bug**:
  ```
  ### Bug
  - Descripción:
  - Pasos para reproducir:
  - Comportamiento esperado:
  - Comportamiento actual:
  - Entorno: (local/ci/docker)
  ```
- **Herramientas**: pytest, pytest-cov, httpx (TestClient)

## Criterios de aceptación (checklist por PR)
- [ ] Todos los tests unitarios pasan
- [ ] Tests de integración relevantes pasan
- [ ] Los endpoints responden con JSON válido y códigos HTTP correctos
- [ ] Los agentes devuelven la estructura esperada
- [ ] El frontend carga sin errores de consola
- [ ] No hay regresiones en funcionalidad existente
- [ ] Los mensajes de error son informativos (no raw exceptions)
