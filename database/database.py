from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from flask import Flask
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


def init_database(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        import models  # noqa: F401

        db.create_all()

        app.logger.info(
            "SMARTEDU DATABASE INITIALIZATION: OK"
        )

        app.logger.info(
            "SMARTEDU DATABASE ENGINE: %s",
            db.engine.name,
        )


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