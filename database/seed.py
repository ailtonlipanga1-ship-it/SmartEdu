from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy import func

from app import app
from database import db
from models import (
    AccessLog,
    Attendance,
    AuditLog,
    Card,
    Device,
    Institution,
    Notification,
    Permission,
    Room,
    Schedule,
    Student,
    Teacher,
    User,
)


PERMISSIONS = [
    ("Administrador", "admin"),
    ("GestÃ£o de utilizadores", "users.manage"),
    ("GestÃ£o de estudantes", "students.manage"),
    ("GestÃ£o de professores", "teachers.manage"),
    ("GestÃ£o de cartÃµes RFID", "cards.manage"),
    ("GestÃ£o de dispositivos", "devices.manage"),
    ("GestÃ£o de salas", "rooms.manage"),
    ("GestÃ£o de presenÃ§as", "attendance.manage"),
    ("GestÃ£o de acessos", "access.manage"),
    ("VisualizaÃ§Ã£o de relatÃ³rios", "reports.view"),
    ("GestÃ£o de configuraÃ§Ãµes", "settings.manage"),
    ("Auditoria do sistema", "audit.view"),
]


def get_or_create(model, defaults=None, **filters):
    instance = (
        db.session.query(model)
        .filter_by(**filters)
        .first()
    )

    if instance:
        return instance, False

    values = dict(defaults or {})
    values.update(filters)

    instance = model(**values)
    db.session.add(instance)
    db.session.flush()

    return instance, True


def seed_institution():
    institution, created = get_or_create(
        Institution,
        code="SMEDU",
        defaults={
            "name": "SmartEdu Campus",
            "email": "admin@smartedu.local",
            "phone": "+258 84 000 0000",
            "address": "Campus SmartEdu",
            "city": "Maputo",
            "country": "MoÃ§ambique",
            "active": True,
        },
    )

    return institution, created


def seed_permissions():
    permissions = {}

    for name, code in PERMISSIONS:
        permission, _ = get_or_create(
            Permission,
            code=code,
            defaults={
                "name": name,
                "description": f"PermissÃ£o: {name}",
                "active": True,
            },
        )

        permission.name = name
        permission.description = f"PermissÃ£o: {name}"
        permission.active = True

        permissions[code] = permission

    db.session.flush()

    return permissions


def seed_admin(institution, permissions):
    admin = (
        db.session.query(User)
        .filter(
            User.institution_id == institution.id,
            User.email == "admin@smartedu.local",
        )
        .first()
    )

    if admin is None:
        admin = User(
            institution_id=institution.id,
            username="admin",
            email="admin@smartedu.local",
            first_name="Administrador",
            last_name="SmartEdu",
            role="admin",
            active=True,
            verified=True,
            failed_login_attempts=0,
        )

        admin.set_password("SmartEdu@2026")

        db.session.add(admin)
        db.session.flush()

    else:
        admin.username = "admin"
        admin.first_name = "Administrador"
        admin.last_name = "SmartEdu"
        admin.role = "admin"
        admin.active = True
        admin.verified = True
        admin.failed_login_attempts = 0
        admin.locked_until = None

        if not admin.password_hash:
            admin.set_password("SmartEdu@2026")

    for permission in permissions.values():
        if permission not in admin.permissions:
            admin.permissions.append(permission)

    db.session.flush()

    return admin


