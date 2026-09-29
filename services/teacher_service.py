from database import db
from models.domain import Teacher

def list_teachers(institution_id=None, search=None):
    query = Teacher.query

    if institution_id:
        query = query.filter_by(institution_id=institution_id)

    if search:
        term = f"%{search}%"
        query = query.filter(
            db.or_(
                Teacher.name.ilike(term),
                Teacher.employee_number.ilike(term),
                Teacher.email.ilike(term),
                Teacher.department.ilike(term),
            )
        )

    return query.order_by(Teacher.name.asc()).all()

def get_teacher(teacher_id):
    return db.session.get(Teacher, teacher_id)

def create_teacher(
    institution_id,
    employee_number,
    name,
    email,
    department,
    status="active",
):
    teacher = Teacher(
        institution_id=institution_id,
        employee_number=employee_number,
        name=name,
        email=email,
        department=department,
        status=status,
    )

    db.session.add(teacher)
    db.session.commit()
    return teacher

def update_teacher(teacher_id, **data):
    teacher = get_teacher(teacher_id)

    if not teacher:
        return None

    allowed = {
        "employee_number",
        "name",
        "email",
        "department",
        "status",
    }

    for key, value in data.items():
        if key in allowed:
            setattr(teacher, key, value)

    db.session.commit()
    return teacher

def delete_teacher(teacher_id):
    teacher = get_teacher(teacher_id)

    if not teacher:
        return False

    db.session.delete(teacher)
    db.session.commit()
    return True
