from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.routers.chat import router as chat_router
from api.routers.session import router as session_router
from api.routers.health import router as health_router
from api.routers.rag_admin import router as rag_admin_router
from api.deps.database import init_db


@asynccontextmanager
async def _lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=_lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir UI en /ui
app.mount("/ui", StaticFiles(directory="ui"), name="ui")

# Servir index.html en /
@app.get("/")
def root():
    return FileResponse("ui/index.html")

# Rutas API
app.include_router(chat_router, prefix="/chat")
app.include_router(session_router, prefix="/session")
app.include_router(health_router, prefix="/health")
app.include_router(rag_admin_router, prefix="/rag")
