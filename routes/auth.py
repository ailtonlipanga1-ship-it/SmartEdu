from __future__ import annotations

import re
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, session
from sqlalchemy import func, or_

from database import db
from models.institution import Institution
from models.user import User


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/v1/auth",
)


MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCK_MINUTES = 15
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def _user_data(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "name": user.full_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "institution_id": user.institution_id,
        "verified": user.verified,
        "active": user.active,
        "permissions": [
            permission.code
            for permission in user.permissions
            if permission.active
        ],
        "last_login_at": (
            user.last_login_at.isoformat()
            if user.last_login_at
            else None
        ),
    }


def _is_valid_email(email: str) -> bool:
    pattern = (
        r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
        r"@"
        r"[A-Za-z0-9-]+"
        r"(?:\.[A-Za-z0-9-]+)+$"
    )

    return re.fullmatch(pattern, email) is not None


def _is_valid_username(username: str) -> bool:
    if not 3 <= len(username) <= 80:
        return False

    return re.fullmatch(
        r"[A-Za-z0-9_.-]+",
        username,
    ) is not None


def _is_locked(user: User) -> bool:
    if user.locked_until is None:
        return False

    now = datetime.utcnow()

    if user.locked_until > now:
        return True

    user.locked_until = None
    user.failed_login_attempts = 0
    db.session.commit()

    return False


def _register_failed_login(user: User) -> None:
    user.failed_login_attempts += 1

    if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
        user.locked_until = (
            datetime.utcnow()
            + timedelta(minutes=LOGIN_LOCK_MINUTES)
        )

    db.session.commit()


def _clear_login_failures(user: User) -> None:
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()

    db.session.commit()


