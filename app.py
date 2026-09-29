from __future__ import annotations

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from config import Config
from database import db


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
        "INFO",
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

    file_handler = RotatingFileHandler(
        LOG_DIR / "smartedu.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )

    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    app.logger.handlers.clear()

    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)

    app.logger.setLevel(log_level)

    logging.getLogger("werkzeug").setLevel(
        logging.INFO
    )


# ============================================================
# CORS
# ============================================================

def configure_cors(app: Flask) -> None:
    """Configura CORS para as APIs do SmartEdu."""

    allowed_origins = os.getenv(
        "SMARTEDU_CORS_ORIGINS",
        "*",
    )

    if allowed_origins == "*":
        origins = "*"
    else:
        origins = [
            origin.strip()
            for origin in allowed_origins.split(",")
            if origin.strip()
        ]

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": origins,
                "supports_credentials": True,
            }
        },
    )


# ============================================================
# RATE LIMITING
# ============================================================

def configure_rate_limiting(app: Flask) -> None:
    """
    Configura Flask-Limiter quando a dependência estiver instalada.

    Caso Flask-Limiter não esteja disponível, a aplicação
    continua funcional.
    """

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
            "Rate limiting ativado."
        )

    except ImportError:
        app.logger.warning(
            "Flask-Limiter nao instalado. "
            "Rate limiting avancado desativado."
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
    """Cria respostas JSON padronizadas para erros de API."""

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
    """
    Regista os módulos principais do SmartEdu.

    Os imports ficam dentro desta função para reduzir
    problemas de importação circular.
    """

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
    """
    Regista as rotas centrais da aplicação.

    A raiz "/" é a entrada web do sistema.
    As rotas "/health" e "/api/*" permanecem como endpoints API.
    """

    @app.get("/")
    def index():
        """
        Página inicial do SmartEdu.

        Se o utilizador já estiver autenticado,
        a interface pode seguir directamente para o dashboard.
        """

        return render_template(
            "login.html"
        )

    @app.get("/login")
    def login_page():
        """Página web de autenticação."""

        return render_template(
            "login.html"
        )

    @app.get("/health")
    def health():
        """Health check principal."""

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
        """Health check da API."""

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
        """Health check da API v1."""

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
        """Verifica o estado interno da aplicação e da base de dados."""

        database_status = "unknown"

        try:
            db.session.execute(
                db.text("SELECT 1")
            )

            database_status = "online"

        except Exception as exc:
            app.logger.error(
                "Falha na verificacao da base de dados: %s",
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
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


# ============================================================
# SECURITY HEADERS
# ============================================================

app_headers_enabled = True


def apply_security_headers(response):
    """Aplica headers HTTP de segurança."""

    if not app_headers_enabled:
        return response

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
    """Regista middleware global da aplicação."""

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
        app.logger.warning(
            "400 %s %s",
            request.method,
            request.path,
        )

        return error_response(
            "Pedido invalido.",
            400,
            code="BAD_REQUEST",
        )

    @app.errorhandler(401)
    def unauthorized(error):
        return error_response(
            "Autenticacao necessaria.",
            401,
            code="UNAUTHORIZED",
        )

    @app.errorhandler(403)
    def forbidden(error):
        return error_response(
            "Acesso nao autorizado.",
            403,
            code="FORBIDDEN",
        )

    @app.errorhandler(404)
    def not_found(error):
        """
        Para páginas HTML inexistentes, mantém resposta JSON
        apenas quando a requisição é claramente de API.
        """

        if request.path.startswith("/api/"):
            return error_response(
                "Recurso nao encontrado.",
                404,
                code="NOT_FOUND",
            )

        return error_response(
            "Recurso nao encontrado.",
            404,
            code="NOT_FOUND",
        )

    @app.errorhandler(405)
    def method_not_allowed(error):
        return error_response(
            "Metodo HTTP nao permitido.",
            405,
            code="METHOD_NOT_ALLOWED",
        )

    @app.errorhandler(429)
    def too_many_requests(error):
        return error_response(
            "Demasiadas solicitacoes. "
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
            "Excecao nao tratada: %s",
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
    """Configura as sessões do Flask."""

    app.config.setdefault(
        "SESSION_COOKIE_HTTPONLY",
        True,
    )

    app.config.setdefault(
        "SESSION_COOKIE_SAMESITE",
        "Lax",
    )

    app.config.setdefault(
        "SESSION_COOKIE_SECURE",
        os.getenv(
            "SESSION_COOKIE_SECURE",
            "false",
        ).lower() == "true",
    )

    app.config.setdefault(
        "PERMANENT_SESSION_LIFETIME",
        60 * 60 * 12,
    )


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

def configure_application(app: Flask) -> None:
    """Configura parâmetros gerais da aplicação."""

    app.config.setdefault(
        "JSON_SORT_KEYS",
        False,
    )

    app.config.setdefault(
        "JSON_AS_ASCII",
        False,
    )

    app.config.setdefault(
        "SMARTEDU_VERSION",
        "1.0.0",
    )


# ============================================================
# DATABASE
# ============================================================

def initialize_database(app: Flask) -> None:
    """Inicializa SQLAlchemy."""

    db.init_app(app)

    app.logger.info(
        "SQLAlchemy inicializado."
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
    # Configuração
    # --------------------------------------------------------

    if config_class is None:
        config_class = Config

    app.config.from_object(
        config_class
    )

    configure_application(app)
    configure_session(app)

    # --------------------------------------------------------
    # Logging
    # --------------------------------------------------------

    configure_logging(app)

    app.logger.info(
        "Inicializando SmartEdu Access..."
    )

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    initialize_database(app)

    # --------------------------------------------------------
    # CORS
    # --------------------------------------------------------

    configure_cors(app)

    # --------------------------------------------------------
    # Rate limiting
    # --------------------------------------------------------

    configure_rate_limiting(app)

    # --------------------------------------------------------
    # Middleware
    # --------------------------------------------------------

    register_middleware(app)

    # --------------------------------------------------------
    # Core routes
    # --------------------------------------------------------

    register_core_routes(app)

    # --------------------------------------------------------
    # Blueprints
    # --------------------------------------------------------

    register_blueprints(app)

    # --------------------------------------------------------
    # Template context
    # --------------------------------------------------------

    register_template_context(app)

    # --------------------------------------------------------
    # Error handlers
    # --------------------------------------------------------

    register_error_handlers(app)

    # --------------------------------------------------------
    # Finalização
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
            "FLASK_PORT",
            "5000",
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