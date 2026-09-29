from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request, session
from sqlalchemy import func

from database import db
from models import Card, Student, Teacher
from services.access_service import create_access_log
from services.auth_service import login_required


cards_bp = Blueprint(
    "cards",
    __name__,
    url_prefix="/api/v1/cards",
)


ALLOWED_HOLDER_TYPES = {
    "student",
    "teacher",
}

ALLOWED_STATUSES = {
    "active",
    "inactive",
    "blocked",
}


def get_institution_id() -> int | None:
    institution_id = session.get("institution_id")

    if institution_id is None:
        return None

    try:
        return int(institution_id)
    except (TypeError, ValueError):
        return None


def card_to_dict(card: Card) -> dict:
    return {
        "id": card.id,
        "institution_id": card.institution_id,
        "uid": card.uid,
        "holder_type": card.holder_type,
        "holder_id": card.holder_id,
        "status": card.status,
        "last_seen": (
            card.last_seen.isoformat()
            if card.last_seen
            else None
        ),
        "created_at": (
            card.created_at.isoformat()
            if card.created_at
            else None
        ),
        "updated_at": (
            card.updated_at.isoformat()
            if card.updated_at
            else None
        ),
    }


def normalize_uid(value) -> str:
    return str(value or "").strip().upper()


def normalize_holder_type(value) -> str:
    return str(value or "student").strip().lower()


def normalize_status(value) -> str:
    return str(value or "active").strip().lower()


@cards_bp.get("/")
@login_required
def list_cards():
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "message": "Instituição não identificada.",
            }
        ), 400

    query = Card.query.filter(
        Card.institution_id == institution_id,
    )

    status = (
        normalize_status(
            request.args.get("status")
        )
        if request.args.get("status")
        else ""
    )

    if status:
        if status not in ALLOWED_STATUSES:
            return jsonify(
                {
                    "success": False,
                    "message": "Estado de cartão inválido.",
                    "allowed_statuses": sorted(
                        ALLOWED_STATUSES
                    ),
                }
            ), 400

        query = query.filter(
            func.lower(Card.status) == status
        )

    holder_type = request.args.get(
        "holder_type",
        "",
    ).strip().lower()

    if holder_type:
        if holder_type not in ALLOWED_HOLDER_TYPES:
            return jsonify(
                {
                    "success": False,
                    "message": "Tipo de titular inválido.",
                    "allowed_holder_types": sorted(
                        ALLOWED_HOLDER_TYPES
                    ),
                }
            ), 400

        query = query.filter(
            func.lower(Card.holder_type) == holder_type
        )

    cards = query.order_by(
        Card.id.desc()
    ).all()

    return jsonify(
        {
            "success": True,
            "count": len(cards),
            "data": [
                card_to_dict(card)
                for card in cards
            ],
        }
    )


@cards_bp.post("/register")
@login_required
def register_card():
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "message": "Instituição não identificada.",
            }
        ), 400

    payload = request.get_json(silent=True) or {}

    uid = normalize_uid(
        payload.get("uid")
    )

    if not uid:
        return jsonify(
            {
                "success": False,
                "message": "UID RFID é obrigatório.",
            }
        ), 400

    if len(uid) > 100:
        return jsonify(
            {
                "success": False,
                "message": "UID RFID excede o limite permitido.",
            }
        ), 400

    holder_type = normalize_holder_type(
        payload.get("holder_type")
    )

    if holder_type not in ALLOWED_HOLDER_TYPES:
        return jsonify(
            {
                "success": False,
                "message": "Tipo de titular inválido.",
                "allowed_holder_types": sorted(
                    ALLOWED_HOLDER_TYPES
                ),
            }
        ), 400

    holder_id = str(
        payload.get("holder_id") or ""
    ).strip()

    if not holder_id:
        return jsonify(
            {
                "success": False,
                "message": "holder_id é obrigatório.",
            }
        ), 400

    if len(holder_id) > 100:
        return jsonify(
            {
                "success": False,
                "message": "holder_id excede o limite permitido.",
            }
        ), 400

    existing = Card.query.filter(
        Card.institution_id == institution_id,
        func.lower(Card.uid) == uid.lower(),
    ).first()

    if existing:
        return jsonify(
            {
                "success": False,
                "message": "Este cartão já está registado.",
                "data": card_to_dict(existing),
            }
        ), 409

    card = Card(
        institution_id=institution_id,
        uid=uid,
        holder_type=holder_type,
        holder_id=holder_id,
        status="active",
        last_seen=None,
    )

    try:
        db.session.add(card)
        db.session.commit()
        db.session.refresh(card)

    except Exception:
        db.session.rollback()

        return jsonify(
            {
                "success": False,
                "message": "Não foi possível registar o cartão.",
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "message": "Cartão RFID registado.",
            "data": card_to_dict(card),
        }
    ), 201


