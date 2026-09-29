from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.memory_store import store


rooms_bp = Blueprint(
    "rooms",
    __name__,
    url_prefix="/api/v1/rooms",
)


@rooms_bp.get("/")
def list_rooms():
    rooms = store.list_collection("rooms")

    query = request.args.get("q", "").strip().lower()

    if query:
        rooms = [
            room
            for room in rooms
            if query in room["name"].lower()
            or query in room["code"].lower()
            or query in room["building"].lower()
        ]

    return jsonify(
        {
            "success": True,
            "count": len(rooms),
            "data": rooms,
        }
    )


@rooms_bp.post("/")
def create_room():
    payload = request.get_json(silent=True) or {}

    required = [
        "code",
        "name",
        "capacity",
    ]

    missing = [
        field
        for field in required
        if payload.get(field) in (
            None,
            "",
        )
    ]

    if missing:
        return jsonify(
            {
                "success": False,
                "message": "Dados obrigatórios em falta.",
                "missing": missing,
            }
        ), 400

    room = store.create(
        "rooms",
        {
            "code": payload["code"],
            "name": payload["name"],
            "building": payload.get(
                "building",
                "Bloco A",
            ),
            "floor": payload.get(
                "floor",
                0,
            ),
            "capacity": int(
                payload["capacity"]
            ),
            "occupancy": 0,
            "status": "online",
        },
        "room",
    )

    return jsonify(
        {
            "success": True,
            "message": "Sala criada.",
            "data": room,
        }
    ), 201


@rooms_bp.get("/<room_id>")
def get_room(room_id):
    room = store.get(
        "rooms",
        room_id,
    )

    if not room:
        return jsonify(
            {
                "success": False,
                "message": "Sala não encontrada.",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "data": room,
        }
    )


@rooms_bp.patch("/<room_id>")
def update_room(room_id):
    payload = request.get_json(silent=True) or {}

    room = store.update(
        "rooms",
        room_id,
        payload,
    )

    if not room:
        return jsonify(
            {
                "success": False,
                "message": "Sala não encontrada.",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "data": room,
        }
    )


@rooms_bp.delete("/<room_id>")
def delete_room(room_id):
    if not store.delete(
        "rooms",
        room_id,
    ):
        return jsonify(
            {
                "success": False,
                "message": "Sala não encontrada.",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "message": "Sala removida.",
        }
    )