from __future__ import annotations

from datetime import datetime

from database import db


class Permission(db.Model):
    __tablename__ = "permissions"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
    )

    code = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    description = db.Column(
        db.String(255),
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

    users = db.relationship(
        "User",
        secondary="user_permissions",
        back_populates="permissions",
    )

    def __repr__(self):
        return (
            f"<Permission "
            f"id={self.id} "
            f"code={self.code!r}>"
        )


user_permissions = db.Table(
    "user_permissions",

    db.Column(
        "user_id",
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),

    db.Column(
        "permission_id",
        db.Integer,
        db.ForeignKey(
            "permissions.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    ),
)