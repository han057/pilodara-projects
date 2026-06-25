# Entrega - Soporte Router Smart WiFi 6

Proyecto de atención al cliente desarrollado con:

- Streamlit para la interfaz.
- FastAPI para la API.
- LangGraph para el flujo de agentes.
- LangChain y ChromaDB para el RAG.
- Ollama con `gemma3:4b` y `nomic-embed-text`.

La entrega incluye los dos PDFs utilizados por N1 y N2 dentro de `data/`. No
necesita archivos situados fuera de esta carpeta.

## Integración en el Compose general

El archivo recomendado para la entrega conjunta es:

```text
docker/compose.integracion.yaml
```

Utiliza nombres prefijados para evitar conflictos con las APIs, interfaces u
Ollama de otros proyectos:

- `router-smartwifi6-ollama`
- `router-smartwifi6-modelos`
- `router-smartwifi6-api`
- `router-smartwifi6-streamlit`

Si el Compose principal está en la carpeta que contiene este proyecto:

```yaml
include:
  - path: ./CustomerSupportProject_PROFESOR/docker/compose.integracion.yaml
```

Después:

```powershell
docker compose up --build
```

La interfaz queda disponible por defecto en:

```text
http://127.0.0.1:8501
```

Si esos puertos ya están ocupados, pueden configurarse en el `.env` del
Compose principal:

```dotenv
ROUTER_API_PORT_HOST=8100
ROUTER_STREAMLIT_PORT_HOST=8601
```

Consulta [`docker/INTEGRACION_COMPOSE.md`](docker/INTEGRACION_COMPOSE.md) para
copiar los servicios dentro de un único YAML en lugar de utilizar `include`.

## Ejecución independiente

Para comprobar este proyecto por separado:

```powershell
cd docker
docker compose up --detach --build --wait --wait-timeout 1800
```

También puede ejecutarse `docker/iniciar_docker.bat` en Windows.

La primera ejecución descarga las imágenes, Gemma 3 4B y el modelo de
embeddings. Los modelos y el índice ChromaDB se guardan en volúmenes
persistentes.

Para detenerlo:

```powershell
cd docker
docker compose down
```

## Estructura de la entrega

```text
CustomerSupportProject_PROFESOR/
|-- app/                         # API, grafo, RAG y sesiones
|-- data/                        # PDF de FAQ y manual técnico
|-- docker/
|   |-- Dockerfile
|   |-- compose.yaml             # ejecución independiente
|   |-- compose.integracion.yaml # integración con otros proyectos
|   `-- INTEGRACION_COMPOSE.md
|-- scripts/check_project.py
|-- requirements.txt
`-- streamlit_app.py
```

No se incluyen `.venv`, logs, cachés, modelos descargados ni una base ChromaDB
generada en otro equipo.
