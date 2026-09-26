from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


db = SQLAlchemy(
    session_options={
        "autoflush": False,
        "expire_on_commit": False,
    }
)

migrate = Migrate()


@contextmanager
def transaction() -> Generator:
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def database_health() -> dict:
    try:
        db.session.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": db.engine.name,
        }

    except Exception as exc:
        return {
            "status": "unhealthy",
            "database": db.engine.name,
            "error": str(exc),
        }


def commit() -> None:
    db.session.commit()


def rollback() -> None:
    db.session.rollback()


def close_session() -> None:
    db.session.remove()