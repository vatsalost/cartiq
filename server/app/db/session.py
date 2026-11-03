"""Database session management and connectivity checks for Carti."""

import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from server.app.core.config import settings

logger = logging.getLogger("carti.db")

# Base model
Base = declarative_base()


def get_engine():
    """Create database engine with fallback handling for local development."""
    db_url = settings.DATABASE_URL
    try:
        # Test creating engine
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            echo=settings.DB_ECHO,
        )
        # Attempt a quick test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to primary database: %s", db_url.split("@")[-1])
        return engine
    except Exception as exc:
        if settings.SQLITE_FALLBACK and settings.APP_ENV != "production":
            fallback_url = "sqlite:///./carti_dev.db"
            logger.warning(
                "Primary database (%s) unavailable (%s). Falling back to SQLite for local development: %s",
                db_url.split("@")[-1],
                str(exc),
                fallback_url,
            )
            return create_engine(
                fallback_url,
                connect_args={"check_same_thread": False},
                echo=settings.DB_ECHO,
            )
        # In production or when fallback disabled, re-raise
        logger.error("Database connection failed: %s", exc)
        raise exc


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to provide a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connectivity() -> bool:
    """Check database health for /api/health."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Database connectivity check failed: %s", exc)
        return False
