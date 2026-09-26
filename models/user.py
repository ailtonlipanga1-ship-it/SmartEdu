from __future__ import annotations

from datetime import datetime

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from database import db


class User(db.Model):
    __tablename__ = "users"

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

    username = db.Column(
        db.String(80),
        nullable=False,
        index=True,
    )

    email = db.Column(
        db.String(150),
        nullable=False,
        index=True,
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False,
    )

    first_name = db.Column(
        db.String(100),
        nullable=False,
    )

    last_name = db.Column(
        db.String(100),
        nullable=False,
    )

    role = db.Column(
        db.String(30),
        nullable=False,
        default="user",
    )

    active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
    )

    verified = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    failed_login_attempts = db.Column(
        db.Integer,
        default=0,
        nullable=False,
    )

    locked_until = db.Column(
        db.DateTime,
    )

    last_login_at = db.Column(
        db.DateTime,
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

    institution = db.relationship(
        "Institution",
        back_populates="users",
    )

    permissions = db.relationship(
        "Permission",
        secondary="user_permissions",
        back_populates="users",
    )

    audit_logs = db.relationship(
        "AuditLog",
        back_populates="user",
        lazy="dynamic",
    )

    notifications = db.relationship(
        "Notification",
        back_populates="user",
        lazy="dynamic",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "institution_id",
            "username",
            name="uq_user_institution_username",
        ),
        db.UniqueConstraint(
            "institution_id",
            "email",
            name="uq_user_institution_email",
        ),
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(
            password
        )

    def check_password(self, password: str) -> bool:
        return check_password_hash(
            self.password_hash,
            password,
        )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def has_permission(self, code: str) -> bool:
        return any(
            permission.code == code
            and permission.active
            for permission in self.permissions
        )

    def __repr__(self):
        return (
            f"<User "
            f"id={self.id} "
            f"username={self.username!r}>"
        )