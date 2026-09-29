from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def env(name: str, default: Any = None) -> Any:
    value = os.getenv(name)

    if value is None:
        return default

    value = value.strip()

    if value == "":
        return default

    return value


def env_bool(name: str, default: bool = False) -> bool:
    value = env(name)

    if value is None:
        return default

    return value.lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def env_int(name: str, default: int) -> int:
    value = env(name)

    if value is None:
        return default

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    value = env(name)

    if value is None:
        return default or []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def normalize_database_url(url: str | None) -> str | None:
    if not url:
        return None

    url = url.strip()

    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    return url


class Config:
    APP_ENV = env("APP_ENV", "development").lower()

    SECRET_KEY = env(
        "SECRET_KEY",
        "smartedu-development-secret-change-this",
    )

    SECURITY_PASSWORD_SALT = env(
        "SECURITY_PASSWORD_SALT",
        "smartedu-development-salt-change-this",
    )

    DATABASE_URL = normalize_database_url(
        env("DATABASE_URL")
    )

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    elif APP_ENV == "production":
        SQLALCHEMY_DATABASE_URI = ""
    else:
        SQLALCHEMY_DATABASE_URI = (
            "sqlite:///"
            + str(BASE_DIR / "smartedu.db")
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    SESSION_COOKIE_NAME = "smartedu_session"

    SESSION_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SECURE = (
        APP_ENV == "production"
    )

    SESSION_COOKIE_SAMESITE = "Lax"

    PERMANENT_SESSION_LIFETIME = timedelta(
        days=7
    )

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    JSON_SORT_KEYS = False

    CORS_ORIGINS = env_list(
        "CORS_ORIGINS",
        ["*"],
    )

    RATELIMIT_ENABLED = env_bool(
        "RATELIMIT_ENABLED",
        True,
    )

    RATELIMIT_DEFAULT = env(
        "RATELIMIT_DEFAULT",
        "200 per day;50 per hour",
    )

    LOG_LEVEL = env(
        "LOG_LEVEL",
        "INFO",
    ).upper()

    UPLOAD_FOLDER = env(
        "UPLOAD_FOLDER",
        str(BASE_DIR / "uploads"),
    )

    MAX_LOGIN_ATTEMPTS = env_int(
        "MAX_LOGIN_ATTEMPTS",
        5,
    )

    LOGIN_LOCK_MINUTES = env_int(
        "LOGIN_LOCK_MINUTES",
        15,
    )

    @classmethod
    def validate(cls) -> None:
        if cls.APP_ENV != "production":
            return

        if (
            not cls.SECRET_KEY
            or cls.SECRET_KEY
            == "smartedu-development-secret-change-this"
        ):
            raise RuntimeError(
                "SECRET_KEY deve ser configurada "
                "em produção."
            )

        if (
            not cls.SECURITY_PASSWORD_SALT
            or cls.SECURITY_PASSWORD_SALT
            == "smartedu-development-salt-change-this"
        ):
            raise RuntimeError(
                "SECURITY_PASSWORD_SALT deve ser "
                "configurada em produção."
            )

        if not cls.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL não foi configurada."
            )

        if not cls.DATABASE_URL.startswith(
            "postgresql://"
        ):
            raise RuntimeError(
                "Em produção, DATABASE_URL deve "
                "apontar para PostgreSQL."
            )


class DevelopmentConfig(Config):
    APP_ENV = "development"


class ProductionConfig(Config):
    APP_ENV = "production"


def get_config():
    if Config.APP_ENV == "production":
        ProductionConfig.validate()
        return ProductionConfig

    return DevelopmentConfig