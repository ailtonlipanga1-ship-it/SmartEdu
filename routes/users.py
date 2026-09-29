from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.memory_store import store


users_bp = Blueprint(
    "users",
    __name__,
    url_prefix="/api/v1/users",
)


@users_bp.get("/")
def list_users():
    users = store.list_collection("users")

    safe_users = []

    for user in users:
        item = dict(user)
        item.pop("password_hash", None)
        safe_users.append(item)

    return jsonify(
        {
            "success": True,
            "count": len(safe_users),
            "data": safe_users,
        }
    )


@users_bp.post("/")
def create_user():
    payload = request.get_json(silent=True) or {}

    required = [
        "name",
        "email",
        "role",
    ]

    missing = [
        field
        for field in required
        if not payload.get(field)
    ]

    if missing:
        return jsonify(
            {
                "success": False,
                "message": "Dados obrigatórios em falta.",
                "missing": missing,
            }
        ), 400

    user = store.create(
        "users",
        {
            "name": payload["name"],
            "email": payload["email"],
            "role": payload["role"],
            "status": payload.get(
                "status",
                "active",
            ),
            "password_hash": None,
        },
        "usr",
    )

    user.pop(
        "password_hash",
        None,
    )

    return jsonify(
        {
            "success": True,
            "message": "Utilizador criado.",
            "data": user,
        }
    ), 201


@users_bp.get("/<user_id>")
def get_user(user_id):
    user = store.get(
        "users",
        user_id,
    )

    if not user:
        return jsonify(
            {
                "success": False,
                "message": "Utilizador não encontrado.",
            }
        ), 404

    user.pop(
        "password_hash",
        None,
    )

    return jsonify(
        {
            "success": True,
            "data": user,
        }
    )


@users_bp.patch("/<user_id>")
def update_user(user_id):
    payload = request.get_json(silent=True) or {}

    user = store.update(
        "users",
        user_id,
        payload,
    )

    if not user:
        return jsonify(
            {
                "success": False,
                "message": "Utilizador não encontrado.",
            }
        ), 404

    user.pop(
        "password_hash",
        None,
    )

    return jsonify(
        {
            "success": True,
            "data": user,
        }
    )


@users_bp.delete("/<user_id>")
def delete_user(user_id):
    if not store.delete(
        "users",
        user_id,
    ):
        return jsonify(
            {
                "success": False,
                "message": "Utilizador não encontrado.",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "message": "Utilizador removido.",
        }
    )