def _clear_session() -> None:
    session.clear()


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(
            {
                "success": False,
                "message": "Dados de registo inválidos.",
            }
        ), 400

    username = str(
        payload.get("username") or ""
    ).strip()

    email = str(
        payload.get("email") or ""
    ).strip().lower()

    first_name = str(
        payload.get("first_name") or ""
    ).strip()

    last_name = str(
        payload.get("last_name") or ""
    ).strip()

    password = str(
        payload.get("password") or ""
    )

    missing = []

    if not username:
        missing.append("username")

    if not email:
        missing.append("email")

    if not first_name:
        missing.append("first_name")

    if not last_name:
        missing.append("last_name")

    if not password:
        missing.append("password")

    if missing:
        return jsonify(
            {
                "success": False,
                "message": (
                    "Preencha todos os campos obrigatórios."
                ),
                "missing": missing,
            }
        ), 400

    if not _is_valid_username(username):
        return jsonify(
            {
                "success": False,
                "message": (
                    "Username inválido. Use entre 3 e "
                    "80 caracteres: letras, números, "
                    "ponto, hífen ou underscore."
                ),
            }
        ), 400

    if not _is_valid_email(email):
        return jsonify(
            {
                "success": False,
                "message": "Introduza um e-mail válido.",
            }
        ), 400

    if not 1 <= len(first_name) <= 100:
        return jsonify(
            {
                "success": False,
                "message": "Nome inválido.",
            }
        ), 400

    if not 1 <= len(last_name) <= 100:
        return jsonify(
            {
                "success": False,
                "message": "Apelido inválido.",
            }
        ), 400

    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify(
            {
                "success": False,
                "message": (
                    "A palavra-passe deve ter pelo menos "
                    f"{MIN_PASSWORD_LENGTH} caracteres."
                ),
            }
        ), 400

    if len(password) > MAX_PASSWORD_LENGTH:
        return jsonify(
            {
                "success": False,
                "message": (
                    "A palavra-passe não pode ter mais de "
                    f"{MAX_PASSWORD_LENGTH} caracteres."
                ),
            }
        ), 400

    existing_user = User.query.filter(
        or_(
            func.lower(User.email) == email,
            func.lower(User.username)
            == username.lower(),
        )
    ).first()

    if existing_user:
        if existing_user.email.lower() == email:
            message = "Este e-mail já está registado."
        else:
            message = "Este username já está registado."

        return jsonify(
            {
                "success": False,
                "message": message,
            }
        ), 409

    institution = (
        Institution.query
        .filter_by(active=True)
        .order_by(Institution.id.asc())
        .first()
    )

    if institution is None:
        return jsonify(
            {
                "success": False,
                "message": (
                    "Não existe uma instituição activa "
                    "disponível para criar a conta."
                ),
                "code": "INSTITUTION_NOT_CONFIGURED",
            }
        ), 503

    user = User(
        institution_id=institution.id,
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        role="user",
        active=True,
        verified=False,
        failed_login_attempts=0,
        locked_until=None,
        last_login_at=None,
    )

    user.set_password(password)

    db.session.add(user)

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()

        return jsonify(
            {
                "success": False,
                "message": (
                    "Não foi possível criar a conta."
                ),
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "message": "Conta criada com sucesso.",
            "authenticated": False,
            "data": _user_data(user),
        }
    ), 201


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(
            {
                "success": False,
                "message": "Dados de login inválidos.",
            }
        ), 400

    identifier = str(
        payload.get("email")
        or payload.get("username")
        or payload.get("identifier")
        or ""
    ).strip()

    password = str(
        payload.get("password") or ""
    )

    if not identifier:
        return jsonify(
            {
                "success": False,
                "message": (
                    "Username ou e-mail é obrigatório."
                ),
            }
        ), 400

    if not password:
        return jsonify(
            {
                "success": False,
                "message": "Palavra-passe é obrigatória.",
            }
        ), 400

    identifier_lower = identifier.lower()

    user = User.query.filter(
        or_(
            func.lower(User.email)
            == identifier_lower,
            func.lower(User.username)
            == identifier_lower,
        )
    ).first()

    if user is None:
        return jsonify(
            {
                "success": False,
                "message": "Credenciais inválidas.",
            }
        ), 401

    if _is_locked(user):
        remaining = max(
            0,
            int(
                (
                    user.locked_until
                    - datetime.utcnow()
                ).total_seconds()
            ),
        )

        return jsonify(
            {
                "success": False,
                "message": (
                    "Conta temporariamente bloqueada."
                ),
                "data": {
                    "locked": True,
                    "retry_after_seconds": remaining,
                },
            }
        ), 423

    if not user.active:
        return jsonify(
            {
                "success": False,
                "message": "Utilizador inactivo.",
            }
        ), 403

    institution = db.session.get(
        Institution,
        user.institution_id,
    )

    if institution is None:
        return jsonify(
            {
                "success": False,
                "message": (
                    "Instituição do utilizador "
                    "não encontrada."
                ),
            }
        ), 403

    if not institution.active:
        return jsonify(
            {
                "success": False,
                "message": "Instituição inactiva.",
            }
        ), 403

    if not user.check_password(password):
        _register_failed_login(user)

        if user.locked_until is not None:
            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Número máximo de tentativas "
                        "atingido. Conta bloqueada "
                        "temporariamente."
                    ),
                    "data": {
                        "locked": True,
                        "retry_after_seconds": (
                            LOGIN_LOCK_MINUTES * 60
                        ),
                    },
                }
            ), 423

        remaining_attempts = max(
            0,
            MAX_LOGIN_ATTEMPTS
            - user.failed_login_attempts,
        )

        return jsonify(
            {
                "success": False,
                "message": "Credenciais inválidas.",
                "data": {
                    "remaining_attempts": (
                        remaining_attempts
                    ),
                },
            }
        ), 401

    _clear_login_failures(user)
    _clear_session()

    session["user_id"] = user.id
    session["authenticated"] = True
    session["institution_id"] = user.institution_id
    session["role"] = user.role
    session.permanent = True

    return jsonify(
        {
            "success": True,
            "authenticated": True,
            "message": (
                "Autenticação efectuada "
                "com sucesso."
            ),
            "data": _user_data(user),
        }
    ), 200


@auth_bp.post("/logout")
def logout():
    _clear_session()

    return jsonify(
        {
            "success": True,
            "authenticated": False,
            "message": (
                "Sessão terminada com sucesso."
            ),
        }
    ), 200


@auth_bp.get("/me")
def current_user():
    user_id = session.get("user_id")
    authenticated = session.get(
        "authenticated",
        False,
    )

    if not user_id or not authenticated:
        return jsonify(
            {
                "success": False,
                "authenticated": False,
                "message": (
                    "Utilizador não autenticado."
                ),
            }
        ), 401

    user = db.session.get(
        User,
        user_id,
    )

    if user is None:
        _clear_session()

        return jsonify(
            {
                "success": False,
                "authenticated": False,
                "message": "Sessão inválida.",
            }
        ), 401

    if not user.active:
        _clear_session()

        return jsonify(
            {
                "success": False,
                "authenticated": False,
                "message": "Utilizador inactivo.",
            }
        ), 403

    institution = db.session.get(
        Institution,
        user.institution_id,
    )

    if (
        institution is None
        or not institution.active
    ):
        _clear_session()

        return jsonify(
            {
                "success": False,
                "authenticated": False,
                "message": (
                    "Instituição inactiva "
                    "ou inexistente."
                ),
            }
        ), 403

    if _is_locked(user):
        _clear_session()

        return jsonify(
            {
                "success": False,
                "authenticated": False,
                "message": (
                    "Conta temporariamente bloqueada."
                ),
            }
        ), 423

    return jsonify(
        {
            "success": True,
            "authenticated": True,
            "data": _user_data(user),
        }
    ), 200