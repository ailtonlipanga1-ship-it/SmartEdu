from __future__ import annotations

from functools import wraps

from flask import jsonify, session

from database import db
from models.institution import Institution
from models.user import User


def get_current_user() -> User | None:
    user_id = session.get("user_id")

    if not user_id:
        return None

    user = db.session.get(User, user_id)

    if user is None:
        session.clear()
        return None

    if not user.active:
        session.clear()
        return None

    institution = db.session.get(
        Institution,
        user.institution_id,
    )

    if institution is None or not institution.active:
        session.clear()
        return None

    return user


def is_authenticated() -> bool:
    return get_current_user() is not None


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user = get_current_user()

        if user is None:
            return jsonify(
                {
                    "success": False,
                    "authenticated": False,
                    "message": "Autenticação necessária.",
                }
            ), 401

        return view_func(
            *args,
            **kwargs,
        )

    return wrapped_view


def permission_required(permission_code: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            user = get_current_user()

            if user is None:
                return jsonify(
                    {
                        "success": False,
                        "authenticated": False,
                        "message": "Autenticação necessária.",
                    }
                ), 401

            if user.role == "admin":
                return view_func(
                    *args,
                    **kwargs,
                )

            if not user.has_permission(permission_code):
                return jsonify(
                    {
                        "success": False,
                        "authenticated": True,
                        "message": "Permissão insuficiente.",
                    }
                ), 403

            return view_func(
                *args,
                **kwargs,
            )

        return wrapped_view

    return decorator


def roles_required(*roles: str):
    allowed_roles = {
        role.strip().lower()
        for role in roles
        if role and role.strip()
    }

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            user = get_current_user()

            if user is None:
                return jsonify(
                    {
                        "success": False,
                        "authenticated": False,
                        "message": "Autenticação necessária.",
                    }
                ), 401

            if user.role.lower() not in allowed_roles:
                return jsonify(
                    {
                        "success": False,
                        "authenticated": True,
                        "message": "Acesso não autorizado.",
                    }
                ), 403

            return view_func(
                *args,
                **kwargs,
            )

        return wrapped_view

    return decorator