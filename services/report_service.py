from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import func

from database import db
from models.domain import (
    AccessLog,
    Attendance,
    Card,
    Device,
    Room,
    Student,
    Teacher,
)


def _scope(query, model, institution_id):
    if institution_id is not None and hasattr(model, "institution_id"):
        return query.filter(
            model.institution_id == institution_id
        )

    return query


def dashboard_statistics(institution_id=None):
    def count(model):
        query = model.query
        query = _scope(query, model, institution_id)
        return query.count()

    cards_query = Card.query
    cards_query = _scope(cards_query, Card, institution_id)

    active_cards = cards_query.filter(
        func.lower(Card.status) == "active"
    ).count()

    inactive_cards = cards_query.filter(
        func.lower(Card.status) != "active"
    ).count()

    access_query = AccessLog.query
    access_query = _scope(
        access_query,
        AccessLog,
        institution_id,
    )

    granted = access_query.filter(
        func.lower(AccessLog.result) == "granted"
    ).count()

    denied = access_query.filter(
        func.lower(AccessLog.result) == "denied"
    ).count()

    total_access = granted + denied

    approval_rate = (
        round((granted / total_access) * 100, 2)
        if total_access
        else 0
    )

    return {
        "students": count(Student),
        "teachers": count(Teacher),
        "rooms": count(Room),
        "devices": count(Device),
        "cards": count(Card),
        "active_cards": active_cards,
        "inactive_cards": inactive_cards,
        "access_logs": count(AccessLog),
        "attendance": count(Attendance),
        "granted": granted,
        "denied": denied,
        "approval_rate": approval_rate,
    }


def recent_access(institution_id=None, limit=10):
    query = AccessLog.query
    query = _scope(
        query,
        AccessLog,
        institution_id,
    )

    return (
        query
        .order_by(
            AccessLog.timestamp.desc(),
            AccessLog.id.desc(),
        )
        .limit(limit)
        .all()
    )


def device_status(institution_id=None):
    query = Device.query
    query = _scope(
        query,
        Device,
        institution_id,
    )

    devices = query.all()

    online = 0
    offline = 0
    maintenance = 0
    unknown = 0

    for device in devices:
        status = str(
            device.status or ""
        ).strip().lower()

        if status == "online":
            online += 1
        elif status == "offline":
            offline += 1
        elif status == "maintenance":
            maintenance += 1
        else:
            unknown += 1

    return {
        "total": len(devices),
        "online": online,
        "offline": offline,
        "maintenance": maintenance,
        "unknown": unknown,
        "devices": [
            {
                "id": device.id,
                "name": device.name,
                "type": device.type,
                "status": device.status,
                "location": device.location,
                "ip_address": device.ip_address,
                "mac_address": device.mac_address,
                "signal": device.signal,
                "heartbeat": device.heartbeat,
                "firmware": device.firmware,
                "last_seen": (
                    device.last_seen.isoformat()
                    if device.last_seen
                    else None
                ),
            }
            for device in devices
        ],
    }


def attendance_summary(institution_id=None):
    query = Attendance.query.join(Student)

    if institution_id is not None:
        query = query.filter(
            Student.institution_id == institution_id
        )

    records = query.all()

    return {
        "total": len(records),
        "present": sum(
            1
            for record in records
            if str(record.status).lower() == "present"
        ),
        "absent": sum(
            1
            for record in records
            if str(record.status).lower() == "absent"
        ),
        "late": sum(
            1
            for record in records
            if str(record.status).lower() == "late"
        ),
    }


def access_activity(
    institution_id=None,
    days=7,
):
    """
    Devolve actividade diária de acessos.

    O resultado mantém todos os dias do período,
    inclusive dias sem acessos.
    """

    days = max(1, min(int(days), 90))

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)

    query = AccessLog.query

    if institution_id is not None:
        query = query.filter(
            AccessLog.institution_id == institution_id
        )

    query = query.filter(
        AccessLog.timestamp >= datetime.combine(
            start_date,
            datetime.min.time(),
        )
    )

    logs = query.all()

    grouped = defaultdict(
        lambda: {
            "total": 0,
            "granted": 0,
            "denied": 0,
        }
    )

    for log in logs:
        if not log.timestamp:
            continue

        day = log.timestamp.date().isoformat()

        grouped[day]["total"] += 1

        if str(log.result).lower() == "granted":
            grouped[day]["granted"] += 1

        elif str(log.result).lower() == "denied":
            grouped[day]["denied"] += 1

    result = []

    for offset in range(days):
        current = start_date + timedelta(days=offset)
        key = current.isoformat()

        values = grouped[key]

        result.append(
            {
                "date": key,
                "total": values["total"],
                "granted": values["granted"],
                "denied": values["denied"],
                "label": current.strftime("%d/%m"),
            }
        )

    return result


def serialize_access(log):
    student_name = None
    teacher_name = None

    if log.student:
        student_name = log.student.name

    if log.teacher:
        teacher_name = log.teacher.name

    holder_name = student_name or teacher_name

    holder_type = None

    if student_name:
        holder_type = "student"

    elif teacher_name:
        holder_type = "teacher"

    return {
        "id": log.id,
        "card_id": log.card_id,
        "card_uid": log.card_uid,
        "device_id": log.device_id,
        "device_code": log.device_code,
        "direction": log.direction,
        "result": log.result,
        "reason": log.reason,
        "student_id": log.student_id,
        "teacher_id": log.teacher_id,
        "holder_name": holder_name,
        "holder_type": holder_type,
        "timestamp": (
            log.timestamp.isoformat()
            if log.timestamp
            else None
        ),
        "metadata": log.metadata_json,
    }


def dashboard_payload(institution_id=None):
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

    activity = access_activity(
        institution_id=institution_id,
        days=7,
    )

    attendance = attendance_summary(
        institution_id=institution_id
    )

    return {
        "statistics": statistics,
        "devices": devices,
        "attendance": attendance,
        "activity": activity,
        "recent_access": [
            serialize_access(log)
            for log in accesses
        ],
        "generated_at": datetime.utcnow().isoformat(),
    }