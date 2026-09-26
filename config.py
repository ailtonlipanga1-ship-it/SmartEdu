"""
SmartEdu Access
Configuração central da aplicação.

Responsabilidades:
- Carregamento das variáveis de ambiente
- Configuração da base de dados
- Segurança
- Sessões
- Cookies
- CSRF
- Rate limiting
- Uploads
- API
- JWT/API devices
- Logs
- Ambiente de execução
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


# ============================================================
# DIRETÓRIOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def env(
    name: str,
    default: Any = None,
    cast: type | None = None,
) -> Any:
    """
    Obtém uma variável de ambiente de forma segura.

    Exemplo:
        env("PORT", 5000, int)
    """

    value = os.getenv(name)

    if value is None:
        return default

    value = value.strip()

    if cast is None:
        return value

    try:
        if cast is bool:
            return value.lower() in {
                "1",
                "true",
                "yes",
                "on",
                "sim",
            }

        return cast(value)

    except (ValueError, TypeError):
        return default


def env_list(
    name: str,
    default: list[str] | None = None,
) -> list[str]:
    """
    Lê uma lista separada por vírgulas.
    """

    value = os.getenv(name)

    if not value:
        return default or []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


# ============================================================
# CONFIGURAÇÃO PRINCIPAL
# ============================================================

class Config:
    """
    Configuração base do SmartEdu Access.
    """

    # --------------------------------------------------------
    # IDENTIDADE
    # --------------------------------------------------------

    APP_NAME = env(
        "APP_NAME",
        "SmartEdu Access",
    )

    APP_VERSION = env(
        "APP_VERSION",
        "1.0.0",
    )

    APP_ENV = env(
        "APP_ENV",
        "development",
    )

    DEBUG = env(
        "DEBUG",
        False,
        bool,
    )

    TESTING = env(
        "TESTING",
        False,
        bool,
    )

    # --------------------------------------------------------
    # SEGURANÇA
    # --------------------------------------------------------

    SECRET_KEY = env(
        "SECRET_KEY",
        "CHANGE-ME-IN-PRODUCTION",
    )

    SECURITY_PASSWORD_SALT = env(
        "SECURITY_PASSWORD_SALT",
        "CHANGE-ME-PASSWORD-SALT",
    )

    # --------------------------------------------------------
    # URL DA APLICAÇÃO
    # --------------------------------------------------------

    SERVER_NAME = env(
        "SERVER_NAME",
        None,
    )

    APPLICATION_ROOT = env(
        "APPLICATION_ROOT",
        "/",
    )

    PREFERRED_URL_SCHEME = env(
        "PREFERRED_URL_SCHEME",
        "https" if APP_ENV == "production" else "http",
    )

    # --------------------------------------------------------
    # BASE DE DADOS
    # --------------------------------------------------------

    DATABASE_URL = env(
        "DATABASE_URL",
        None,
    )

    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = (
            "sqlite:///"
            + str(BASE_DIR / "smartedu.db")
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # --------------------------------------------------------
    # SESSÃO
    # --------------------------------------------------------

    PERMANENT_SESSION_LIFETIME = timedelta(
        hours=env(
            "SESSION_LIFETIME_HOURS",
            8,
            int,
        )
    )

    SESSION_COOKIE_NAME = env(
        "SESSION_COOKIE_NAME",
        "smartedu_session",
    )

    SESSION_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SECURE = env(
        "SESSION_COOKIE_SECURE",
        APP_ENV == "production",
        bool,
    )

    SESSION_COOKIE_SAMESITE = env(
        "SESSION_COOKIE_SAMESITE",
        "Lax",
    )

    # --------------------------------------------------------
    # CSRF
    # --------------------------------------------------------

    WTF_CSRF_ENABLED = env(
        "WTF_CSRF_ENABLED",
        True,
        bool,
    )

    WTF_CSRF_TIME_LIMIT = timedelta(
        hours=2
    )

    WTF_CSRF_CHECK_DEFAULT = True

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    JSON_SORT_KEYS = False

    JSON_AS_ASCII = False

    JSONIFY_PRETTYPRINT_REGULAR = False

    # --------------------------------------------------------
    # UPLOADS
    # --------------------------------------------------------

    UPLOAD_FOLDER = Path(
        env(
            "UPLOAD_FOLDER",
            str(BASE_DIR / "uploads"),
        )
    )

    MAX_CONTENT_LENGTH = env(
        "MAX_CONTENT_LENGTH",
        10 * 1024 * 1024,
        int,
    )

    ALLOWED_IMAGE_EXTENSIONS = {
        "jpg",
        "jpeg",
        "png",
        "webp",
    }

    # --------------------------------------------------------
    # RATE LIMITING
    # --------------------------------------------------------

    RATELIMIT_ENABLED = env(
        "RATELIMIT_ENABLED",
        True,
        bool,
    )

    RATELIMIT_DEFAULT = env(
        "RATELIMIT_DEFAULT",
        "200 per hour",
    )

    RATELIMIT_STORAGE_URI = env(
        "RATELIMIT_STORAGE_URI",
        "memory://",
    )

    RATELIMIT_HEADERS_ENABLED = True

    RATELIMIT_FAIL_ON_FIRST_BREACH = False

    # --------------------------------------------------------
    # CORS
    # --------------------------------------------------------

    CORS_ORIGINS = env_list(
        "CORS_ORIGINS",
        [
            "http://localhost:5000",
            "http://127.0.0.1:5000",
        ],
    )

    CORS_SUPPORTS_CREDENTIALS = True

    # --------------------------------------------------------
    # API
    # --------------------------------------------------------

    API_PREFIX = env(
        "API_PREFIX",
        "/api",
    )

    API_VERSION = env(
        "API_VERSION",
        "v1",
    )

    API_RATE_LIMIT = env(
        "API_RATE_LIMIT",
        "100 per minute",
    )

    # --------------------------------------------------------
    # ESP32 / DISPOSITIVOS
    # --------------------------------------------------------

    DEVICE_REQUEST_TIMEOUT = env(
        "DEVICE_REQUEST_TIMEOUT",
        10,
        int,
    )

    DEVICE_HEARTBEAT_TIMEOUT = env(
        "DEVICE_HEARTBEAT_TIMEOUT",
        180,
        int,
    )

    DEVICE_TOKEN_LENGTH = env(
        "DEVICE_TOKEN_LENGTH",
        64,
        int,
    )

    DEVICE_CLOCK_DRIFT_SECONDS = env(
        "DEVICE_CLOCK_DRIFT_SECONDS",
        120,
        int,
    )

    # --------------------------------------------------------
    # RFID
    # --------------------------------------------------------

    RFID_UID_MAX_LENGTH = env(
        "RFID_UID_MAX_LENGTH",
        32,
        int,
    )

    # --------------------------------------------------------
    # AUTENTICAÇÃO
    # --------------------------------------------------------

    PASSWORD_MIN_LENGTH = env(
        "PASSWORD_MIN_LENGTH",
        10,
        int,
    )

    MAX_LOGIN_ATTEMPTS = env(
        "MAX_LOGIN_ATTEMPTS",
        5,
        int,
    )

    LOGIN_LOCKOUT_MINUTES = env(
        "LOGIN_LOCKOUT_MINUTES",
        15,
        int,
    )

    # --------------------------------------------------------
    # AUDITORIA
    # --------------------------------------------------------

    AUDIT_LOG_ENABLED = env(
        "AUDIT_LOG_ENABLED",
        True,
        bool,
    )

    # --------------------------------------------------------
    # NOTIFICAÇÕES
    # --------------------------------------------------------

    NOTIFICATIONS_ENABLED = env(
        "NOTIFICATIONS_ENABLED",
        True,
        bool,
    )

    # --------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------

    MAIL_SERVER = env(
        "MAIL_SERVER",
        "",
    )

    MAIL_PORT = env(
        "MAIL_PORT",
        587,
        int,
    )

    MAIL_USE_TLS = env(
        "MAIL_USE_TLS",
        True,
        bool,
    )

    MAIL_USERNAME = env(
        "MAIL_USERNAME",
        "",
    )

    MAIL_PASSWORD = env(
        "MAIL_PASSWORD",
        "",
    )

    MAIL_DEFAULT_SENDER = env(
        "MAIL_DEFAULT_SENDER",
        "",
    )

    # --------------------------------------------------------
    # LOGGING
    # --------------------------------------------------------

    LOG_LEVEL = env(
        "LOG_LEVEL",
        "INFO",
    )

    LOG_FILE = env(
        "LOG_FILE",
        str(BASE_DIR / "logs" / "smartedu.log"),
    )

    # --------------------------------------------------------
    # PAGINAÇÃO
    # --------------------------------------------------------

    DEFAULT_PAGE_SIZE = env(
        "DEFAULT_PAGE_SIZE",
        25,
        int,
    )

    MAX_PAGE_SIZE = env(
        "MAX_PAGE_SIZE",
        100,
        int,
    )

    # --------------------------------------------------------
    # CACHE
    # --------------------------------------------------------

    CACHE_TYPE = env(
        "CACHE_TYPE",
        "SimpleCache",
    )

    CACHE_DEFAULT_TIMEOUT = env(
        "CACHE_DEFAULT_TIMEOUT",
        300,
        int,
    )

    # --------------------------------------------------------
    # SEGURANÇA HTTP
    # --------------------------------------------------------

    SEND_FILE_MAX_AGE_DEFAULT = timedelta(
        hours=1
    )

    # --------------------------------------------------------
    # FEATURE FLAGS
    # --------------------------------------------------------

    ENABLE_DEVICE_API = env(
        "ENABLE_DEVICE_API",
        True,
        bool,
    )

    ENABLE_ATTENDANCE = env(
        "ENABLE_ATTENDANCE",
        True,
        bool,
    )

    ENABLE_NOTIFICATIONS = env(
        "ENABLE_NOTIFICATIONS",
        True,
        bool,
    )

    ENABLE_REPORTS = env(
        "ENABLE_REPORTS",
        True,
        bool,
    )

    ENABLE_AUDIT_LOG = env(
        "ENABLE_AUDIT_LOG",
        True,
        bool,
    )

    # --------------------------------------------------------
    # MÉTODOS
    # --------------------------------------------------------

    @classmethod
    def validate(cls) -> None:
        """
        Valida configurações críticas.
        """

        if cls.APP_ENV == "production":

            if cls.SECRET_KEY in {
                "",
                "CHANGE-ME-IN-PRODUCTION",
            }:
                raise RuntimeError(
                    "SECRET_KEY não configurada para produção."
                )

            if cls.SECURITY_PASSWORD_SALT in {
                "",
                "CHANGE-ME-PASSWORD-SALT",
            }:
                raise RuntimeError(
                    "SECURITY_PASSWORD_SALT não configurada."
                )

            if not cls.SQLALCHEMY_DATABASE_URI:
                raise RuntimeError(
                    "DATABASE_URL não configurada."
                )

    @classmethod
    def ensure_directories(cls) -> None:
        """
        Cria diretórios necessários.
        """

        cls.UPLOAD_FOLDER.mkdir(
            parents=True,
            exist_ok=True,
        )

        Path(
            cls.LOG_FILE
        ).parent.mkdir(
            parents=True,
            exist_ok=True,
        )


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    TESTING = True
    DEBUG = False

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///:memory:"
    )

    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config() -> type[Config]:
    """
    Retorna a configuração correspondente
    ao ambiente atual.
    """

    environment = (
        os.getenv(
            "APP_ENV",
            "development",
        )
        .strip()
        .lower()
    )

    config_class = CONFIG_MAP.get(
        environment,
        DevelopmentConfig,
    )

    config_class.validate()
    config_class.ensure_directories()

    return config_class


