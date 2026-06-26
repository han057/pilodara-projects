import os
import logging

from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://travelplanner:travelplanner@localhost:5432/travelplanner",
)

Base = declarative_base()

_engine = None
_SessionLocal = None
_db_available = False


def _get_engine():
    global _engine
    if _engine is None:
        from sqlalchemy import create_engine
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine


def _get_session_local():
    global _SessionLocal
    if _SessionLocal is None:
        from sqlalchemy.orm import sessionmaker
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())
    return _SessionLocal


def get_session():
    return _get_session_local()()


def init_db():
    global _db_available
    try:
        from api.models.models import Session, Message
        _get_engine()
        Base.metadata.create_all(bind=_get_engine())
        _db_available = True
        logger.info("PostgreSQL connected and tables created")
    except Exception as exc:
        _db_available = False
        logger.warning("PostgreSQL not available (%s). Using in-memory fallback.", exc)


def db_available() -> bool:
    return _db_available
