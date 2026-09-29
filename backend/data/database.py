"""
ArogyaGrid — Database Engine & Session Factory
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import config
from data.models import Base

engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False},   # SQLite only
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    """Create all tables (idempotent)."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_session():
    """Context-manager session — auto-commit / rollback."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    """FastAPI dependency — yields a session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
