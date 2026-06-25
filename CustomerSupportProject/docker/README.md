# Ejecución completa con Docker

Esta carpeta permite ejecutar la aplicación completa sin utilizar el entorno
virtual ni el Ollama instalados en Windows.

Para añadir el proyecto a un Compose que ya contiene otras aplicaciones, usa
`compose.integracion.yaml` y consulta `INTEGRACION_COMPOSE.md`.

Docker Compose crea:

- `ollama`: servidor local de modelos.
- `modelos`: descarga `gemma3:4b` y `nomic-embed-text`.
- `api`: FastAPI, LangGraph, LangChain y ChromaDB.
- `streamlit`: interfaz gráfica.

Los PDFs se incluyen en la imagen desde `../data`. ChromaDB y los modelos se
guardan en volúmenes persistentes para no descargarlos o indexarlos de nuevo en
cada arranque.

## Requisitos

- Docker Desktop en ejecución.
- Al menos 15 GB libres en disco.
- Se recomiendan 8 GB de memoria disponible para Docker.
- Internet durante el primer arranque.

## Inicio sencillo en Windows

Ejecuta:

```text
iniciar_docker.bat
```

La primera ejecución será lenta porque construye la imagen, descarga Gemma 3
4B y genera el índice vectorial.

Después estarán disponibles:

- Interfaz: <http://127.0.0.1:8501>
- API: <http://127.0.0.1:8000/docs>

No ejecutes simultáneamente la versión local y la versión Docker con los
puertos predeterminados. Si necesitas mantener ambas abiertas, configura
`API_PORT_HOST` y `STREAMLIT_PORT_HOST` en un archivo `.env`.

Para detener los contenedores usa `detener_docker.bat`. Para revisar su salida
usa `ver_logs.bat`.

## Comandos

Desde esta carpeta:

```powershell
docker compose up --detach --build --wait --wait-timeout 1800
docker compose ps
docker compose logs --follow
docker compose down
```

## Configuración opcional

Copia `.env.example` como `.env` dentro de esta carpeta para cambiar modelos,
datos de contacto o puertos.

Ejemplo para utilizar otros puertos en el ordenador:

```dotenv
API_PORT_HOST=8100
STREAMLIT_PORT_HOST=8601
```

## Reiniciar los datos persistentes

El siguiente comando elimina contenedores, el índice Chroma y los modelos
descargados:

```powershell
docker compose down --volumes
```

Debe utilizarse solo cuando se quiera reconstruir todo desde cero.
