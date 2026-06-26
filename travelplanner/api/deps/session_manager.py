import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session as DBSession

from api.deps.database import get_session, db_available
from api.models.models import Session, Message


class SessionManager:
    _memory: dict[str, list[dict]] = {}

    @staticmethod
    def _ensure_db() -> DBSession | None:
        if not db_available():
            return None
        return get_session()

    @staticmethod
    def _close_db(db: DBSession | None):
        if db is not None:
            db.close()

    @staticmethod
    def create_session() -> str:
        session_id = str(uuid.uuid4())
        db = SessionManager._ensure_db()
        if db is not None:
            try:
                db.add(Session(id=session_id))
                db.commit()
            finally:
                db.close()
        else:
            SessionManager._memory[session_id] = []
        return session_id

    @staticmethod
    def append_message(session_id: str, role: str, content: str):
        db = SessionManager._ensure_db()
        if db is not None:
            try:
                db.add(Message(session_id=session_id, role=role, content=content))
                db.commit()
            finally:
                db.close()
        else:
            msgs = SessionManager._memory.setdefault(session_id, [])
            msgs.append({"role": role, "message": content, "time": datetime.now(timezone.utc).isoformat()})

    @staticmethod
    def get_history(session_id: str) -> list[dict]:
        db = SessionManager._ensure_db()
        if db is not None:
            try:
                rows = (
                    db.query(Message)
                    .filter(Message.session_id == session_id)
                    .order_by(Message.created_at)
                    .all()
                )
                return [
                    {"role": m.role, "message": m.content, "time": m.created_at.isoformat()}
                    for m in rows
                ]
            finally:
                db.close()
        else:
            return SessionManager._memory.get(session_id, [])

    @staticmethod
    def reset(session_id: str):
        db = SessionManager._ensure_db()
        if db is not None:
            try:
                db.query(Message).filter(Message.session_id == session_id).delete()
                db.commit()
            finally:
                db.close()
        else:
            SessionManager._memory[session_id] = []

    @staticmethod
    def session_exists(session_id: str) -> bool:
        db = SessionManager._ensure_db()
        if db is not None:
            try:
                return db.query(Session).filter(Session.id == session_id).first() is not None
            finally:
                db.close()
        else:
            return session_id in SessionManager._memory

    @staticmethod
    def delete(session_id: str):
        db = SessionManager._ensure_db()
        if db is not None:
            try:
                session = db.query(Session).filter(Session.id == session_id).first()
                if session:
                    db.delete(session)
                    db.commit()
            finally:
                db.close()
        else:
            SessionManager._memory.pop(session_id, None)
