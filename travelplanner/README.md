# TravelPlanner

Planificador de viajes impulsado por inteligencia artificial. El usuario describe su destino y duración del viaje en lenguaje natural; el sistema genera un itinerario día a día con atracciones reales, contexto local y consejos prácticos.

## Stack

| Componente | Tecnología |
|---|---|
| Backend API | FastAPI + Uvicorn |
| Orquestación IA | LangGraph |
| Modelo de lenguaje | Ollama — qwen3:1.7b |
| Embeddings / RAG | Ollama — nomic-embed-text + ChromaDB |
| Atracciones | Booking.com via RapidAPI |
| Base de datos | PostgreSQL 16 |
| Contenedores | Docker Compose |
| Frontend | HTML + CSS + JavaScript (vanilla) |

## Estructura del proyecto

```
.
├── agents/              Agentes LLM (planner, itinerary, rag, utils)
├── api/
│   ├── chat_schema.py   Schema Pydantic del chat
│   ├── deps/            Database y SessionManager
│   ├── models/          Modelos SQLAlchemy (Session, Message)
│   └── routers/         Endpoints: chat, session, health, rag_admin
├── graph/
│   ├── graph.py         Pipeline LangGraph (RAG → Planner → Attractions → Itinerary)
│   ├── nodes.py         Nodo de atracciones (RapidAPI)
│   └── state.py         TravelState TypedDict
├── prompts/             Plantillas de prompt para cada agente
├── rag/                 Ingesta y consulta ChromaDB
├── services/
│   ├── config.py        RAPIDAPI_HOST y RAPIDAPI_KEY centralizados
│   └── attractions/     Fetcher de atracciones via Booking.com API
├── tests/               Tests unitarios
├── ui/                  Frontend (index.html, chat.js, styles.css)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Requisitos previos

- Docker y Docker Compose instalados
- Clave de API de RapidAPI con acceso a **Booking.com API** (`booking-com15.p.rapidapi.com`)

## Puesta en marcha

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd travelplanner

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores
```

Variables en `.env`:

```env
RAPIDAPI_KEY=tu_clave_de_rapidapi
OLLAMA_API_BASE_URL=http://localhost:11434
DATABASE_URL=postgresql://travelplanner:travelplanner@db:5432/travelplanner
```

`OLLAMA_API_BASE_URL` debe apuntar a tu instancia de Ollama. Si usas el Ollama incluido en Docker Compose, déjalo como está.

```bash
# 3. Arrancar todos los servicios
docker compose up --build -d
```

El primer arranque descarga los modelos de Ollama (`qwen3:1.7b` y `nomic-embed-text`), lo que puede tardar varios minutos según la conexión.

```bash
# 4. Abrir el navegador
http://localhost:8000
```

## Servicios

| Servicio | Puerto | Descripcion |
|---|---|---|
| Web (FastAPI) | 8000 | API + frontend |
| PostgreSQL | 5432 | Base de datos de sesiones |
| Ollama | 11434 | Servidor de modelos LLM |

## API principal

| Metodo | Ruta | Descripcion |
|---|---|---|
| `POST` | `/session/create` | Crear nueva sesion de conversacion |
| `POST` | `/chat/{session_id}` | Enviar mensaje y recibir respuesta |
| `POST` | `/session/{session_id}/reset` | Reiniciar conversacion |
| `GET` | `/health/ollama` | Estado de conexion con Ollama |

## RAG Admin

El panel de administracion RAG permite indexar documentos de conocimiento local (PDF, TXT, MD, CSV) para enriquecer las respuestas con informacion especifica sobre destinos.

Acceso: abrir la aplicacion en el navegador y hacer clic en **RAG Admin** en la barra lateral.

Categorias disponibles: `destinos`, `clima`, `transporte`, `eventos`, `barrios`, `tips`, `general`.

Los documentos indexados se almacenan en `rag/embeddings/vectorstore/` (excluido del repositorio — se regenera con el boton "Reindexar todo").

## Flujo de generacion de respuestas

```
Mensaje del usuario
       |
       v
  Deteccion de intencion
  (viaje / conversacional)
       |
    [viaje]──────────────────────[conversacional]
       |                                |
       v                                v
  RAG Node                       LLM directo
  (ChromaDB)                     (qwen3:1.7b)
       |
       v
  Planner Node
  (contexto + historial)
       |
       v
  Attractions Node
  (RapidAPI)
       |
       v
  Itinerary Node
  (LLM dia a dia)
       |
       v
  Respuesta en Markdown
```

## Logs

```bash
docker compose logs web -f       # API FastAPI
docker compose logs ollama -f    # Modelos LLM
docker compose logs db -f        # PostgreSQL
```