@cards_bp.post("/scan")
@login_required
def scan_card():
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "message": "Instituição não identificada.",
            }
        ), 400

    payload = request.get_json(
        silent=True
    ) or {}

    uid = normalize_uid(
        payload.get("uid")
    )

    if not uid:
        return jsonify(
            {
                "success": False,
                "message": "UID RFID não informado.",
            }
        ), 400

    direction = str(
        payload.get(
            "direction",
            "entry",
        )
        or "entry"
    ).strip().lower()

    if direction not in {
        "entry",
        "exit",
    }:
        return jsonify(
            {
                "success": False,
                "message": "Direção de acesso inválida.",
                "allowed_directions": [
                    "entry",
                    "exit",
                ],
            }
        ), 400

    device_code = str(
        payload.get(
            "device_code",
            "RFID-GW-001",
        )
        or "RFID-GW-001"
    ).strip()

    if not device_code:
        device_code = "RFID-GW-001"

    card = Card.query.filter(
        Card.institution_id == institution_id,
        func.lower(Card.uid) == uid.lower(),
    ).first()

    if card is None:
        try:
            create_access_log(
                institution_id=institution_id,
                card_uid=uid,
                result="denied",
                direction=direction,
                reason="Cartão RFID não registado.",
                device_code=device_code,
                metadata={
                    "source": "rfid_scan",
                    "card_found": False,
                },
            )

        except Exception:
            db.session.rollback()

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Não foi possível guardar "
                        "o evento de acesso."
                    ),
                }
            ), 500

        return jsonify(
            {
                "success": False,
                "result": "denied",
                "message": "Cartão RFID não registado.",
                "uid": uid,
            }
        ), 403

    student_id = None
    teacher_id = None

    try:
        holder_id = int(card.holder_id)
    except (TypeError, ValueError):
        holder_id = None

    if card.holder_type == "student":
        student = Student.query.filter(
            Student.id == holder_id,
            Student.institution_id == institution_id,
        ).first()

        if student is not None:
            student_id = student.id

    elif card.holder_type == "teacher":
        teacher = Teacher.query.filter(
            Teacher.id == holder_id,
            Teacher.institution_id == institution_id,
        ).first()

        if teacher is not None:
            teacher_id = teacher.id

    if card.status != "active":
        try:
            create_access_log(
                institution_id=institution_id,
                card_uid=uid,
                result="denied",
                direction=direction,
                reason="Cartão RFID não autorizado.",
                device_code=device_code,
                card_id=card.id,
                student_id=student_id,
                teacher_id=teacher_id,
                metadata={
                    "source": "rfid_scan",
                    "card_found": True,
                    "card_status": card.status,
                    "holder_type": card.holder_type,
                    "holder_id": card.holder_id,
                },
            )

        except Exception:
            db.session.rollback()

            return jsonify(
                {
                    "success": False,
                    "message": (
                        "Não foi possível guardar "
                        "o evento de acesso."
                    ),
                }
            ), 500

        return jsonify(
            {
                "success": False,
                "result": "denied",
                "message": "Cartão RFID não autorizado.",
                "data": card_to_dict(card),
            }
        ), 403

    now = datetime.utcnow()

    card.last_seen = now

    try:
        create_access_log(
            institution_id=institution_id,
            card_uid=uid,
            result="granted",
            direction=direction,
            reason="Acesso autorizado.",
            device_code=device_code,
            card_id=card.id,
            student_id=student_id,
            teacher_id=teacher_id,
            metadata={
                "source": "rfid_scan",
                "card_found": True,
                "card_status": card.status,
                "holder_type": card.holder_type,
                "holder_id": card.holder_id,
            },
            timestamp=now,
        )

        db.session.refresh(card)

    except Exception:
        db.session.rollback()

        return jsonify(
            {
                "success": False,
                "message": (
                    "Não foi possível processar "
                    "o scan RFID."
                ),
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "result": "granted",
            "message": "Acesso autorizado.",
            "data": {
                "card": card_to_dict(card),
                "student_id": student_id,
                "teacher_id": teacher_id,
                "device_code": device_code,
                "direction": direction,
                "scanned_at": now.isoformat(),
            },
        }
    ), 200


