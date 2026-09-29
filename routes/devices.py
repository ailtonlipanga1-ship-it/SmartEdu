from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request, session

from database import db
from models.domain import Device, Room
from services.auth_service import login_required


devices_bp = Blueprint(
    "devices",
    __name__,
    url_prefix="/api/v1/devices",
)


def current_institution_id():
    user = session.get("user")

    if isinstance(user, dict):
        return user.get("institution_id")

    return session.get("institution_id")


def device_to_dict(device: Device) -> dict:
    return {
        "id": device.id,
        "institution_id": device.institution_id,
        "room_id": device.room_id,
        "name": device.name,
        "type": device.type,
        "location": device.location,
        "status": device.status,
        "ip_address": device.ip_address,
        "mac_address": device.mac_address,
        "signal": device.signal,
        "heartbeat": device.heartbeat,
        "firmware": device.firmware,
        "has_device_token": bool(device.device_token),
        "last_seen": (
            device.last_seen.isoformat()
            if device.last_seen
            else None
        ),
        "created_at": (
            device.created_at.isoformat()
            if device.created_at
            else None
        ),
        "updated_at": (
            device.updated_at.isoformat()
            if device.updated_at
            else None
        ),
    }


@devices_bp.get("/")
@login_required
def list_devices():
    institution_id = current_institution_id()

    query = Device.query

    if institution_id is not None:
        query = query.filter(
            Device.institution_id == institution_id
        )

    devices = query.order_by(Device.id.asc()).all()

    return jsonify({
        "success": True,
        "data": [device_to_dict(device) for device in devices],
    })


@devices_bp.get("/<int:device_id>")
@login_required
def get_device(device_id):
    institution_id = current_institution_id()

    query = Device.query.filter(
        Device.id == device_id
    )

    if institution_id is not None:
        query = query.filter(
            Device.institution_id == institution_id
        )

    device = query.first()

    if not device:
        return jsonify({
            "success": False,
            "message": "Dispositivo não encontrado.",
        }), 404

    return jsonify({
        "success": True,
        "data": device_to_dict(device),
    })


@devices_bp.post("/")
@login_required
def create_device():
    institution_id = current_institution_id()

    if institution_id is None:
        return jsonify({
            "success": False,
            "message": "Instituição da sessão não encontrada.",
        }), 403

    payload = request.get_json(silent=True) or {}

    name = str(
        payload.get("name", "")
    ).strip()

    device_type = str(
        payload.get("type", "rfid_reader")
    ).strip()

    location = str(
        payload.get("location", "")
    ).strip()

    if not name:
        return jsonify({
            "success": False,
            "message": "Nome do dispositivo é obrigatório.",
        }), 400

    if not device_type:
        return jsonify({
            "success": False,
            "message": "Tipo do dispositivo é obrigatório.",
        }), 400

    room_id = payload.get("room_id")

    if room_id not in (None, ""):
        try:
            room_id = int(room_id)
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "message": "room_id inválido.",
            }), 400

        room = Room.query.filter(
            Room.id == room_id,
            Room.institution_id == institution_id,
        ).first()

        if not room:
            return jsonify({
                "success": False,
                "message": "Sala não encontrada nesta instituição.",
            }), 400
    else:
        room_id = None

    device = Device(
        institution_id=institution_id,
        room_id=room_id,
        name=name,
        type=device_type,
        location=location or None,
        status=str(
            payload.get("status", "offline")
        ).strip().lower() or "offline",
        ip_address=(
            str(payload.get("ip_address")).strip()
            if payload.get("ip_address")
            else None
        ),
        mac_address=(
            str(payload.get("mac_address")).strip().upper()
            if payload.get("mac_address")
            else None
        ),
        signal=payload.get("signal"),
        heartbeat=payload.get("heartbeat"),
        firmware=(
            str(payload.get("firmware")).strip()
            if payload.get("firmware")
            else None
        ),
        device_token=(
            str(payload.get("device_token")).strip()
            if payload.get("device_token")
            else None
        ),
    )

    db.session.add(device)
    db.session.commit()
    db.session.refresh(device)

    return jsonify({
        "success": True,
        "message": "Dispositivo criado com sucesso.",
        "data": device_to_dict(device),
    }), 201


@devices_bp.put("/<int:device_id>")
@login_required
def update_device(device_id):
    institution_id = current_institution_id()

    query = Device.query.filter(
        Device.id == device_id
    )

    if institution_id is not None:
        query = query.filter(
            Device.institution_id == institution_id
        )

    device = query.first()

    if not device:
        return jsonify({
            "success": False,
            "message": "Dispositivo não encontrado.",
        }), 404

    payload = request.get_json(silent=True) or {}

    if "name" in payload:
        name = str(payload.get("name", "")).strip()

        if not name:
            return jsonify({
                "success": False,
                "message": "Nome do dispositivo não pode ficar vazio.",
            }), 400

        device.name = name

    if "type" in payload:
        device.type = str(
            payload.get("type", "")
        ).strip()

    if "location" in payload:
        device.location = (
            str(payload.get("location")).strip()
            if payload.get("location") is not None
            else None
        )

    if "status" in payload:
        device.status = str(
            payload.get("status", "offline")
        ).strip().lower()

    if "ip_address" in payload:
        device.ip_address = (
            str(payload.get("ip_address")).strip()
            if payload.get("ip_address")
            else None
        )

    if "mac_address" in payload:
        device.mac_address = (
            str(payload.get("mac_address")).strip().upper()
            if payload.get("mac_address")
            else None
        )

    if "signal" in payload:
        device.signal = payload.get("signal")

    if "heartbeat" in payload:
        device.heartbeat = payload.get("heartbeat")

    if "firmware" in payload:
        device.firmware = (
            str(payload.get("firmware")).strip()
            if payload.get("firmware")
            else None
        )

    if "device_token" in payload:
        device.device_token = (
            str(payload.get("device_token")).strip()
            if payload.get("device_token")
            else None
        )

    if "room_id" in payload:
        room_id = payload.get("room_id")

        if room_id in (None, ""):
            device.room_id = None
        else:
            try:
                room_id = int(room_id)
            except (TypeError, ValueError):
                return jsonify({
                    "success": False,
                    "message": "room_id inválido.",
                }), 400

            room = Room.query.filter(
                Room.id == room_id,
                Room.institution_id == institution_id,
            ).first()

            if not room:
                return jsonify({
                    "success": False,
                    "message": "Sala não encontrada nesta instituição.",
                }), 400

            device.room_id = room_id

    db.session.commit()
    db.session.refresh(device)

    return jsonify({
        "success": True,
        "message": "Dispositivo atualizado com sucesso.",
        "data": device_to_dict(device),
    })


@devices_bp.delete("/<int:device_id>")
@login_required
def delete_device(device_id):
    institution_id = current_institution_id()

    query = Device.query.filter(
        Device.id == device_id
    )

    if institution_id is not None:
        query = query.filter(
            Device.institution_id == institution_id
        )

    device = query.first()

    if not device:
        return jsonify({
            "success": False,
            "message": "Dispositivo não encontrado.",
        }), 404

    db.session.delete(device)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Dispositivo removido com sucesso.",
    })