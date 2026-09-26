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
        db.String(150),
        nullable=False,
    )

    code = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    email = db.Column(
        db.String(150),
        unique=True,
    )

    phone = db.Column(
        db.String(30),
    )

    address = db.Column(
        db.String(255),
    )

    city = db.Column(
        db.String(100),
    )

    country = db.Column(
        db.String(100),
        default="Moçambique",
    )

    active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    users = db.relationship(
        "User",
        back_populates="institution",
        lazy="dynamic",
    )

    students = db.relationship(
        "Student",
        back_populates="institution",
        lazy="dynamic",
    )

    teachers = db.relationship(
        "Teacher",
        back_populates="institution",
        lazy="dynamic",
    )

    rooms = db.relationship(
        "Room",
        back_populates="institution",
        lazy="dynamic",
    )

    devices = db.relationship(
        "Device",
        back_populates="institution",
        lazy="dynamic",
    )

    cards = db.relationship(
        "Card",
        back_populates="institution",
        lazy="dynamic",
    )

    def __repr__(self):
        return (
            f"<Institution "
            f"id={self.id} "
            f"code={self.code!r}>"
        )