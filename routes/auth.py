from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, session
from sqlalchemy import or_

from database import db
from models.institution import Institution
from models.user import User


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/v1/auth",
)


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

    max_attempts = 5

    if user.failed_login_attempts >= max_attempts:
        user.locked_until = (
            datetime.utcnow()
            + timedelta(minutes=15)
        )

    db.session.commit()


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
        payload.get("password")
        or ""
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
            db.func.lower(User.email) == identifier_lower,
            db.func.lower(User.username) == identifier_lower,
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
                "message": "Conta temporariamente bloqueada.",
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
                "message": "Utilizador inativo.",
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
                    "Instituição do utilizador não encontrada."
                ),
            }
        ), 403

    if not institution.active:
        return jsonify(
            {
                "success": False,
                "message": "Instituição inativa.",
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
                        "retry_after_seconds": 900,
                    },
                }
            ), 423

        remaining_attempts = max(
            0,
            5 - user.failed_login_attempts,
        )

        return jsonify(
            {
                "success": False,
                "message": "Credenciais inválidas.",
                "data": {
                    "remaining_attempts": remaining_attempts,
                },
            }
        ), 401

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()

    db.session.commit()

    session.clear()

    session["user_id"] = user.id
    session["authenticated"] = True
    session["institution_id"] = user.institution_id
    session["role"] = user.role

    session.permanent = True

    return jsonify(
        {
            "success": True,
            "authenticated": True,
            "message": "Autenticação efetuada com sucesso.",
            "data": _user_data(user),
        }
    ), 200


@auth_bp.post("/logout")
def logout():
    session.clear()

    return jsonify(
        {
            "success": True,
            "authenticated": False,
            "message": "Sessão terminada com sucesso.",
        }
    ), 200


@auth_bp.get("/me")
def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify(
            {
                "success": False,
                "authenticated": False,
                "message": "Utilizador não autenticado.",
            }
        ), 401

    user = db.session.get(
        User,
        user_id,
    )

    if user is None:
        session.clear()

        return jsonify(
            {
                "success": False,
                "authenticated": False,
                "message": "Sessão inválida.",
            }
        ), 401

    if not user.active:
        session.clear()

        return jsonify(
            {
                "success": False,
                "authenticated": False,
                "message": "Utilizador inativo.",
            }
        ), 403

    institution = db.session.get(
        Institution,
        user.institution_id,
    )

    if institution is None or not institution.active:
        session.clear()

        return jsonify(
            {
                "success": False,
                "authenticated": False,
                "message": (
                    "Instituição inativa ou inexistente."
                ),
            }
        ), 403

    if _is_locked(user):
        session.clear()

        return jsonify(
            {
                "success": False,
                "authenticated": False,
                "message": "Conta temporariamente bloqueada.",
            }
        ), 423

    return jsonify(
        {
            "success": True,
            "authenticated": True,
            "data": _user_data(user),
        }
    ), 200