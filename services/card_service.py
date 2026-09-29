from datetime import datetime

from database import db
from models.domain import Card, AccessLog

def list_cards(institution_id=None, status=None):
    query = Card.query

    if institution_id:
        query = query.filter_by(institution_id=institution_id)

    if status:
        query = query.filter_by(status=status)

    return query.order_by(Card.created_at.desc()).all()

def get_card(card_id):
    return db.session.get(Card, card_id)

def get_card_by_uid(uid):
    return Card.query.filter_by(uid=uid).first()

def register_card(institution_id, uid, holder_type, holder_id, status="active"):
    existing = get_card_by_uid(uid)

    if existing:
        raise ValueError("Cartão RFID já registado.")

    card = Card(
        institution_id=institution_id,
        uid=uid,
        holder_type=holder_type,
        holder_id=holder_id,
        status=status,
    )

    db.session.add(card)
    db.session.commit()
    return card

def update_card(card_id, **data):
    card = get_card(card_id)

    if not card:
        return None

    allowed = {
        "uid",
        "holder_type",
        "holder_id",
        "status",
    }

    for key, value in data.items():
        if key in allowed:
            setattr(card, key, value)

    db.session.commit()
    return card

def delete_card(card_id):
    card = get_card(card_id)

    if not card:
        return False

    db.session.delete(card)
    db.session.commit()
    return True

def scan_card(uid, device_code=None, direction="entry"):
    card = get_card_by_uid(uid)
    now = datetime.utcnow()

    if not card:
        log = AccessLog(
            card_uid=uid,
            device_code=device_code,
            direction=direction,
            result="denied",
            reason="Cartão não registado",
            timestamp=now,
        )

        db.session.add(log)
        db.session.commit()

        return {
            "granted": False,
            "reason": "Cartão não registado",
            "card": None,
        }

    if card.status != "active":
        log = AccessLog(
            institution_id=card.institution_id,
            card_id=card.id,
            card_uid=uid,
            device_code=device_code,
            direction=direction,
            result="denied",
            reason="Cartão inactivo",
            timestamp=now,
        )

        db.session.add(log)
        db.session.commit()

        return {
            "granted": False,
            "reason": "Cartão inactivo",
            "card": card,
        }

    card.last_seen = now

    log = AccessLog(
        institution_id=card.institution_id,
        card_id=card.id,
        card_uid=uid,
        device_code=device_code,
        direction=direction,
        result="granted",
        reason="Acesso autorizado",
        timestamp=now,
    )

    db.session.add(log)
    db.session.commit()

    return {
        "granted": True,
        "reason": "Acesso autorizado",
        "card": card,
    }
