from database import db
from models.domain import Device

def list_devices(institution_id=None, status=None):
    query = Device.query

    if institution_id:
        query = query.filter_by(institution_id=institution_id)

    if status:
        query = query.filter_by(status=status)

    return query.order_by(Device.name.asc()).all()

def get_device(device_id):
    return db.session.get(Device, device_id)

def create_device(
    institution_id,
    name,
    type,
    location=None,
    status="online",
    ip_address=None,
    mac_address=None,
    room_id=None,
):
    device = Device(
        institution_id=institution_id,
        name=name,
        type=type,
        location=location,
        status=status,
        ip_address=ip_address,
        mac_address=mac_address,
        room_id=room_id,
    )

    db.session.add(device)
    db.session.commit()
    return device

def update_device(device_id, **data):
    device = get_device(device_id)

    if not device:
        return None

    allowed = {
        "room_id",
        "name",
        "type",
        "location",
        "status",
        "ip_address",
        "mac_address",
        "signal",
        "heartbeat",
        "firmware",
        "device_token",
        "last_seen",
    }

    for key, value in data.items():
        if key in allowed:
            setattr(device, key, value)

    db.session.commit()
    return device

def delete_device(device_id):
    device = get_device(device_id)

    if not device:
        return False

    db.session.delete(device)
    db.session.commit()
    return True
