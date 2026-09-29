from database import db
from models.domain import Student

def list_students(institution_id=None, search=None, status=None):
    query = Student.query
    if institution_id:
        query = query.filter_by(institution_id=institution_id)
    if status:
        query = query.filter_by(status=status)
    if search:
        term = f"%{search}%"
        query = query.filter(
            db.or_(
                Student.name.ilike(term),
                Student.student_number.ilike(term),
                Student.email.ilike(term),
            )
        )
    return query.order_by(Student.name.asc()).all()

def get_student(student_id):
    return db.session.get(Student, student_id)

def create_student(institution_id, student_number, name, email, course,
                   class_name=None, status="active", rfid_card_id=None):
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
    db.session.add(student)
    db.session.commit()
    return student

def update_student(student_id, **data):
    student = get_student(student_id)
    if not student:
        return None

    allowed = {
        "student_number",
        "name",
        "email",
        "course",
        "class_name",
        "status",
        "rfid_card_id",
    }

    for key, value in data.items():
        if key in allowed:
            setattr(student, key, value)

    db.session.commit()
    return student

def delete_student(student_id):
    student = get_student(student_id)
    if not student:
        return False

    db.session.delete(student)
    db.session.commit()
    return True
