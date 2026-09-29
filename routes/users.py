from **future** import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy import or_, func

from database import db
from models.institution import Institution
from models.user import User

users_bp = Blueprint(
"users",
**name**,
url_prefix="/api/v1/users",
)

@users_bp.get("/")
def list_users():
users = User.query.order_by(User.id.asc()).all()

data = []

for user in users:
    data.append(
        {
            "id": user.id,
            "institution_id": user.institution_id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "role": user.role,
            "active": user.active,
            "verified": user.verified,
            "failed_login_attempts": user.failed_login_attempts,
            "locked_until": (
                user.locked_until.isoformat()
                if user.locked_until
                else None
            ),
            "last_login_at": (
                user.last_login_at.isoformat()
                if user.last_login_at
                else None
            ),
            "created_at": (
                user.created_at.isoformat()
                if user.created_at
                else None
            ),
        }
    )

return jsonify(
    {
        "success": True,
        "count": len(data),
        "data": data,
    }
)

@users_bp.post("/")
def create_user():
payload = request.get_json(silent=True) or {}

required = [
    "username",
    "email",
    "password",
    "first_name",
    "last_name",
    "role",
    "institution_id",
]

missing = [
    field
    for field in required
    if payload.get(field) is None
    or str(payload.get(field)).strip() == ""
]

if missing:
    return jsonify(
        {
            "success": False,
            "message": "Dados obrigatórios em falta.",
            "missing": missing,
        }
    ), 400

password = str(payload["password"])

if len(password) < 8:
    return jsonify(
        {
            "success": False,
            "message": (
                "A palavra-passe deve ter "
                "pelo menos 8 caracteres."
            ),
        }
    ), 400

try:
    institution_id = int(
        payload["institution_id"]
    )
except (TypeError, ValueError):
    return jsonify(
        {
            "success": False,
            "message": "institution_id inválido.",
        }
    ), 400

institution = db.session.get(
    Institution,
    institution_id,
)

if not institution:
    return jsonify(
        {
            "success": False,
            "message": "Instituição não encontrada.",
        }
    ), 404

if not institution.active:
    return jsonify(
        {
            "success": False,
            "message": "A instituição está inactiva.",
        }
    ), 400

username = str(
    payload["username"]
).strip()

email = str(
    payload["email"]
).strip().lower()

existing_user = User.query.filter(
    or_(
        and_condition := (
            func.lower(User.username)
            == username.lower()
        ),
        func.lower(User.email)
        == email,
    )
).filter(
    User.institution_id == institution_id
).first()

if existing_user:
    return jsonify(
        {
            "success": False,
            "message": (
                "Username ou email já está "
                "associado a um utilizador."
            ),
        }
    ), 409

user = User(
    institution_id=institution_id,
    username=username,
    email=email,
    first_name=str(
        payload["first_name"]
    ).strip(),
    last_name=str(
        payload["last_name"]
    ).strip(),
    role=str(
        payload["role"]
    ).strip().lower(),
    active=bool(
        payload.get("active", True)
    ),
    verified=bool(
        payload.get("verified", False)
    ),
)

user.set_password(password)

db.session.add(user)
db.session.commit()

return jsonify(
    {
        "success": True,
        "message": "Utilizador criado com sucesso.",
        "data": {
            "id": user.id,
            "institution_id": user.institution_id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "role": user.role,
            "active": user.active,
            "verified": user.verified,
            "created_at": (
                user.created_at.isoformat()
                if user.created_at
                else None
            ),
        },
    }
), 201


@users_bp.get("/[int:user_id](int:user_id)")
def get_user(user_id: int):
user = db.session.get(
User,
user_id,
)

if not user:
    return jsonify(
        {
            "success": False,
            "message": "Utilizador não encontrado.",
        }
    ), 404

return jsonify(
    {
        "success": True,
        "data": {
            "id": user.id,
            "institution_id": user.institution_id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "role": user.role,
            "active": user.active,
            "verified": user.verified,
            "failed_login_attempts": user.failed_login_attempts,
            "locked_until": (
                user.locked_until.isoformat()
                if user.locked_until
                else None
            ),
            "last_login_at": (
                user.last_login_at.isoformat()
                if user.last_login_at
                else None
            ),
            "created_at": (
                user.created_at.isoformat()
                if user.created_at
                else None
            ),
            "updated_at": (
                user.updated_at.isoformat()
                if user.updated_at
                else None
            ),
        },
    }
)


@users_bp.patch("/[int:user_id](int:user_id)")
def update_user(user_id: int):
user = db.session.get(
User,
user_id,
)

if not user:
    return jsonify(
        {
            "success": False,
            "message": "Utilizador não encontrado.",
        }
    ), 404

payload = request.get_json(silent=True) or {}

if "username" in payload:
    username = str(
        payload["username"]
    ).strip()

    if not username:
        return jsonify(
            {
                "success": False,
                "message": "Username inválido.",
            }
        ), 400

    conflict = User.query.filter(
        func.lower(User.username)
        == username.lower(),
        User.institution_id
        == user.institution_id,
        User.id != user.id,
    ).first()

    if conflict:
        return jsonify(
            {
                "success": False,
                "message": "Username já utilizado.",
            }
        ), 409

    user.username = username

if "email" in payload:
    email = str(
        payload["email"]
    ).strip().lower()

    if not email:
        return jsonify(
            {
                "success": False,
                "message": "Email inválido.",
            }
        ), 400

    conflict = User.query.filter(
        func.lower(User.email)
        == email,
        User.institution_id
        == user.institution_id,
        User.id != user.id,
    ).first()

    if conflict:
        return jsonify(
            {
                "success": False,
                "message": "Email já utilizado.",
            }
        ), 409

    user.email = email

if "first_name" in payload:
    user.first_name = str(
        payload["first_name"]
    ).strip()

if "last_name" in payload:
    user.last_name = str(
        payload["last_name"]
    ).strip()

if "role" in payload:
    user.role = str(
        payload["role"]
    ).strip().lower()

if "active" in payload:
    user.active = bool(
        payload["active"]
    )

if "verified" in payload:
    user.verified = bool(
        payload["verified"]
    )

if "password" in payload:
    password = str(
        payload["password"]
    )

    if len(password) < 8:
        return jsonify(
            {
                "success": False,
                "message": (
                    "A palavra-passe deve ter "
                    "pelo menos 8 caracteres."
                ),
            }
        ), 400

    user.set_password(password)

db.session.commit()

return jsonify(
    {
        "success": True,
        "message": "Utilizador actualizado com sucesso.",
        "data": {
            "id": user.id,
            "institution_id": user.institution_id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "role": user.role,
            "active": user.active,
            "verified": user.verified,
        },
    }
)


@users_bp.delete("/[int:user_id](int:user_id)")
def delete_user(user_id: int):
user = db.session.get(
User,
user_id,
)


if not user:
    return jsonify(
        {
            "success": False,
            "message": "Utilizador não encontrado.",
        }
    ), 404

db.session.delete(user)
db.session.commit()

return jsonify(
    {
        "success": True,
        "message": "Utilizador removido com sucesso.",
    }
)

