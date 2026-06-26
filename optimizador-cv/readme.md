# Optimizador Inteligente de Curriculums

Sistema multi-agente con IA que optimiza automaticamente tu CV para mejorar su compatibilidad con filtros ATS. El flujo combina matching semantico de ofertas con embeddings, contexto RAG y generacion con LLM local mediante Ollama.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Ollama](https://img.shields.io/badge/LLM-Ollama-orange)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED)

## Caracteristicas

- Matching automatico de ofertas usando ChromaDB y `nomic-embed-text`
- Optimizacion del CV con LLM local (`qwen3:8b`)
- Evaluacion ATS con keywords encontradas, faltantes y puntuaciones
- Base de conocimiento RAG con buenas practicas de CV
- API REST con FastAPI y frontend web integrado
- Exportacion del CV optimizado a PDF
- Ejecucion local o mediante Docker

## Arquitectura

```text
START -> match_offer -> review_cv -> END
           |               |
           |               -> CV Reviewer Agent (LLM + RAG)
           -> ChromaDB + embeddings
```

## Estructura del proyecto

```text
optimizador-cv/
|-- Dockerfile
|-- docker-compose.yml
|-- chroma_db/
|-- optimizador_project/
|   |-- api/
|   |-- data/
|   |-- docs/
|   |-- ofertas/
|   |-- optimizador/
|   |   |-- agents/
|   |   |-- graph/
|   |   |-- models/
|   |   |-- rag/
|   |   `-- utils/
|   |-- static/
|   `-- tests/
`-- readme.md
```

## Requisitos

### Opcion 1: ejecucion local

- Python 3.9 o superior
- Ollama instalado y corriendo
- Modelos descargados:
  - `qwen3:8b`
  - `nomic-embed-text`

### Opcion 2: ejecucion con Docker

- Docker Desktop corriendo
- Ollama corriendo en la maquina host
- Modelos descargados en Ollama:
  - `qwen3:8b`
  - `nomic-embed-text`

Descarga de modelos:

```bash
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

## Instalacion local

```bash
git clone https://github.com/tu-usuario/optimizador-cv.git
cd optimizador-cv/optimizador_project
pip install -e .
```

Para desarrollo:

```bash
pip install -e ".[dev]"
```

## Uso

### Modo web local

```bash
cd optimizador_project
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Abre [http://localhost:8000](http://localhost:8000).

### Modo Docker

Desde la raiz del proyecto:

```bash
docker compose up --build
```

Abre [http://localhost:8000](http://localhost:8000).

Configuracion actual de Docker:

- El contenedor expone la API en `8000`
- `OLLAMA_BASE_URL` apunta a `http://host.docker.internal:11434`
- `chroma_db/` se monta como volumen persistente

Nota:

- En Windows y macOS, `host.docker.internal` suele funcionar directamente
- En Linux, puede ser necesario cambiar `OLLAMA_BASE_URL` por la IP de host accesible desde Docker

### Levantarlo en otro ordenador

Si otra persona descarga este proyecto, necesita estas piezas:

- Docker Desktop funcionando
- Ollama instalado y corriendo
- Los modelos `qwen3:8b` y `nomic-embed-text`

Pasos:

```bash
git clone <repo>
cd optimizador-cv
ollama pull qwen3:8b
ollama pull nomic-embed-text
docker compose up --build
```

Luego abre [http://localhost:8000](http://localhost:8000).

Notas por sistema:

- Windows y macOS: la configuracion actual suele funcionar sin cambios
- Linux: `host.docker.internal` puede no resolver
- Si usas Linux, cambia `OLLAMA_BASE_URL` en `docker-compose.yml` por una IP accesible desde el contenedor

Ejemplo en Linux:

```yaml
environment:
  OLLAMA_BASE_URL: http://172.17.0.1:11434
```

Si la pagina abre pero no salen ofertas:

- revisa que Ollama siga activo
- revisa que `nomic-embed-text` este descargado
- prueba `http://localhost:8000/api/health`
- prueba `http://localhost:8000/api/offers`

### Modo CLI

```bash
cd optimizador_project
python -m optimizador
```

## Flujo funcional

1. El sistema indexa las ofertas de `optimizador_project/ofertas/` en ChromaDB.
2. El usuario sube un CV en PDF o TXT.
3. Se calcula el embedding del CV y se busca la oferta mas compatible.
4. El agente analiza la oferta, optimiza el CV y evalua la compatibilidad ATS.
5. El frontend muestra puntuaciones, keywords, mejoras y el CV final.
6. El usuario puede descargar el resultado en PDF.

## Endpoints API

| Metodo | Ruta | Descripcion |
|---|---|---|
| `GET` | `/` | Interfaz web |
| `GET` | `/api/health` | Estado de API, Ollama y modelos |
| `GET` | `/api/offers` | Lista de ofertas indexadas |
| `GET` | `/api/offers/{filename}` | Detalle de una oferta |
| `POST` | `/api/optimize` | Optimiza un CV subido como `cv_file` |
| `POST` | `/api/download-pdf` | Genera un PDF del CV optimizado |

## Configuracion

La configuracion principal esta en [`optimizador_project/optimizador/config.py`](./optimizador_project/optimizador/config.py).

Parametros relevantes:

| Parametro | Default | Descripcion |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | URL base de Ollama |
| `LLM_CONFIG.model` | `qwen3:8b` | Modelo principal |
| `RAG_CONFIG.top_k` | `3` | Documentos RAG recuperados |
| `OFERTAS_RAG_CONFIG.top_k` | `1` | Numero de ofertas candidatas |

## Tests

Tests no integracion:

```bash
cd optimizador_project
python -m pytest tests -m "not integration" -v
```

Tests de integracion con Ollama:

```bash
cd optimizador_project
python -m pytest tests -m integration -v
```

## Solucion de problemas

### No aparecen ofertas en la interfaz

Comprueba:

- Que Ollama esta corriendo
- Que `nomic-embed-text` esta descargado
- Que `optimizador_project/ofertas/` contiene archivos `.txt` o `.pdf`
- Que `OLLAMA_BASE_URL` apunta a una instancia accesible desde donde corre la API

Prueba el endpoint:

```bash
python -c "import json, urllib.request; print(json.load(urllib.request.urlopen('http://localhost:8000/api/offers')))"
```

### Docker no conecta con el daemon

En Windows, asegurate de que Docker Desktop este abierto y el engine este en estado `running`.

### La API arranca pero no detecta Ollama en Docker

Verifica que Ollama este disponible en el host y que `docker-compose.yml` use una URL accesible desde el contenedor.

## Tecnologias

- [FastAPI](https://fastapi.tiangolo.com/)
- [LangGraph](https://langchain-ai.github.io/langgraph/)
- [LangChain](https://python.langchain.com/)
- [Ollama](https://ollama.com/)
- [ChromaDB](https://www.trychroma.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [fpdf2](https://py-pdf.github.io/fpdf2/)

## Licencia

MIT
