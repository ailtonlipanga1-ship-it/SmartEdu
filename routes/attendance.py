from __future__ import annotations

from datetime import date, datetime

from flask import Blueprint, jsonify, request, session
from sqlalchemy import func

from database import db
from models.domain import Attendance, Student


attendance_bp = Blueprint(
    "attendance",
    __name__,
    url_prefix="/api/v1/attendance",
)


def get_institution_id():
    institution_id = session.get("institution_id")

    if institution_id is None:
        return None

    try:
        return int(institution_id)
    except (TypeError, ValueError):
        return None


def attendance_to_dict(record: Attendance):
    return {
        "id": record.id,
        "student_id": record.student_id,
        "attendance_date": (
            record.attendance_date.isoformat()
            if record.attendance_date
            else None
        ),
        "status": record.status,
        "check_in": (
            record.check_in.isoformat()
            if record.check_in
            else None
        ),
        "check_out": (
            record.check_out.isoformat()
            if record.check_out
            else None
        ),
        "created_at": (
            record.created_at.isoformat()
            if record.created_at
            else None
        ),
        "updated_at": (
            record.updated_at.isoformat()
            if record.updated_at
            else None
        ),
    }


def student_to_dict(student: Student):
    return {
        "id": student.id,
        "student_number": student.student_number,
        "name": student.name,
        "email": student.email,
        "course": student.course,
        "class_name": student.class_name,
        "status": student.status,
    }


@attendance_bp.get("/")
def list_attendance():
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify({
            "success": False,
            "message": "Instituição não identificada.",
        }), 401

    query = (
        Attendance.query
        .join(
            Student,
            Attendance.student_id == Student.id,
        )
        .filter(
            Student.institution_id == institution_id
        )
    )

    student_id = request.args.get("student_id")
    status = request.args.get("status")

    if student_id:
        try:
            student_id = int(student_id)
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "student_id inválido.",
            }), 400

        query = query.filter(
            Attendance.student_id == student_id
        )

    if status:
        query = query.filter(
            func.lower(Attendance.status)
            == status.strip().lower()
        )

    records = query.order_by(
        Attendance.attendance_date.desc(),
        Attendance.id.desc(),
    ).all()

    return jsonify({
        "success": True,
        "count": len(records),
        "data": [
            attendance_to_dict(record)
            for record in records
        ],
    })


@attendance_bp.post("/")
def register_attendance():
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify({
            "success": False,
            "message": "Instituição não identificada.",
        }), 401

    payload = request.get_json(silent=True) or {}

    student_id = payload.get("student_id")

    if student_id is None:
        return jsonify({
            "success": False,
            "message": "student_id é obrigatório.",
        }), 400

    try:
        student_id = int(student_id)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "student_id inválido.",
        }), 400

    student = (
        Student.query
        .filter(
            Student.id == student_id,
            Student.institution_id == institution_id,
        )
        .first()
    )

    if student is None:
        return jsonify({
            "success": False,
            "message": "Estudante não encontrado.",
        }), 404

    status = str(
        payload.get("status") or "present"
    ).strip().lower()

    allowed_statuses = {
        "present",
        "absent",
        "late",
        "excused",
    }

    if status not in allowed_statuses:
        return jsonify({
            "success": False,
            "message": "Status de presença inválido.",
        }), 400

    attendance_date = payload.get(
        "attendance_date"
    )

    if attendance_date is None:
        attendance_date = payload.get("date")

    if attendance_date:
        try:
            attendance_date = date.fromisoformat(
                str(attendance_date)
            )
        except ValueError:
            return jsonify({
                "success": False,
                "message": (
                    "attendance_date inválida. "
                    "Use YYYY-MM-DD."
                ),
            }), 400
    else:
        attendance_date = date.today()

    existing = (
        Attendance.query
        .filter(
            Attendance.student_id == student.id,
            Attendance.attendance_date
            == attendance_date,
        )
        .first()
    )

    if existing:
        return jsonify({
            "success": False,
            "message": (
                "Já existe um registo de presença "
                "para este estudante nesta data."
            ),
            "data": attendance_to_dict(existing),
        }), 409

    now = datetime.utcnow()

    record = Attendance(
        student_id=student.id,
        attendance_date=attendance_date,
        status=status,
        check_in=now if status != "absent" else None,
        check_out=None,
    )

    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)

    return jsonify({
        "success": True,
        "message": "Presença registada.",
        "data": attendance_to_dict(record),
    }), 201


@attendance_bp.get("/statistics")
def attendance_statistics():
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify({
            "success": False,
            "message": "Instituição não identificada.",
        }), 401

    base_query = (
        Attendance.query
        .join(
            Student,
            Attendance.student_id == Student.id,
        )
        .filter(
            Student.institution_id == institution_id
        )
    )

    total = base_query.count()

    present = base_query.filter(
        func.lower(Attendance.status) == "present"
    ).count()

    absent = base_query.filter(
        func.lower(Attendance.status) == "absent"
    ).count()

    late = base_query.filter(
        func.lower(Attendance.status) == "late"
    ).count()

    excused = base_query.filter(
        func.lower(Attendance.status) == "excused"
    ).count()

    attendance_rate = (
        round(
            (present / total) * 100,
            1,
        )
        if total
        else 0
    )

    return jsonify({
        "success": True,
        "data": {
            "total": total,
            "present": present,
            "absent": absent,
            "late": late,
            "excused": excused,
            "attendance_rate": attendance_rate,
        },
    })


@attendance_bp.get("/student/<int:student_id>")
def student_attendance(student_id):
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify({
            "success": False,
            "message": "Instituição não identificada.",
        }), 401

    student = (
        Student.query
        .filter(
            Student.id == student_id,
            Student.institution_id == institution_id,
        )
        .first()
    )

    if student is None:
        return jsonify({
            "success": False,
            "message": "Estudante não encontrado.",
        }), 404

    records = (
        Attendance.query
        .filter(
            Attendance.student_id == student.id
        )
        .order_by(
            Attendance.attendance_date.desc(),
            Attendance.id.desc(),
        )
        .all()
    )

    return jsonify({
        "success": True,
        "student": student_to_dict(student),
        "count": len(records),
        "data": [
            attendance_to_dict(record)
            for record in records
        ],
    })