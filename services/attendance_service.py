from database import db
from models.domain import Attendance, Student

def list_attendance(student_id=None, status=None, attendance_date=None):
    query = Attendance.query

    if student_id:
        query = query.filter_by(student_id=student_id)

    if status:
        query = query.filter_by(status=status)

    if attendance_date:
        query = query.filter_by(attendance_date=attendance_date)

    return query.order_by(Attendance.attendance_date.desc()).all()

def get_attendance(attendance_id):
    return db.session.get(Attendance, attendance_id)

def create_attendance(
    student_id,
    attendance_date,
    status="present",
    check_in=None,
    check_out=None,
):
    student = db.session.get(Student, student_id)

    if not student:
        raise ValueError("Estudante não encontrado.")

    existing = Attendance.query.filter_by(
        student_id=student_id,
        attendance_date=attendance_date,
    ).first()

    if existing:
        raise ValueError(
            "Já existe presença para este estudante nesta data."
        )

    record = Attendance(
        student_id=student_id,
        attendance_date=attendance_date,
        status=status,
        check_in=check_in,
        check_out=check_out,
    )

    db.session.add(record)
    db.session.commit()
    return record

def update_attendance(attendance_id, **data):
    record = get_attendance(attendance_id)

    if not record:
        return None

    allowed = {
        "attendance_date",
        "status",
        "check_in",
        "check_out",
    }

    for key, value in data.items():
        if key in allowed:
            setattr(record, key, value)

    db.session.commit()
    return record
