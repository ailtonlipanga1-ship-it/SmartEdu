from __future__ import annotations

from datetime import datetime

from sqlalchemy import func

from database import db
from models.domain import AccessLog


ALLOWED_RESULTS = {
    "granted",
    "denied",
}

ALLOWED_DIRECTIONS = {
    "entry",
    "exit",
}


def access_log_to_dict(log: AccessLog) -> dict:
    return {
        "id": log.id,
        "institution_id": log.institution_id,
        "card_id": log.card_id,
        "student_id": log.student_id,
        "teacher_id": log.teacher_id,
        "device_id": log.device_id,
        "card_uid": log.card_uid,
        "device_code": log.device_code,
        "direction": log.direction,
        "result": log.result,
        "reason": log.reason,
        "timestamp": (
            log.timestamp.isoformat()
            if log.timestamp
            else None
        ),
        "metadata": log.metadata_json,
    }


def list_access_logs(
    institution_id=None,
    result=None,
    student_id=None,
    teacher_id=None,
    card_id=None,
    device_id=None,
    card_uid=None,
    direction=None,
    limit=None,
):
    query = AccessLog.query

    if institution_id is not None:
        query = query.filter(
            AccessLog.institution_id == institution_id
        )

    if result:
        query = query.filter(
            func.lower(AccessLog.result)
            == result.strip().lower()
        )

    if student_id is not None:
        query = query.filter(
            AccessLog.student_id == student_id
        )

    if teacher_id is not None:
        query = query.filter(
            AccessLog.teacher_id == teacher_id
        )

    if card_id is not None:
        query = query.filter(
            AccessLog.card_id == card_id
        )

    if device_id is not None:
        query = query.filter(
            AccessLog.device_id == device_id
        )

    if card_uid:
        query = query.filter(
            func.lower(AccessLog.card_uid)
            == card_uid.strip().lower()
        )

    if direction:
        query = query.filter(
            func.lower(AccessLog.direction)
            == direction.strip().lower()
        )

    query = query.order_by(
        AccessLog.timestamp.desc(),
        AccessLog.id.desc(),
    )

    if limit is not None:
        query = query.limit(limit)

    return query.all()


def get_access_log(log_id):
    return db.session.get(
        AccessLog,
        log_id,
    )


def create_access_log(
    institution_id,
    card_uid,
    result,
    direction="entry",
    reason=None,
    device_code=None,
    card_id=None,
    student_id=None,
    teacher_id=None,
    device_id=None,
    metadata=None,
    timestamp=None,
):
    normalized_result = str(
        result or ""
    ).strip().lower()

    if normalized_result not in ALLOWED_RESULTS:
        raise ValueError(
            "Resultado de acesso inválido."
        )

    normalized_direction = str(
        direction or "entry"
    ).strip().lower()

    if normalized_direction not in ALLOWED_DIRECTIONS:
        raise ValueError(
            "Direção de acesso inválida."
        )

    normalized_uid = str(
        card_uid or ""
    ).strip().upper()

    if not normalized_uid:
        raise ValueError(
            "UID RFID é obrigatório."
        )

    event_time = (
        timestamp
        if timestamp is not None
        else datetime.utcnow()
    )

    log = AccessLog(
        institution_id=institution_id,
        card_id=card_id,
        student_id=student_id,
        teacher_id=teacher_id,
        device_id=device_id,
        card_uid=normalized_uid,
        device_code=(
            str(device_code).strip()
            if device_code
            else None
        ),
        direction=normalized_direction,
        result=normalized_result,
        reason=reason,
        timestamp=event_time,
        metadata_json=metadata,
    )

    db.session.add(log)
    db.session.commit()
    db.session.refresh(log)

    return log


def access_statistics(institution_id=None):
    query = AccessLog.query

    if institution_id is not None:
        query = query.filter(
            AccessLog.institution_id == institution_id
        )

    total = query.count()

    granted = query.filter(
        AccessLog.result == "granted"
    ).count()

    denied = query.filter(
        AccessLog.result == "denied"
    ).count()

    approval_rate = (
        round(
            (granted / total) * 100,
            2,
        )
        if total
        else 0
    )

    return {
        "total": total,
        "granted": granted,
        "denied": denied,
        "approval_rate": approval_rate,
    }