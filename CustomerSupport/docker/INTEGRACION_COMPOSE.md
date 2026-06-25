# Integración con el Compose de la clase

La aplicación funciona de dos formas:

- Local: `run_streamlit.bat`, usando Python y Ollama instalados en Windows.
- Docker: Streamlit, FastAPI, Ollama, los modelos y ChromaDB se ejecutan en
  contenedores.

`compose.yaml` está pensado para ejecutar este proyecto por separado.
`compose.integracion.yaml` utiliza nombres con el prefijo
`router-smartwifi6-` y está preparado para convivir con otros proyectos.

## Opción 1: incluir el archivo

Si el Compose principal está en la carpeta que contiene
`CustomerSupportProject_PROFESOR`, añade:

```yaml
include:
  - path: ./CustomerSupportProject_PROFESOR/docker/compose.integracion.yaml
```

Después se inicia todo desde el Compose principal:

```powershell
docker compose up --build
```

Las rutas de `build` continúan resolviéndose desde la ubicación del archivo
incluido.

## Opción 2: crear un único YAML

Copia al Compose general:

- Los cuatro servicios de `compose.integracion.yaml`.
- Las dos entradas de la sección `volumes`.

Si el Compose general está en otra carpeta, adapta `build.context` para que
apunte a `CustomerSupportProject_PROFESOR`. Por ejemplo:

```yaml
build:
  context: ./CustomerSupportProject_PROFESOR
  dockerfile: docker/Dockerfile
```

## Evitar conflictos de puertos

Si otro proyecto ya utiliza 8000 o 8501, define otros puertos en el `.env` del
Compose principal:

```dotenv
ROUTER_API_PORT_HOST=8100
ROUTER_STREAMLIT_PORT_HOST=8601
```

Los puertos internos no se cambian porque la comunicación entre contenedores
utiliza los nombres de servicio.

## Servicios creados

- `router-smartwifi6-ollama`
- `router-smartwifi6-modelos`
- `router-smartwifi6-api`
- `router-smartwifi6-streamlit`

Los nombres tienen prefijo para no interferir con otros servicios llamados
`api`, `streamlit` u `ollama`.
