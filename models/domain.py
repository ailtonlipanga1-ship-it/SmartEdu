from __future__ import annotations

from datetime import datetime, date

from database import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)

    institution_id = db.Column(
        db.Integer,
        db.ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    student_number = db.Column(
        db.String(100),
        nullable=False,
        index=True,
    )

    name = db.Column(
        db.String(200),
        nullable=False,
    )

    email = db.Column(
        db.String(255),
        nullable=False,
        index=True,
    )

    course = db.Column(
        db.String(200),
        nullable=False,
    )

    class_name = db.Column(
        db.String(100),
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="active",
    )

    rfid_card_id = db.Column(
        db.String(100),
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    institution = db.relationship(
        "Institution",
        back_populates="students",
    )

    attendance_records = db.relationship(
        "Attendance",
        back_populates="student",
        cascade="all, delete-orphan",
    )

    access_logs = db.relationship(
        "AccessLog",
        back_populates="student",
    )

    cards = db.relationship(
        "Card",
        primaryjoin=(
            "and_("
            "Student.id == foreign(Card.holder_id), "
            "Card.holder_type == 'student'"
            ")"
        ),
        viewonly=True,
    )

    __table_args__ = (
        db.UniqueConstraint(
            "institution_id",
            "student_number",
            name="uq_students_institution_number",
        ),
        db.UniqueConstraint(
            "institution_id",
            "email",
            name="uq_students_institution_email",
        ),
    )


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)

    institution_id = db.Column(
        db.Integer,
        db.ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    employee_number = db.Column(
        db.String(100),
        nullable=False,
        index=True,
    )

    name = db.Column(
        db.String(200),
        nullable=False,
    )

    email = db.Column(
        db.String(255),
        nullable=False,
        index=True,
    )

    department = db.Column(
        db.String(200),
        nullable=False,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="active",
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    institution = db.relationship(
        "Institution",
        back_populates="teachers",
    )

    access_logs = db.relationship(
        "AccessLog",
        back_populates="teacher",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "institution_id",
            "employee_number",
            name="uq_teachers_institution_employee",
        ),
        db.UniqueConstraint(
            "institution_id",
            "email",
            name="uq_teachers_institution_email",
        ),
    )


class Card(db.Model):
    __tablename__ = "cards"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    institution_id = db.Column(
        db.Integer,
        db.ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    uid = db.Column(
        db.String(100),
        nullable=False,
        index=True,
    )

    holder_type = db.Column(
        db.String(30),
        nullable=False,
    )

    holder_id = db.Column(
        db.String(100),
        nullable=False,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="active",
    )

    last_seen = db.Column(
        db.DateTime,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    institution = db.relationship(
        "Institution",
        back_populates="cards",
    )

    # IMPORTANTE:
    # Não utilizar cascade="all, delete-orphan" aqui.
    #
    # Os AccessLogs representam histórico permanente.
    # Ao eliminar um cartão, os eventos históricos devem
    # continuar na base de dados.
    access_logs = db.relationship(
        "AccessLog",
        back_populates="card",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "institution_id",
            "uid",
            name="uq_cards_institution_uid",
        ),
        db.Index(
            "ix_cards_holder",
            "holder_type",
            "holder_id",
        ),
    )


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    institution_id = db.Column(
        db.Integer,
        db.ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    code = db.Column(
        db.String(100),
        nullable=False,
        index=True,
    )

    name = db.Column(
        db.String(200),
        nullable=False,
    )

    building = db.Column(
        db.String(150),
    )

    floor = db.Column(
        db.String(50),
    )

    capacity = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    occupancy = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="active",
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    institution = db.relationship(
        "Institution",
        back_populates="rooms",
    )

    devices = db.relationship(
        "Device",
        back_populates="room",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "institution_id",
            "code",
            name="uq_rooms_institution_code",
        ),
    )


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    institution_id = db.Column(
        db.Integer,
        db.ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    room_id = db.Column(
        db.Integer,
        db.ForeignKey("rooms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name = db.Column(
        db.String(150),
        nullable=False,
    )

    type = db.Column(
        db.String(80),
        nullable=False,
    )

    location = db.Column(
        db.String(200),
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="offline",
    )

    ip_address = db.Column(
        db.String(45),
    )

    mac_address = db.Column(
        db.String(50),
        index=True,
    )

    signal = db.Column(
        db.Integer,
    )

    heartbeat = db.Column(
        db.Integer,
    )

    firmware = db.Column(
        db.String(100),
    )

    device_token = db.Column(
        db.String(255),
    )

    last_seen = db.Column(
        db.DateTime,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    institution = db.relationship(
        "Institution",
        back_populates="devices",
    )

    room = db.relationship(
        "Room",
        back_populates="devices",
    )

    access_logs = db.relationship(
        "AccessLog",
        back_populates="device",
    )


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    student_id = db.Column(
        db.Integer,
        db.ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    attendance_date = db.Column(
        db.Date,
        nullable=False,
        default=date.today,
        index=True,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="present",
    )

    check_in = db.Column(
        db.DateTime,
    )

    check_out = db.Column(
        db.DateTime,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    student = db.relationship(
        "Student",
        back_populates="attendance_records",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "student_id",
            "attendance_date",
            name="uq_attendance_student_date",
        ),
        db.Index(
            "ix_attendance_date_status",
            "attendance_date",
            "status",
        ),
    )


class AccessLog(db.Model):
    __tablename__ = "access_logs"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    institution_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "institutions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # O cartão pode ser eliminado sem destruir o histórico.
    card_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "cards.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # O estudante pode ser eliminado sem destruir o histórico.
    student_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "students.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # O professor pode ser eliminado sem destruir o histórico.
    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "teachers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # O dispositivo pode ser eliminado sem destruir o histórico.
    device_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "devices.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # Snapshot do UID.
    # Mesmo que o cartão seja eliminado posteriormente,
    # o UID continua registado no histórico.
    card_uid = db.Column(
        db.String(100),
        index=True,
    )

    # Snapshot do código do dispositivo.
    device_code = db.Column(
        db.String(100),
        index=True,
    )

    direction = db.Column(
        db.String(30),
        nullable=False,
        default="entry",
    )

    result = db.Column(
        db.String(30),
        nullable=False,
        default="granted",
        index=True,
    )

    reason = db.Column(
        db.String(255),
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    metadata_json = db.Column(
        db.JSON,
    )

    institution = db.relationship(
        "Institution",
        back_populates="access_logs",
    )

    card = db.relationship(
        "Card",
        back_populates="access_logs",
    )

    student = db.relationship(
        "Student",
        back_populates="access_logs",
    )

    teacher = db.relationship(
        "Teacher",
        back_populates="access_logs",
    )

    device = db.relationship(
        "Device",
        back_populates="access_logs",
    )


class Schedule(db.Model):
    __tablename__ = "schedules"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    institution_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "institutions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    room_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "rooms.id",
            ondelete="SET NULL",
        ),
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "teachers.id",
            ondelete="SET NULL",
        ),
    )

    title = db.Column(
        db.String(200),
        nullable=False,
    )

    course = db.Column(
        db.String(200),
    )

    class_name = db.Column(
        db.String(100),
    )

    weekday = db.Column(
        db.Integer,
        nullable=False,
    )

    start_time = db.Column(
        db.Time,
        nullable=False,
    )

    end_time = db.Column(
        db.Time,
        nullable=False,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="active",
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    institution = db.relationship(
        "Institution",
        back_populates="schedules",
    )

    room = db.relationship(
        "Room",
    )

    teacher = db.relationship(
        "Teacher",
    )


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    institution_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "institutions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    action = db.Column(
        db.String(100),
        nullable=False,
        index=True,
    )

    resource = db.Column(
        db.String(100),
        index=True,
    )

    resource_id = db.Column(
        db.String(100),
    )

    details = db.Column(
        db.JSON,
    )

    ip_address = db.Column(
        db.String(45),
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    user = db.relationship(
        "User",
        back_populates="audit_logs",
    )

    institution = db.relationship(
        "Institution",
    )


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title = db.Column(
        db.String(200),
        nullable=False,
    )

    message = db.Column(
        db.Text,
        nullable=False,
    )

    notification_type = db.Column(
        db.String(50),
        nullable=False,
        default="system",
    )

    read = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    read_at = db.Column(
        db.DateTime,
    )

    user = db.relationship(
        "User",
        back_populates="notifications",
    )