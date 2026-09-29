from __future__ import annotations

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from sqlalchemy import text

from config import get_config
from database import db
from database.database import init_database


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOGGING
# ============================================================

def configure_logging(app: Flask) -> None:
    """Configura o sistema de logging do SmartEdu."""

    log_level_name = os.getenv(
        "SMARTEDU_LOG_LEVEL",
        app.config.get("LOG_LEVEL", "INFO"),
    ).upper()

    log_level = getattr(
        logging,
        log_level_name,
        logging.INFO,
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    )

    app.logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    app.logger.addHandler(console_handler)

    # Em ambientes onde o filesystem é persistente,
    # também mantemos o ficheiro local de log.
    try:
        file_handler = RotatingFileHandler(
            LOG_DIR / "smartedu.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )

        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)

        app.logger.addHandler(file_handler)

    except OSError:
        app.logger.warning(
            "Não foi possível activar o ficheiro de log."
        )

    app.logger.setLevel(log_level)

    logging.getLogger("werkzeug").setLevel(
        logging.INFO
    )


# ============================================================
# CORS
# ============================================================

def configure_cors(app: Flask) -> None:
    """Configura CORS para as APIs do SmartEdu."""

    allowed_origins = app.config.get(
        "CORS_ORIGINS",
        ["*"],
    )

    if not allowed_origins:
        allowed_origins = ["*"]

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": allowed_origins,
                "supports_credentials": True,
            }
        },
    )


# ============================================================
# RATE LIMITING
# ============================================================

def configure_rate_limiting(app: Flask) -> None:
    """Configura Flask-Limiter."""

    if not app.config.get(
        "RATELIMIT_ENABLED",
        True,
    ):
        app.logger.info(
            "Rate limiting desactivado."
        )
        return

    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address

        limiter = Limiter(
            key_func=get_remote_address,
            app=app,
            default_limits=[
                "300 per minute",
                "5000 per day",
            ],
            storage_uri=os.getenv(
                "RATELIMIT_STORAGE_URI",
                "memory://",
            ),
        )

        app.extensions["limiter"] = limiter

        app.logger.info(
            "Rate limiting activado."
        )

    except ImportError:
        app.logger.warning(
            "Flask-Limiter não está disponível."
        )


# ============================================================
# ERROR RESPONSE
# ============================================================

