from __future__ import annotations

from flask import Blueprint, jsonify, render_template, session

from services.report_service import (
    dashboard_statistics,
    recent_access,
    device_status,
)


dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard",
)


def current_institution_id():
    user = session.get("user")

    if isinstance(user, dict):
        return user.get("institution_id")

    return session.get("institution_id")


def serialize_access(log):
    return {
        "id": log.id,
        "card_uid": log.card_uid,
        "device_code": log.device_code,
        "direction": log.direction,
        "result": log.result,
        "reason": log.reason,
        "student_id": log.student_id,
        "teacher_id": log.teacher_id,
        "timestamp": (
            log.timestamp.isoformat()
            if log.timestamp
            else None
        ),
    }


@dashboard_bp.get("/")
def index():
    institution_id = current_institution_id()

    statistics = dashboard_statistics(
        institution_id=institution_id
    )

    devices = device_status(
        institution_id=institution_id
    )

    accesses = recent_access(
        institution_id=institution_id,
        limit=10,
    )

    dashboard = {
        "statistics": statistics,
        "devices": devices,
        "recent_access": [
            serialize_access(log)
            for log in accesses
        ],
    }

    return render_template(
        "dashboard/index.html",
        dashboard=dashboard,
    )


@dashboard_bp.get("/api")
def dashboard_api():
    institution_id = current_institution_id()

    statistics = dashboard_statistics(
        institution_id=institution_id
    )

    devices = device_status(
        institution_id=institution_id
    )

    accesses = recent_access(
        institution_id=institution_id,
        limit=10,
    )

    return jsonify(
        {
            "success": True,
            "data": {
                "statistics": statistics,
                "devices": devices,
                "recent_access": [
                    serialize_access(log)
                    for log in accesses
                ],
            },
        }
    )