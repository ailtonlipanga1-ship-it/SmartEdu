from __future__ import annotations

from sqlalchemy import or_
from flask import Blueprint, jsonify, request, session

from database import db
from models import Teacher
from services.auth_service import login_required


teachers_bp = Blueprint(
    "teachers",
    __name__,
    url_prefix="/api/v1/teachers",
)


def teacher_to_dict(teacher: Teacher) -> dict:
    return {
        "id": teacher.id,
        "institution_id": teacher.institution_id,
        "employee_number": teacher.employee_number,
        "name": teacher.name,
        "email": teacher.email,
        "department": teacher.department,
        "status": teacher.status,
        "created_at": (
            teacher.created_at.isoformat()
            if teacher.created_at
            else None
        ),
        "updated_at": (
            teacher.updated_at.isoformat()
            if teacher.updated_at
            else None
        ),
    }


def get_institution_id() -> int | None:
    institution_id = session.get("institution_id")

    if institution_id is None:
        return None

    try:
        return int(institution_id)
    except (TypeError, ValueError):
        return None


@teachers_bp.get("/")
@login_required
def list_teachers():
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "error": "Instituição da sessão não encontrada.",
            }
        ), 403

    query = Teacher.query.filter(
        Teacher.institution_id == institution_id
    )

    search = request.args.get("q", "").strip()

    status = request.args.get("status", "").strip().lower()

    if search:
        pattern = f"%{search}%"

        query = query.filter(
            or_(
                Teacher.employee_number.ilike(pattern),
                Teacher.name.ilike(pattern),
                Teacher.email.ilike(pattern),
                Teacher.department.ilike(pattern),
            )
        )

    if status:
        query = query.filter(
            Teacher.status == status
        )

    teachers = (
        query
        .order_by(Teacher.name.asc())
        .all()
    )

    return jsonify(
        {
            "success": True,
            "count": len(teachers),
            "data": [
                teacher_to_dict(teacher)
                for teacher in teachers
            ],
        }
    ), 200


@teachers_bp.get("/statistics")
@login_required
def teacher_statistics():
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "error": "Instituição da sessão não encontrada.",
            }
        ), 403

    base_query = Teacher.query.filter(
        Teacher.institution_id == institution_id
    )

    total = base_query.count()

    active = (
        base_query
        .filter(Teacher.status == "active")
        .count()
    )

    inactive = total - active

    return jsonify(
        {
            "success": True,
            "data": {
                "total": total,
                "active": active,
                "inactive": inactive,
            },
        }
    ), 200


@teachers_bp.get("/<int:teacher_id>")
@login_required
def get_teacher(teacher_id: int):
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "error": "Instituição da sessão não encontrada.",
            }
        ), 403

    teacher = (
        Teacher.query
        .filter(
            Teacher.id == teacher_id,
            Teacher.institution_id == institution_id,
        )
        .first()
    )

    if teacher is None:
        return jsonify(
            {
                "success": False,
                "message": "Professor não encontrado.",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "data": teacher_to_dict(teacher),
        }
    ), 200


@teachers_bp.post("/")
@login_required
def create_teacher():
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "error": "Instituição da sessão não encontrada.",
            }
        ), 403

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(
            {
                "success": False,
                "message": "Dados inválidos.",
            }
        ), 400

    required = [
        "employee_number",
        "name",
        "email",
        "department",
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
                "message": "Campos obrigatórios em falta.",
                "missing": missing,
            }
        ), 400

    employee_number = str(
        payload["employee_number"]
    ).strip()

    name = str(
        payload["name"]
    ).strip()

    email = str(
        payload["email"]
    ).strip()

    department = str(
        payload["department"]
    ).strip()

    status = str(
        payload.get("status", "active")
    ).strip().lower()

    if not employee_number:
        return jsonify(
            {
                "success": False,
                "message": "Número de funcionário inválido.",
            }
        ), 400

    if not name:
        return jsonify(
            {
                "success": False,
                "message": "Nome do professor é obrigatório.",
            }
        ), 400

    if not email:
        return jsonify(
            {
                "success": False,
                "message": "E-mail do professor é obrigatório.",
            }
        ), 400

    if not department:
        return jsonify(
            {
                "success": False,
                "message": "Departamento é obrigatório.",
            }
        ), 400

    if status not in {"active", "inactive"}:
        return jsonify(
            {
                "success": False,
                "message": "Estado do professor inválido.",
                "allowed": [
                    "active",
                    "inactive",
                ],
            }
        ), 400

    existing_employee = (
        Teacher.query
        .filter(
            Teacher.institution_id == institution_id,
            Teacher.employee_number == employee_number,
        )
        .first()
    )

    if existing_employee:
        return jsonify(
            {
                "success": False,
                "message": "Número de funcionário já existe nesta instituição.",
            }
        ), 409

    existing_email = (
        Teacher.query
        .filter(
            Teacher.institution_id == institution_id,
            Teacher.email == email,
        )
        .first()
    )

    if existing_email:
        return jsonify(
            {
                "success": False,
                "message": "E-mail já existe nesta instituição.",
            }
        ), 409

    teacher = Teacher(
        institution_id=institution_id,
        employee_number=employee_number,
        name=name,
        email=email,
        department=department,
        status=status,
    )

    try:
        db.session.add(teacher)
        db.session.commit()

    except Exception:
        db.session.rollback()

        return jsonify(
            {
                "success": False,
                "message": "Não foi possível criar o professor.",
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "message": "Professor criado com sucesso.",
            "data": teacher_to_dict(teacher),
        }
    ), 201


