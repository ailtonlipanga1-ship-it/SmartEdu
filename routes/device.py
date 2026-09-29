from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request

from database import db
from models.domain import Card, Device, Student, Teacher
from services.access_service import create_access_log


device_bp = Blueprint(
    "device",
    __name__,
    url_prefix="/api/v1/device",
)


def _get_device():
    device_code = (
        request.headers.get("X-Device-Code")
        or request.headers.get("X-Device-ID")
        or ""
    ).strip()

    device_token = (
        request.headers.get("X-Device-Token")
        or ""
    ).strip()

    if not device_code or not device_token:
        return None, "Credenciais do dispositivo são obrigatórias."

    device = Device.query.filter(
        Device.mac_address.isnot(None),
    ).filter(
        Device.name == device_code
    ).first()

    if device is None:
        device = Device.query.filter(
            Device.device_token == device_token
        ).first()

    if device is None:
        return None, "Dispositivo não encontrado."

    if device.device_token != device_token:
        return None, "Token do dispositivo inválido."

    return device, None


@device_bp.post("/scan")
def device_scan():
    device, error = _get_device()

    if error:
        return jsonify({
            "success": False,
            "message": error,
        }), 401

    payload = request.get_json(silent=True) or {}

    uid = str(
        payload.get("uid")
        or payload.get("card_uid")
        or ""
    ).strip().upper()

    direction = str(
        payload.get("direction")
        or "entry"
    ).strip().lower()

    if not uid:
        return jsonify({
            "success": False,
            "message": "UID RFID é obrigatório.",
        }), 400

    if direction not in {"entry", "exit"}:
        return jsonify({
            "success": False,
            "message": "Direção inválida.",
        }), 400

    now = datetime.utcnow()

    device.last_seen = now
    device.status = "online"

    if payload.get("firmware"):
        device.firmware = str(payload["firmware"])

    if payload.get("signal") is not None:
        try:
            device.signal = int(payload["signal"])
        except (TypeError, ValueError):
            pass

    if payload.get("heartbeat") is not None:
        try:
            device.heartbeat = int(payload["heartbeat"])
        except (TypeError, ValueError):
            pass

    card = Card.query.filter_by(
        institution_id=device.institution_id,
        uid=uid,
    ).first()

    holder_name = None
    holder_type = None
    student_id = None
    teacher_id = None
    card_id = None

    if card is None:
        result = "denied"
        reason = "Cartão RFID não cadastrado."

        metadata = {
            "source": "esp32_rc522",
            "card_found": False,
            "device_authenticated": True,
        }

    elif card.status != "active":
        result = "denied"
        reason = "Cartão RFID bloqueado."

        card_id = card.id
        holder_type = card.holder_type

        if card.holder_type == "student":
            try:
                student = db.session.get(
                    Student,
                    int(card.holder_id),
                )
            except (TypeError, ValueError):
                student = None

            if student:
                student_id = student.id
                holder_name = student.name

        elif card.holder_type == "teacher":
            try:
                teacher = db.session.get(
                    Teacher,
                    int(card.holder_id),
                )
            except (TypeError, ValueError):
                teacher = None

            if teacher:
                teacher_id = teacher.id
                holder_name = teacher.name

        metadata = {
            "source": "esp32_rc522",
            "card_found": True,
            "card_status": card.status,
            "holder_type": card.holder_type,
            "holder_id": card.holder_id,
            "device_authenticated": True,
        }

    else:
        result = "granted"
        reason = "Acesso autorizado."

        card_id = card.id
        card.last_seen = now
        holder_type = card.holder_type

        if card.holder_type == "student":
            try:
                student = db.session.get(
                    Student,
                    int(card.holder_id),
                )
            except (TypeError, ValueError):
                student = None

            if student:
                student_id = student.id
                holder_name = student.name

        elif card.holder_type == "teacher":
            try:
                teacher = db.session.get(
                    Teacher,
                    int(card.holder_id),
                )
            except (TypeError, ValueError):
                teacher = None

            if teacher:
                teacher_id = teacher.id
                holder_name = teacher.name

        metadata = {
            "source": "esp32_rc522",
            "card_found": True,
            "card_status": card.status,
            "holder_type": card.holder_type,
            "holder_id": card.holder_id,
            "device_authenticated": True,
        }

    log = create_access_log(
        institution_id=device.institution_id,
        card_uid=uid,
        result=result,
        direction=direction,
        reason=reason,
        device_code=device.name,
        card_id=card_id,
        student_id=student_id,
        teacher_id=teacher_id,
        device_id=device.id,
        metadata=metadata,
        timestamp=now,
    )

    db.session.commit()

    return jsonify({
        "success": True,
        "access": {
            "id": log.id,
            "uid": uid,
            "result": result,
            "reason": reason,
            "direction": direction,
            "holder_name": holder_name,
            "holder_type": holder_type,
            "student_id": student_id,
            "teacher_id": teacher_id,
            "device_id": device.id,
            "device_code": device.name,
            "timestamp": now.isoformat(),
        },
    }), 200


@device_bp.post("/heartbeat")
def device_heartbeat():
    device, error = _get_device()

    if error:
        return jsonify({
            "success": False,
            "message": error,
        }), 401

    payload = request.get_json(silent=True) or {}

    device.status = "online"
    device.last_seen = datetime.utcnow()

    if payload.get("firmware"):
        device.firmware = str(payload["firmware"])

    if payload.get("signal") is not None:
        try:
            device.signal = int(payload["signal"])
        except (TypeError, ValueError):
            pass

    if payload.get("heartbeat") is not None:
        try:
            device.heartbeat = int(payload["heartbeat"])
        except (TypeError, ValueError):
            pass

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Heartbeat recebido.",
        "device": {
            "id": device.id,
            "name": device.name,
            "status": device.status,
            "last_seen": (
                device.last_seen.isoformat()
                if device.last_seen
                else None
            ),
            "firmware": device.firmware,
            "signal": device.signal,
            "heartbeat": device.heartbeat,
        },
    }), 200