def seed_students(institution):
    data = [
        {
            "student_number": "STD001",
            "name": "Ana Cristina",
            "email": "ana.cristina@smartedu.local",
            "course": "AdministraÃ§Ã£o de Sistemas de Redes InformÃ¡ticas",
            "class_name": "ASRI-2A",
            "status": "active",
            "rfid_card_id": "RFID-001",
        },
        {
            "student_number": "STD002",
            "name": "Carlos Manuel",
            "email": "carlos.manuel@smartedu.local",
            "course": "AdministraÃ§Ã£o de Sistemas de Redes InformÃ¡ticas",
            "class_name": "ASRI-2A",
            "status": "active",
            "rfid_card_id": "RFID-002",
        },
        {
            "student_number": "STD003",
            "name": "Maria JosÃ©",
            "email": "maria.jose@smartedu.local",
            "course": "AdministraÃ§Ã£o de Sistemas de Redes InformÃ¡ticas",
            "class_name": "ASRI-2B",
            "status": "active",
            "rfid_card_id": "RFID-003",
        },
        {
            "student_number": "STD004",
            "name": "JoÃ£o Ernesto",
            "email": "joao.ernesto@smartedu.local",
            "course": "AdministraÃ§Ã£o de Sistemas de Redes InformÃ¡ticas",
            "class_name": "ASRI-2B",
            "status": "active",
            "rfid_card_id": "RFID-004",
        },
    ]

    students = []

    for item in data:
        student_number = item["student_number"]

        student, _ = get_or_create(
            Student,
            institution_id=institution.id,
            student_number=student_number,
            defaults={
                key: value
                for key, value in item.items()
                if key != "student_number"
            },
        )

        for key, value in item.items():
            setattr(student, key, value)

        students.append(student)

    db.session.flush()

    return students


def seed_teachers(institution):
    data = [
        {
            "employee_number": "DOC001",
            "name": "Pedro Alberto",
            "email": "pedro.alberto@smartedu.local",
            "department": "Tecnologias de InformaÃ§Ã£o",
            "status": "active",
        },
        {
            "employee_number": "DOC002",
            "name": "Lucas Fernando",
            "email": "lucas.fernando@smartedu.local",
            "department": "Redes e Sistemas",
            "status": "active",
        },
    ]

    teachers = []

    for item in data:
        employee_number = item["employee_number"]

        teacher, _ = get_or_create(
            Teacher,
            institution_id=institution.id,
            employee_number=employee_number,
            defaults={
                key: value
                for key, value in item.items()
                if key != "employee_number"
            },
        )

        for key, value in item.items():
            setattr(teacher, key, value)

        teachers.append(teacher)

    db.session.flush()

    return teachers


def seed_rooms(institution):
    data = [
        {
            "code": "LAB-01",
            "name": "LaboratÃ³rio de Redes",
            "building": "Bloco A",
            "floor": "1",
            "capacity": 30,
            "occupancy": 0,
            "status": "active",
        },
        {
            "code": "LAB-02",
            "name": "LaboratÃ³rio de ProgramaÃ§Ã£o",
            "building": "Bloco A",
            "floor": "1",
            "capacity": 25,
            "occupancy": 0,
            "status": "active",
        },
        {
            "code": "SALA-01",
            "name": "Sala de AdministraÃ§Ã£o",
            "building": "Bloco B",
            "floor": "1",
            "capacity": 40,
            "occupancy": 0,
            "status": "active",
        },
    ]

    rooms = []

    for item in data:
        code = item["code"]

        room, _ = get_or_create(
            Room,
            institution_id=institution.id,
            code=code,
            defaults={
                key: value
                for key, value in item.items()
                if key != "code"
            },
        )

        for key, value in item.items():
            setattr(room, key, value)

        rooms.append(room)

    db.session.flush()

    return rooms


