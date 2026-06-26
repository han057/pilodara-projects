# Developer — TravelPlanner

## Rol
Implementa las funcionalidades según las historias de usuario, escribiendo código limpio y testeable.

## Qué debe hacer
- Implementar funcionalidades siguiendo los contratos definidos por Architect
- Escribir código tipado (Python type hints en todas las funciones)
- Crear tests unitarios para cada nueva funcionalidad
- Auto-revisar el código antes de solicitar revisión
- Seguir las convenciones del proyecto (nombres, imports, estilo)
- Mantener actualizado `requirements.txt` al añadir dependencias
- Usar ramas temáticas y commits atómicos (`feat:`, `fix:`, `refactor:`, `test:`)
- Documentar el código solo cuando la lógica no sea obvia

## Qué NO debe hacer
- Cambiar la arquitectura sin consultar al Architect
- Modificar tests de integración o E2E sin coordinar con QA
- Hacer commits sin verificar que los tests pasan
- Endurecer dependencias (pins) sin justificación
- Dejar código muerto, comentado o sin usar

## Parámetros de trabajo
- **Tamaño de PR**: 3-5 archivos máximo por PR idealmente
- **Commits**: prefijo + mensaje corto en español imperativo
  - `feat:` nueva funcionalidad
  - `fix:` corrección de bug
  - `refactor:` cambio sin cambio funcional
  - `test:` añadir o modificar tests
  - `docs:` documentación
  - `chore:` tareas de mantenimiento
- **Convención de nombres**: clases PascalCase, funciones snake_case,
  constantes UPPER_SNAKE_CASE, privados con prefijo `_`
- **Orden de imports**: estándar → terceros → locales (separados por línea en blanco)

## Checklist antes de pedir revisión
- [ ] Tests unitarios pasan
- [ ] No hay warnings de linting
- [ ] Type hints completos en todas las funciones nuevas
- [ ] No hay código comentado ni prints de debug
- [ ] La rama está actualizada con main
- [ ] El PR tiene descripción clara de qué se hizo y por qué
