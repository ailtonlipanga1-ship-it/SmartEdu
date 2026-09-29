from __future__ import annotations

from sqlalchemy import or_
from flask import Blueprint, jsonify, request, session

from database import db
from models import Student
from services.auth_service import login_required


students_bp = Blueprint(
    "students",
    __name__,
    url_prefix="/api/v1/students",
)


def student_to_dict(student: Student) -> dict:
    return {
        "id": student.id,
        "institution_id": student.institution_id,
        "student_number": student.student_number,
        "name": student.name,
        "email": student.email,
        "course": student.course,
        "class_name": student.class_name,
        "status": student.status,
        "rfid_card_id": student.rfid_card_id,
        "created_at": (
            student.created_at.isoformat()
            if student.created_at
            else None
        ),
        "updated_at": (
            student.updated_at.isoformat()
            if student.updated_at
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


@students_bp.get("/")
@login_required
def list_students():
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "error": "Instituição da sessão não encontrada.",
            }
        ), 403

    query = Student.query.filter(
        Student.institution_id == institution_id
    )

    search = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()

    if search:
        pattern = f"%{search}%"

        query = query.filter(
            or_(
                Student.student_number.ilike(pattern),
                Student.name.ilike(pattern),
                Student.email.ilike(pattern),
                Student.course.ilike(pattern),
                Student.class_name.ilike(pattern),
            )
        )

    if status:
        query = query.filter(
            Student.status == status
        )

    students = (
        query
        .order_by(Student.name.asc())
        .all()
    )

    return jsonify(
        {
            "success": True,
            "count": len(students),
            "students": [
                student_to_dict(student)
                for student in students
            ],
        }
    ), 200


@students_bp.get("/statistics")
@login_required
def student_statistics():
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "error": "Instituição da sessão não encontrada.",
            }
        ), 403

    base_query = Student.query.filter(
        Student.institution_id == institution_id
    )

    total = base_query.count()

    active = (
        base_query
        .filter(Student.status == "active")
        .count()
    )

    inactive = total - active

    return jsonify(
        {
            "success": True,
            "statistics": {
                "total": total,
                "active": active,
                "inactive": inactive,
            },
        }
    ), 200


@students_bp.get("/<int:student_id>")
@login_required
def get_student(student_id: int):
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "error": "Instituição da sessão não encontrada.",
            }
        ), 403

    student = (
        Student.query
        .filter(
            Student.id == student_id,
            Student.institution_id == institution_id,
        )
        .first()
    )

    if student is None:
        return jsonify(
            {
                "success": False,
                "error": "Estudante não encontrado.",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "student": student_to_dict(student),
        }
    ), 200


@students_bp.post("/")
@login_required
def create_student():
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "error": "Instituição da sessão não encontrada.",
            }
        ), 403

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            {
                "success": False,
                "error": "Dados inválidos.",
            }
        ), 400

    required = [
        "student_number",
        "name",
        "email",
        "course",
    ]

    missing = [
        field
        for field in required
        if not data.get(field)
    ]

    if missing:
        return jsonify(
            {
                "success": False,
                "error": "Campos obrigatórios em falta.",
                "missing": missing,
            }
        ), 400

    student_number = str(
        data["student_number"]
    ).strip()

    name = str(
        data["name"]
    ).strip()

    email = str(
        data["email"]
    ).strip()

    course = str(
        data["course"]
    ).strip()

    class_name = data.get("class_name")

    if class_name is not None:
        class_name = str(class_name).strip()

    status = str(
        data.get("status", "active")
    ).strip().lower()

    rfid_card_id = data.get("rfid_card_id")

    if not student_number:
        return jsonify(
            {
                "success": False,
                "error": "Número de estudante inválido.",
            }
        ), 400

    if not name:
        return jsonify(
            {
                "success": False,
                "error": "Nome do estudante é obrigatório.",
            }
        ), 400

    if not email:
        return jsonify(
            {
                "success": False,
                "error": "E-mail do estudante é obrigatório.",
            }
        ), 400

    if not course:
        return jsonify(
            {
                "success": False,
                "error": "Curso é obrigatório.",
            }
        ), 400

    allowed_statuses = {
        "active",
        "inactive",
    }

    if status not in allowed_statuses:
        return jsonify(
            {
                "success": False,
                "error": "Estado do estudante inválido.",
                "allowed": sorted(allowed_statuses),
            }
        ), 400

    existing = (
        Student.query
        .filter(
            Student.institution_id == institution_id,
            Student.student_number == student_number,
        )
        .first()
    )

    if existing:
        return jsonify(
            {
                "success": False,
                "error": "Número de estudante já existe nesta instituição.",
            }
        ), 409

    student = Student(
        institution_id=institution_id,
        student_number=student_number,
        name=name,
        email=email,
        course=course,
        class_name=class_name,
        status=status,
        rfid_card_id=rfid_card_id,
    )

    try:
        db.session.add(student)
        db.session.commit()

    except Exception:
        db.session.rollback()

        return jsonify(
            {
                "success": False,
                "error": "Não foi possível criar o estudante.",
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "message": "Estudante criado com sucesso.",
            "student": student_to_dict(student),
        }
    ), 201


