from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, jsonify, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import get_config
from database import database_health, db, migrate


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour"],
    storage_uri="memory://",
)


def create_app(config_class=None):
    app = Flask(
        __name__,
        instance_relative_config=True,
    )

    config = config_class or get_config()
    app.config.from_object(config)

    config.ensure_directories()

    initialize_extensions(app)
    initialize_logging(app)
    register_teardown(app)
    register_core_routes(app)
    register_error_handlers(app)
    register_blueprints(app)

    return app


def initialize_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    origins = app.config.get(
        "CORS_ORIGINS",
        [],
    )

    if origins:
        CORS(
            app,
            origins=origins,
            supports_credentials=True,
        )


def initialize_logging(app):
    level = getattr(
        logging,
        str(
            app.config.get(
                "LOG_LEVEL",
                "INFO",
            )
        ).upper(),
        logging.INFO,
    )

    app.logger.setLevel(level)

    log_file = Path(
        app.config.get(
            "LOG_FILE",
            "logs/smartedu.log",
        )
    )

    log_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not any(
        isinstance(
            handler,
            RotatingFileHandler,
        )
        for handler in app.logger.handlers
    ):
        handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )

        handler.setLevel(level)

        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | "
                "%(name)s | %(message)s"
            )
        )

        app.logger.addHandler(handler)


def register_teardown(app):

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()


def register_core_routes(app):

    @app.get("/")
    def index():
        return render_template(
            "login.html"
        )

    @app.get("/health")
    @limiter.limit("30 per minute")
    def health():
        database = database_health()

        status = (
            "ok"
            if database["status"] == "healthy"
            else "degraded"
        )

        return jsonify(
            {
                "status": status,
                "application": app.config[
                    "APP_NAME"
                ],
                "version": app.config[
                    "APP_VERSION"
                ],
                "environment": app.config[
                    "APP_ENV"
                ],
                "database": database,
            }
        ), 200 if status == "ok" else 503

    @app.get("/api")
    def api_root():
        return jsonify(
            {
                "name": app.config["APP_NAME"],
                "version": app.config["API_VERSION"],
                "status": "online",
            }
        )

    @app.get("/api/v1/health")
    @limiter.limit("30 per minute")
    def api_health():
        database = database_health()

        return jsonify(
            {
                "success": True,
                "service": app.config[
                    "APP_NAME"
                ],
                "api_version": app.config[
                    "API_VERSION"
                ],
                "database": database,
            }
        )


def register_blueprints(app):
    blueprints = []

    modules = [
        ("routes.auth", "auth_bp"),
        ("routes.dashboard", "dashboard_bp"),
        ("routes.students", "students_bp"),
        ("routes.teachers", "teachers_bp"),
        ("routes.cards", "cards_bp"),
        ("routes.rooms", "rooms_bp"),
        ("routes.devices", "devices_bp"),
        ("routes.attendance", "attendance_bp"),
        ("routes.access", "access_bp"),
        ("routes.reports", "reports_bp"),
        ("routes.users", "users_bp"),
        ("routes.settings", "settings_bp"),
    ]

    for module_name, blueprint_name in modules:
        try:
            module = __import__(
                module_name,
                fromlist=[blueprint_name],
            )

            blueprint = getattr(
                module,
                blueprint_name,
            )

            blueprints.append(blueprint)

        except (ImportError, AttributeError):
            continue

    for blueprint in blueprints:
        app.register_blueprint(
            blueprint
        )


def register_error_handlers(app):

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify(
            {
                "success": False,
                "error": "bad_request",
                "message": "Pedido inválido.",
            }
        ), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify(
            {
                "success": False,
                "error": "unauthorized",
                "message": "Autenticação necessária.",
            }
        ), 401

    @app.errorhandler(403)
    def forbidden(error):
        if app.accept_mimetypes.best == "text/html":
            return render_template(
                "errors/403.html"
            ), 403

        return jsonify(
            {
                "success": False,
                "error": "forbidden",
                "message": "Acesso não autorizado.",
            }
        ), 403

    @app.errorhandler(404)
    def not_found(error):
        if app.accept_mimetypes.best == "text/html":
            return render_template(
                "errors/404.html"
            ), 404

        return jsonify(
            {
                "success": False,
                "error": "not_found",
                "message": "Recurso não encontrado.",
            }
        ), 404

    @app.errorhandler(429)
    def rate_limit(error):
        return jsonify(
            {
                "success": False,
                "error": "rate_limit_exceeded",
                "message": "Limite de pedidos excedido.",
            }
        ), 429

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception(
            "Erro interno da aplicação"
        )

        return jsonify(
            {
                "success": False,
                "error": "internal_server_error",
                "message": "Erro interno do servidor.",
            }
        ), 500


app = create_app()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=app.config["DEBUG"],
    )