def seed_devices(institution, rooms):
    room_map = {
        room.code: room
        for room in rooms
    }

    data = [
        {
            "name": "RFID Gateway LAB-01",
            "type": "rfid_reader",
            "location": "LaboratÃ³rio de Redes",
            "status": "online",
            "ip_address": "192.168.10.101",
            "mac_address": "AA:BB:CC:00:00:01",
            "signal": -48,
            "heartbeat": 30,
            "firmware": "1.0.0",
            "device_token": "demo-device-token-001",
            "room_code": "LAB-01",
        },
        {
            "name": "RFID Gateway LAB-02",
            "type": "rfid_reader",
            "location": "LaboratÃ³rio de ProgramaÃ§Ã£o",
            "status": "online",
            "ip_address": "192.168.10.102",
            "mac_address": "AA:BB:CC:00:00:02",
            "signal": -51,
            "heartbeat": 30,
            "firmware": "1.0.0",
            "device_token": "demo-device-token-002",
            "room_code": "LAB-02",
        },
        {
            "name": "Controlador Principal",
            "type": "gateway",
            "location": "Entrada Principal",
            "status": "online",
            "ip_address": "192.168.10.103",
            "mac_address": "AA:BB:CC:00:00:03",
            "signal": -43,
            "heartbeat": 15,
            "firmware": "1.0.0",
            "device_token": "demo-device-token-003",
            "room_code": "SALA-01",
        },
        {
            "name": "Leitor RFID Portaria",
            "type": "rfid_reader",
            "location": "Portaria",
            "status": "online",
            "ip_address": "192.168.10.104",
            "mac_address": "AA:BB:CC:00:00:04",
            "signal": -46,
            "heartbeat": 20,
            "firmware": "1.0.0",
            "device_token": "demo-device-token-004",
            "room_code": None,
        },
    ]

    devices = []

    for item in data:
        device, _ = get_or_create(
            Device,
            institution_id=institution.id,
            name=item["name"],
            defaults={
                "type": item["type"],
                "location": item["location"],
                "status": item["status"],
                "ip_address": item["ip_address"],
                "mac_address": item["mac_address"],
                "signal": item["signal"],
                "heartbeat": item["heartbeat"],
                "firmware": item["firmware"],
                "device_token": item["device_token"],
                "last_seen": datetime.utcnow(),
            },
        )

        device.room_id = (
            room_map[item["room_code"]].id
            if item["room_code"] and item["room_code"] in room_map
            else None
        )

        device.type = item["type"]
        device.location = item["location"]
        device.status = item["status"]
        device.ip_address = item["ip_address"]
        device.mac_address = item["mac_address"]
        device.signal = item["signal"]
        device.heartbeat = item["heartbeat"]
        device.firmware = item["firmware"]
        device.device_token = item["device_token"]
        device.last_seen = datetime.utcnow()

        devices.append(device)

    db.session.flush()

    return devices


def seed_cards(institution, students):
    cards = []

    for student in students:
        uid = student.rfid_card_id

        card, _ = get_or_create(
            Card,
            institution_id=institution.id,
            uid=uid,
            defaults={
                "holder_type": "student",
                "holder_id": str(student.id),
                "status": "active",
                "last_seen": datetime.utcnow(),
            },
        )

        card.holder_type = "student"
        card.holder_id = str(student.id)
        card.status = "active"

        cards.append(card)

    db.session.flush()

    return cards


def seed_attendance(students):
    today = date.today()

    for index, student in enumerate(students):
        existing = (
            db.session.query(Attendance)
            .filter_by(
                student_id=student.id,
                attendance_date=today,
            )
            .first()
        )

        if existing:
            continue

        check_in = datetime.combine(
            today,
            time(7, 40 + index),
        )

        db.session.add(
            Attendance(
                student_id=student.id,
                attendance_date=today,
                status="present",
                check_in=check_in,
            )
        )

    db.session.flush()


def seed_access_logs(institution, students, cards, devices):
    if not devices:
        return

    existing_count = (
        db.session.query(AccessLog)
        .filter_by(institution_id=institution.id)
        .count()
    )

    if existing_count > 0:
        return

    now = datetime.utcnow()

    for index, (student, card) in enumerate(
        zip(students, cards)
    ):
        device = devices[index % len(devices)]

        db.session.add(
            AccessLog(
                institution_id=institution.id,
                card_id=card.id,
                student_id=student.id,
                device_id=device.id,
                card_uid=card.uid,
                device_code=device.name,
                direction="entry",
                result="granted",
                reason="CartÃ£o vÃ¡lido",
                timestamp=now - timedelta(minutes=index * 7),
                metadata_json={
                    "source": "seed",
                    "reader": device.name,
                },
            )
        )

    db.session.add(
        AccessLog(
            institution_id=institution.id,
            card_uid="UNKNOWN-000",
            device_code=devices[0].name,
            direction="entry",
            result="denied",
            reason="CartÃ£o nÃ£o registado",
            timestamp=now - timedelta(minutes=35),
            metadata_json={
                "source": "seed",
            },
        )
    )

    db.session.flush()


