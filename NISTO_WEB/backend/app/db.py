"""Database configuration for the NISTO FastAPI backend."""

from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/nisto.db")

sqlite_connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    sqlite_connect_args = {"check_same_thread": False}

# SQLite needs ``check_same_thread=False`` for usage with FastAPI dependency injection
# and routers that may run in multiple worker threads.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=sqlite_connect_args,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[override]
    """Ensure SQLite enforces foreign key constraints."""

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_db() -> Generator:
    """Yield a database session for dependency injection."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

