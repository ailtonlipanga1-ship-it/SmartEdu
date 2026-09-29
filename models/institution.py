from __future__ import annotations

from datetime import datetime

from database import db


class Institution(db.Model):
    __tablename__ = "institutions"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.String(200),
        nullable=False,
    )

    code = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    email = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
    )

    phone = db.Column(
        db.String(50),
    )

    address = db.Column(
        db.String(255),
    )

    city = db.Column(
        db.String(100),
    )

    country = db.Column(
        db.String(100),
        nullable=False,
        default="Moçambique",
    )

    active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True,
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

    users = db.relationship(
        "User",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    students = db.relationship(
        "Student",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    teachers = db.relationship(
        "Teacher",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    rooms = db.relationship(
        "Room",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    devices = db.relationship(
        "Device",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    cards = db.relationship(
        "Card",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    access_logs = db.relationship(
        "AccessLog",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    schedules = db.relationship(
        "Schedule",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    audit_logs = db.relationship(
        "AuditLog",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return (
            f"<Institution "
            f"id={self.id!r} "
            f"code={self.code!r} "
            f"name={self.name!r}>"
        )