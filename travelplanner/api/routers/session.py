from fastapi import APIRouter, HTTPException
from api.deps.session_manager import SessionManager

router = APIRouter()

@router.post("/create")
def create_session():
    session_id = SessionManager.create_session()
    return {"session_id": session_id}

@router.post("/{session_id}/reset")
def reset_session(session_id: str):
    SessionManager.reset(session_id)
    return {"status": "ok"}

@router.get("/{session_id}/history")
def get_history(session_id: str):
    return {"history": SessionManager.get_history(session_id)}

@router.delete("/{session_id}")
def delete_session(session_id: str):
    if not SessionManager.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    SessionManager.delete(session_id)
    return {"status": "ok"}
