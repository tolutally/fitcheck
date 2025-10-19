from __future__ import annotations

import os
from functools import lru_cache
from typing import AsyncGenerator, Generator, Optional

from sqlalchemy import event, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import settings
from ..models.base import Base


class _DatabaseSettings:
    """Database configuration for Fitscore backend.
    Settings are loaded from environment variables at import time.
    Supports both sync and async database connections."""

    SYNC_DATABASE_URL: str = settings.SYNC_DATABASE_URL
    ASYNC_DATABASE_URL: str = settings.ASYNC_DATABASE_URL
    DB_ECHO: bool = settings.DB_ECHO

    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))

    DB_CONNECT_ARGS = (
        {"check_same_thread": False, "timeout": 30} if SYNC_DATABASE_URL.startswith("sqlite") else {}
    )


settings = _DatabaseSettings()


def _configure_sqlite(engine: Engine) -> None:
    """
    For SQLite:

    * Enable WAL mode (better concurrent writes).
    * Enforce foreign-key constraints.
    * Safe noop for non-SQLite engines.
    """
    if engine.dialect.name != "sqlite":
        return

    @event.listens_for(engine, "connect", once=True)
    def _set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


@lru_cache(maxsize=1)
def get_sync_engine() -> Engine:
    """Get or create the SQLAlchemy engine for synchronous operations."""
    engine = create_engine(
        settings.SYNC_DATABASE_URL,
        echo=settings.DB_ECHO,
        connect_args=settings.DB_CONNECT_ARGS,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
    )
    _configure_sqlite(engine)
    return engine


@lru_cache(maxsize=1)
def get_async_engine() -> AsyncEngine:
    """Get or create the SQLAlchemy engine for asynchronous operations."""
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        echo=settings.DB_ECHO,
        connect_args=settings.DB_CONNECT_ARGS,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
    )
    return engine


# ──────────────────────────────────────────────────────────────────────────────
# Session factories
# ──────────────────────────────────────────────────────────────────────────────

sync_engine: Engine = get_sync_engine()
async_engine: AsyncEngine = get_async_engine()

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)


def get_sync_db_session() -> Generator[Session, None, None]:
    """
    Yield a *transactional* synchronous ``Session``.

    Commits if no exception was raised, otherwise rolls back. Always closes.
    Useful for CLI scripts or rare sync paths.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_models(Base: Base) -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