def error_response(
    message: str,
    status_code: int,
    *,
    code: str | None = None,
):
    """Cria respostas JSON padronizadas."""

    payload = {
        "success": False,
        "error": message,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if code:
        payload["code"] = code

    return jsonify(payload), status_code


# ============================================================
# BLUEPRINTS
# ============================================================

def register_blueprints(app: Flask) -> None:
    """Regista os módulos principais do SmartEdu."""

    from routes.auth import auth_bp
    from routes.students import students_bp
    from routes.teachers import teachers_bp
    from routes.cards import cards_bp
    from routes.access import access_bp
    from routes.attendance import attendance_bp
    from routes.reports import reports_bp
    from routes.dashboard import dashboard_bp
    from routes.monitoring import monitoring_bp
    from routes.device import device_bp
    from routes.devices import devices_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(teachers_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(access_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(device_bp)
    app.register_blueprint(devices_bp)

    app.logger.info(
        "Blueprints SmartEdu registados."
    )


# ============================================================
# CORE ROUTES
# ============================================================

def register_core_routes(app: Flask) -> None:
    """Regista as rotas centrais."""

    @app.get("/")
    def index():
        return render_template(
            "login.html"
        )

    @app.get("/login")
    def login_page():
        return render_template(
            "login.html"
        )

    @app.get("/health")
    def health():
        return jsonify(
            {
                "success": True,
                "status": "healthy",
                "application": "SmartEdu Access",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    @app.get("/api/health")
    def api_health():
        return jsonify(
            {
                "success": True,
                "status": "healthy",
                "service": "smartedu-api",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    @app.get("/api/v1/health")
    def api_v1_health():
        return jsonify(
            {
                "success": True,
                "status": "healthy",
                "service": "smartedu-api-v1",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    @app.get("/api/v1/system/status")
    def system_status():
        """Verifica aplicação e PostgreSQL."""

        database_status = "unknown"

        try:
            db.session.execute(
                text("SELECT 1")
            )

            database_status = "online"

        except Exception as exc:
            app.logger.error(
                "Falha na base de dados: %s",
                exc,
            )

            database_status = "offline"

        application_status = (
            "online"
            if database_status == "online"
            else "degraded"
        )

        return jsonify(
            {
                "success": True,
                "application": "SmartEdu Access",
                "status": application_status,
                "database": database_status,
                "database_engine": (
                    db.engine.name
                    if database_status == "online"
                    else None
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


# ============================================================
# SECURITY HEADERS
# ============================================================

def apply_security_headers(response):
    """Aplica headers HTTP de segurança."""

    response.headers.setdefault(
        "X-Content-Type-Options",
        "nosniff",
    )

    response.headers.setdefault(
        "X-Frame-Options",
        "SAMEORIGIN",
    )

    response.headers.setdefault(
        "Referrer-Policy",
        "strict-origin-when-cross-origin",
    )

    response.headers.setdefault(
        "Permissions-Policy",
        "camera=*, microphone=*, geolocation=()",
    )

    return response


# ============================================================
# MIDDLEWARE
# ============================================================

def register_middleware(app: Flask) -> None:
    """Regista middleware global."""

    @app.before_request
    def before_request():
        request.smartedu_started_at = datetime.utcnow()

    @app.after_request
    def after_request(response):
        response = apply_security_headers(
            response
        )

        started_at = getattr(
            request,
            "smartedu_started_at",
            None,
        )

        if started_at is not None:
            elapsed = (
                datetime.utcnow() - started_at
            ).total_seconds()

            response.headers[
                "X-SmartEdu-Response-Time"
            ] = f"{elapsed:.4f}s"

        return response


# ============================================================
# ERROR HANDLERS
# ============================================================

def register_error_handlers(app: Flask) -> None:
    """Regista tratamento centralizado de erros."""

    @app.errorhandler(400)
    def bad_request(error):
        return error_response(
            "Pedido inválido.",
            400,
            code="BAD_REQUEST",
        )

    @app.errorhandler(401)
    def unauthorized(error):
        return error_response(
            "Autenticação necessária.",
            401,
            code="UNAUTHORIZED",
        )

    @app.errorhandler(403)
    def forbidden(error):
        return error_response(
            "Acesso não autorizado.",
            403,
            code="FORBIDDEN",
        )

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return error_response(
                "Recurso não encontrado.",
                404,
                code="NOT_FOUND",
            )

        return error_response(
            "Recurso não encontrado.",
            404,
            code="NOT_FOUND",
        )

    @app.errorhandler(405)
    def method_not_allowed(error):
        return error_response(
            "Método HTTP não permitido.",
            405,
            code="METHOD_NOT_ALLOWED",
        )

    @app.errorhandler(429)
    def too_many_requests(error):
        return error_response(
            "Demasiadas solicitações. "
            "Tente novamente mais tarde.",
            429,
            code="RATE_LIMITED",
        )

    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.exception(
            "Erro interno do servidor."
        )

        try:
            db.session.rollback()
        except Exception:
            pass

        return error_response(
            "Erro interno do servidor.",
            500,
            code="INTERNAL_SERVER_ERROR",
        )

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        app.logger.exception(
            "Exceção não tratada: %s",
            error,
        )

        try:
            db.session.rollback()
        except Exception:
            pass

        return error_response(
            "Ocorreu um erro inesperado.",
            500,
            code="UNHANDLED_EXCEPTION",
        )


# ============================================================
# SESSION
# ============================================================

def configure_session(app: Flask) -> None:
    """Configura as sessões Flask."""

    app.config["SESSION_COOKIE_HTTPONLY"] = True

    app.config["SESSION_COOKIE_SAMESITE"] = (
        "Lax"
    )

    app.config["SESSION_COOKIE_SECURE"] = (
        app.config.get(
            "SESSION_COOKIE_SECURE",
            False,
        )
    )

    app.config["PERMANENT_SESSION_LIFETIME"] = (
        app.config.get(
            "PERMANENT_SESSION_LIFETIME",
            60 * 60 * 24 * 7,
        )
    )


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

def configure_application(app: Flask) -> None:
    """Configura parâmetros gerais."""

    app.config["JSON_SORT_KEYS"] = False

    app.config["SMARTEDU_VERSION"] = (
        "1.0.0"
    )


# ============================================================
# TEMPLATE CONTEXT
# ============================================================

def register_template_context(app: Flask) -> None:
    """Disponibiliza dados globais aos templates."""

    @app.context_processor
    def inject_smartedu_context():
        return {
            "smartedu_version": app.config.get(
                "SMARTEDU_VERSION",
                "1.0.0",
            ),
            "smartedu_name": "SmartEdu Access",
        }


# ============================================================
# APPLICATION FACTORY
# ============================================================

def create_app(config_class=None) -> Flask:
    """Cria e configura a aplicação Flask."""

    app = Flask(
        __name__,
        instance_relative_config=True,
    )

    # --------------------------------------------------------
    # CONFIG
    # --------------------------------------------------------

    if config_class is None:
        config_class = get_config()

    app.config.from_object(
        config_class
    )

    database_uri = app.config.get(
        "SQLALCHEMY_DATABASE_URI",
        "",
    )

    # --------------------------------------------------------
    # LOGGING
    # --------------------------------------------------------

    configure_logging(app)

    # --------------------------------------------------------
    # DATABASE IDENTIFICATION
    # --------------------------------------------------------

    if database_uri.startswith(
        "postgresql://"
    ):
        app.logger.info(
            "SMARTEDU DATABASE: POSTGRESQL"
        )

    elif database_uri.startswith(
        "sqlite://"
    ):
        app.logger.warning(
            "SMARTEDU DATABASE: SQLITE"
        )

    else:
        app.logger.error(
            "SMARTEDU DATABASE: DATABASE "
            "NÃO CONFIGURADA OU INVÁLIDA"
        )

    app.logger.info(
        "SmartEdu Access a iniciar..."
    )

    # --------------------------------------------------------
    # APPLICATION
    # --------------------------------------------------------

    configure_application(app)

    configure_session(app)

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    init_database(app)

    # --------------------------------------------------------
    # CORS
    # --------------------------------------------------------

    configure_cors(app)

    # --------------------------------------------------------
    # RATE LIMITING
    # --------------------------------------------------------

    configure_rate_limiting(app)

    # --------------------------------------------------------
    # MIDDLEWARE
    # --------------------------------------------------------

    register_middleware(app)

    # --------------------------------------------------------
    # CORE ROUTES
    # --------------------------------------------------------

    register_core_routes(app)

    # --------------------------------------------------------
    # BLUEPRINTS
    # --------------------------------------------------------

    register_blueprints(app)

    # --------------------------------------------------------
    # TEMPLATE CONTEXT
    # --------------------------------------------------------

    register_template_context(app)

    # --------------------------------------------------------
    # ERROR HANDLERS
    # --------------------------------------------------------

    register_error_handlers(app)

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    app.logger.info(
        "SmartEdu Access inicializado com sucesso."
    )

    return app


# ============================================================
# APPLICATION INSTANCE
# ============================================================

app = create_app()


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    host = os.getenv(
        "FLASK_HOST",
        "0.0.0.0",
    )

    port = int(
        os.getenv(
            "PORT",
            os.getenv(
                "FLASK_PORT",
                "5000",
            ),
        )
    )

    debug = (
        os.getenv(
            "FLASK_DEBUG",
            "false",
        ).lower()
        == "true"
    )

    app.logger.info(
        "SmartEdu iniciado em %s:%s",
        host,
        port,
    )

    app.run(
        host=host,
        port=port,
        debug=debug,
    )