@students_bp.patch("/<int:student_id>")
@login_required
def update_student(student_id: int):
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "error": "Instituição da sessão não encontrada.",
            }
        ), 403

    student = (
        Student.query
        .filter(
            Student.id == student_id,
            Student.institution_id == institution_id,
        )
        .first()
    )

    if student is None:
        return jsonify(
            {
                "success": False,
                "error": "Estudante não encontrado.",
            }
        ), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            {
                "success": False,
                "error": "Dados inválidos.",
            }
        ), 400

    allowed_fields = {
        "student_number",
        "name",
        "email",
        "course",
        "class_name",
        "status",
        "rfid_card_id",
    }

    updates = {
        field: data[field]
        for field in allowed_fields
        if field in data
    }

    if not updates:
        return jsonify(
            {
                "success": False,
                "error": "Nenhum campo válido para atualização.",
            }
        ), 400

    if "student_number" in updates:
        student_number = str(
            updates["student_number"]
        ).strip()

        if not student_number:
            return jsonify(
                {
                    "success": False,
                    "error": "Número de estudante inválido.",
                }
            ), 400

        duplicate = (
            Student.query
            .filter(
                Student.institution_id == institution_id,
                Student.student_number == student_number,
                Student.id != student.id,
            )
            .first()
        )

        if duplicate:
            return jsonify(
                {
                    "success": False,
                    "error": "Número de estudante já existe nesta instituição.",
                }
            ), 409

        updates["student_number"] = student_number

    if "name" in updates:
        updates["name"] = str(
            updates["name"]
        ).strip()

        if not updates["name"]:
            return jsonify(
                {
                    "success": False,
                    "error": "Nome do estudante é obrigatório.",
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
                    "error": "E-mail do estudante é obrigatório.",
                }
            ), 400

    if "course" in updates:
        updates["course"] = str(
            updates["course"]
        ).strip()

        if not updates["course"]:
            return jsonify(
                {
                    "success": False,
                    "error": "Curso é obrigatório.",
                }
            ), 400

    if "class_name" in updates and updates["class_name"] is not None:
        updates["class_name"] = str(
            updates["class_name"]
        ).strip()

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
                    "error": "Estado do estudante inválido.",
                    "allowed": [
                        "active",
                        "inactive",
                    ],
                }
            ), 400

    for field, value in updates.items():
        setattr(student, field, value)

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()

        return jsonify(
            {
                "success": False,
                "error": "Não foi possível atualizar o estudante.",
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "message": "Estudante atualizado com sucesso.",
            "student": student_to_dict(student),
        }
    ), 200


@students_bp.delete("/<int:student_id>")
@login_required
def delete_student(student_id: int):
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "error": "Instituição da sessão não encontrada.",
            }
        ), 403

    student = (
        Student.query
        .filter(
            Student.id == student_id,
            Student.institution_id == institution_id,
        )
        .first()
    )

    if student is None:
        return jsonify(
            {
                "success": False,
                "error": "Estudante não encontrado.",
            }
        ), 404

    try:
        db.session.delete(student)
        db.session.commit()

    except Exception:
        db.session.rollback()

        return jsonify(
            {
                "success": False,
                "error": "Não foi possível eliminar o estudante.",
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "message": "Estudante eliminado com sucesso.",
        }
    ), 200