@teachers_bp.patch("/<int:teacher_id>")
@login_required
def update_teacher(teacher_id: int):
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "error": "Instituição da sessão não encontrada.",
            }
        ), 403

    teacher = (
        Teacher.query
        .filter(
            Teacher.id == teacher_id,
            Teacher.institution_id == institution_id,
        )
        .first()
    )

    if teacher is None:
        return jsonify(
            {
                "success": False,
                "message": "Professor não encontrado.",
            }
        ), 404

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(
            {
                "success": False,
                "message": "Dados inválidos.",
            }
        ), 400

    allowed_fields = {
        "employee_number",
        "name",
        "email",
        "department",
        "status",
    }

    updates = {
        field: payload[field]
        for field in allowed_fields
        if field in payload
    }

    if not updates:
        return jsonify(
            {
                "success": False,
                "message": "Nenhum campo válido para atualização.",
            }
        ), 400

    if "employee_number" in updates:
        employee_number = str(
            updates["employee_number"]
        ).strip()

        if not employee_number:
            return jsonify(
                {
                    "success": False,
                    "message": "Número de funcionário inválido.",
                }
            ), 400

        duplicate = (
            Teacher.query
            .filter(
                Teacher.institution_id == institution_id,
                Teacher.employee_number == employee_number,
                Teacher.id != teacher.id,
            )
            .first()
        )

        if duplicate:
            return jsonify(
                {
                    "success": False,
                    "message": "Número de funcionário já existe nesta instituição.",
                }
            ), 409

        updates["employee_number"] = employee_number

    if "name" in updates:
        updates["name"] = str(
            updates["name"]
        ).strip()

        if not updates["name"]:
            return jsonify(
                {
                    "success": False,
                    "message": "Nome do professor é obrigatório.",
                }
            ), 400

    if "email" in updates:
        updates["email"] = str(
            updates["email"]
        ).strip()

        if not updates["email"]:
            return jsonify(
                {
                    "success": False,
                    "message": "E-mail do professor é obrigatório.",
                }
            ), 400

        duplicate = (
            Teacher.query
            .filter(
                Teacher.institution_id == institution_id,
                Teacher.email == updates["email"],
                Teacher.id != teacher.id,
            )
            .first()
        )

        if duplicate:
            return jsonify(
                {
                    "success": False,
                    "message": "E-mail já existe nesta instituição.",
                }
            ), 409

    if "department" in updates:
        updates["department"] = str(
            updates["department"]
        ).strip()

        if not updates["department"]:
            return jsonify(
                {
                    "success": False,
                    "message": "Departamento é obrigatório.",
                }
            ), 400

    if "status" in updates:
        updates["status"] = str(
            updates["status"]
        ).strip().lower()

        if updates["status"] not in {
            "active",
            "inactive",
        }:
            return jsonify(
                {
                    "success": False,
                    "message": "Estado do professor inválido.",
                    "allowed": [
                        "active",
                        "inactive",
                    ],
                }
            ), 400

    for field, value in updates.items():
        setattr(
            teacher,
            field,
            value,
        )

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()

        return jsonify(
            {
                "success": False,
                "message": "Não foi possível atualizar o professor.",
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "message": "Professor atualizado com sucesso.",
            "data": teacher_to_dict(teacher),
        }
    ), 200


@teachers_bp.delete("/<int:teacher_id>")
@login_required
def delete_teacher(teacher_id: int):
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "error": "Instituição da sessão não encontrada.",
            }
        ), 403

    teacher = (
        Teacher.query
        .filter(
            Teacher.id == teacher_id,
            Teacher.institution_id == institution_id,
        )
        .first()
    )

    if teacher is None:
        return jsonify(
            {
                "success": False,
                "message": "Professor não encontrado.",
            }
        ), 404

    try:
        db.session.delete(teacher)
        db.session.commit()

    except Exception:
        db.session.rollback()

        return jsonify(
            {
                "success": False,
                "message": "Não foi possível eliminar o professor.",
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "message": "Professor eliminado com sucesso.",
        }
    ), 200