def seed_schedule(institution, teachers, rooms):
    existing_count = (
        db.session.query(Schedule)
        .filter_by(institution_id=institution.id)
        .count()
    )

    if existing_count > 0:
        return

    db.session.add(
        Schedule(
            institution_id=institution.id,
            room_id=rooms[0].id,
            teacher_id=teachers[0].id,
            title="AdministraÃ§Ã£o de Sistemas de Redes",
            course="AdministraÃ§Ã£o de Sistemas de Redes InformÃ¡ticas",
            class_name="ASRI-2A",
            weekday=1,
            start_time=time(7, 30),
            end_time=time(9, 30),
            status="active",
        )
    )

    db.session.add(
        Schedule(
            institution_id=institution.id,
            room_id=rooms[1].id,
            teacher_id=teachers[1].id,
            title="ProgramaÃ§Ã£o Python",
            course="AdministraÃ§Ã£o de Sistemas de Redes InformÃ¡ticas",
            class_name="ASRI-2B",
            weekday=3,
            start_time=time(9, 30),
            end_time=time(11, 30),
            status="active",
        )
    )

    db.session.flush()


def seed_notification(admin):
    existing = (
        db.session.query(Notification)
        .filter_by(
            user_id=admin.id,
            title="SmartEdu inicializado",
        )
        .first()
    )

    if existing:
        return

    db.session.add(
        Notification(
            user_id=admin.id,
            title="SmartEdu inicializado",
            message="A plataforma SmartEdu foi inicializada correctamente.",
            notification_type="system",
            read=False,
        )
    )

    db.session.flush()


def seed_audit(admin, institution):
    existing = (
        db.session.query(AuditLog)
        .filter_by(
            user_id=admin.id,
            action="system.seed",
        )
        .first()
    )

    if existing:
        return

    db.session.add(
        AuditLog(
            user_id=admin.id,
            institution_id=institution.id,
            action="system.seed",
            resource="database",
            resource_id=str(institution.id),
            details={
                "message": "Base inicial do SmartEdu criada.",
                "source": "database.seed",
            },
        )
    )

    db.session.flush()


def table_count(table_name):
    table = db.metadata.tables[table_name]

    return db.session.execute(
        db.select(func.count()).select_from(table)
    ).scalar_one()


def seed():
    with app.app_context():
        print("=" * 60)
        print("SMARTEDU DATABASE SEED")
        print("=" * 60)

        try:
            db.create_all()

            institution, institution_created = seed_institution()

            permissions = seed_permissions()

            admin = seed_admin(
                institution,
                permissions,
            )

            students = seed_students(institution)

            teachers = seed_teachers(institution)

            rooms = seed_rooms(institution)

            devices = seed_devices(
                institution,
                rooms,
            )

            cards = seed_cards(
                institution,
                students,
            )

            seed_attendance(students)

            seed_access_logs(
                institution,
                students,
                cards,
                devices,
            )

            seed_schedule(
                institution,
                teachers,
                rooms,
            )

            seed_notification(admin)

            seed_audit(
                admin,
                institution,
            )

            db.session.commit()

            print()
            print("BASE DE DADOS CRIADA COM SUCESSO")
            print("-" * 60)
            print(
                f"InstituiÃ§Ã£o : {institution.name}"
            )
            print(
                f"Utilizador  : {admin.email}"
            )
            print("Password    : SmartEdu@2026")
            print(
                f"Estudantes  : {len(students)}"
            )
            print(
                f"Professores : {len(teachers)}"
            )
            print(
                f"Salas       : {len(rooms)}"
            )
            print(
                f"Dispositivos: {len(devices)}"
            )
            print(
                f"CartÃµes RFID: {len(cards)}"
            )
            print(
                f"PermissÃµes  : {len(permissions)}"
            )

            print()
            print("REGISTOS DA BASE DE DADOS")
            print("-" * 60)

            for table_name in db.metadata.tables:
                count = table_count(table_name)
                print(
                    f"  {table_name:<20} {count}"
                )

            print("=" * 60)
            print("SEED FINALIZADO")
            print("=" * 60)

        except Exception:
            db.session.rollback()

            print()
            print("=" * 60)
            print("ERRO DURANTE O DATABASE SEED")
            print("=" * 60)

            raise


if __name__ == "__main__":
    seed()