@cards_bp.get("/<int:card_id>")
@login_required
def get_card(card_id: int):
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "message": "Instituição não identificada.",
            }
        ), 400

    card = Card.query.filter(
        Card.id == card_id,
        Card.institution_id == institution_id,
    ).first()

    if card is None:
        return jsonify(
            {
                "success": False,
                "message": "Cartão não encontrado.",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "data": card_to_dict(card),
        }
    )


@cards_bp.patch("/<int:card_id>")
@login_required
def update_card(card_id: int):
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "message": "Instituição não identificada.",
            }
        ), 400

    card = Card.query.filter(
        Card.id == card_id,
        Card.institution_id == institution_id,
    ).first()

    if card is None:
        return jsonify(
            {
                "success": False,
                "message": "Cartão não encontrado.",
            }
        ), 404

    payload = request.get_json(silent=True) or {}

    if "uid" in payload:
        uid = normalize_uid(
            payload.get("uid")
        )

        if not uid:
            return jsonify(
                {
                    "success": False,
                    "message": "UID RFID não pode estar vazio.",
                }
            ), 400

        if len(uid) > 100:
            return jsonify(
                {
                    "success": False,
                    "message": "UID RFID excede o limite permitido.",
                }
            ), 400

        duplicate = Card.query.filter(
            Card.institution_id == institution_id,
            func.lower(Card.uid) == uid.lower(),
            Card.id != card.id,
        ).first()

        if duplicate:
            return jsonify(
                {
                    "success": False,
                    "message": "Este UID RFID já pertence a outro cartão.",
                    "data": card_to_dict(duplicate),
                }
            ), 409

        card.uid = uid

    if "holder_type" in payload:
        holder_type = normalize_holder_type(
            payload.get("holder_type")
        )

        if holder_type not in ALLOWED_HOLDER_TYPES:
            return jsonify(
                {
                    "success": False,
                    "message": "Tipo de titular inválido.",
                    "allowed_holder_types": sorted(
                        ALLOWED_HOLDER_TYPES
                    ),
                }
            ), 400

        card.holder_type = holder_type

    if "holder_id" in payload:
        holder_id = str(
            payload.get("holder_id") or ""
        ).strip()

        if not holder_id:
            return jsonify(
                {
                    "success": False,
                    "message": "holder_id não pode estar vazio.",
                }
            ), 400

        if len(holder_id) > 100:
            return jsonify(
                {
                    "success": False,
                    "message": "holder_id excede o limite permitido.",
                }
            ), 400

        card.holder_id = holder_id

    if "status" in payload:
        status = normalize_status(
            payload.get("status")
        )

        if status not in ALLOWED_STATUSES:
            return jsonify(
                {
                    "success": False,
                    "message": "Estado de cartão inválido.",
                    "allowed_statuses": sorted(
                        ALLOWED_STATUSES
                    ),
                }
            ), 400

        card.status = status

    try:
        db.session.commit()
        db.session.refresh(card)

    except Exception:
        db.session.rollback()

        return jsonify(
            {
                "success": False,
                "message": "Não foi possível atualizar o cartão.",
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "message": "Cartão atualizado.",
            "data": card_to_dict(card),
        }
    )


@cards_bp.delete("/<int:card_id>")
@login_required
def delete_card(card_id: int):
    institution_id = get_institution_id()

    if institution_id is None:
        return jsonify(
            {
                "success": False,
                "message": "Instituição não identificada.",
            }
        ), 400

    card = Card.query.filter(
        Card.id == card_id,
        Card.institution_id == institution_id,
    ).first()

    if card is None:
        return jsonify(
            {
                "success": False,
                "message": "Cartão não encontrado.",
            }
        ), 404

    try:
        db.session.delete(card)
        db.session.commit()

    except Exception:
        db.session.rollback()

        return jsonify(
            {
                "success": False,
                "message": "Não foi possível remover o cartão.",
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "message": "Cartão removido.",
        }
    )