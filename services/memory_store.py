from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from threading import RLock
from uuid import uuid4


class MemoryStore:
    """
    Camada temporÃ¡ria de dados do SmartEdu.
    Serve para manter o sistema funcional durante o desenvolvimento
    antes da migraÃ§Ã£o definitiva para PostgreSQL + SQLAlchemy.
    """

    def __init__(self) -> None:
        self._lock = RLock()

        self.students: dict[str, dict] = {}
        self.teachers: dict[str, dict] = {}
        self.cards: dict[str, dict] = {}
        self.rooms: dict[str, dict] = {}
        self.devices: dict[str, dict] = {}
        self.access_logs: list[dict] = []
        self.attendance: list[dict] = []
        self.users: dict[str, dict] = {}
        self.settings: dict[str, object] = {}

        self._seed()

    # ------------------------------------------------------------------
    # INTERNAL
    # ------------------------------------------------------------------

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:10]}"

    @staticmethod
    def _copy(value):
        return deepcopy(value)

    # ------------------------------------------------------------------
    # SEED
    # ------------------------------------------------------------------

    def _seed(self) -> None:
        students = [
            {
                "id": "std_001",
                "student_number": "STD2026001",
                "name": "Luis Manuel",
                "email": "luis.manuel@smartedu.local",
                "course": "AdministraÃ§Ã£o de Sistemas de Redes InformÃ¡ticas",
                "class_name": "2Âº Ano - ASRI",
                "status": "active",
                "rfid_card_id": "card_001",
                "created_at": self._now(),
            },
            {
                "id": "std_002",
                "student_number": "STD2026002",
                "name": "Ana Cristina",
                "email": "ana.cristina@smartedu.local",
                "course": "Tecnologias de InformaÃ§Ã£o",
                "class_name": "2Âº Ano - TI",
                "status": "active",
                "rfid_card_id": "card_002",
                "created_at": self._now(),
            },
            {
                "id": "std_003",
                "student_number": "STD2026003",
                "name": "Pedro Alberto",
                "email": "pedro.alberto@smartedu.local",
                "course": "Engenharia InformÃ¡tica",
                "class_name": "3Âº Ano - EI",
                "status": "active",
                "rfid_card_id": "card_003",
                "created_at": self._now(),
            },
            {
                "id": "std_004",
                "student_number": "STD2026004",
                "name": "Maria JosÃ©",
                "email": "maria.jose@smartedu.local",
                "course": "AdministraÃ§Ã£o e GestÃ£o",
                "class_name": "1Âº Ano - AG",
                "status": "active",
                "rfid_card_id": "card_004",
                "created_at": self._now(),
            },
        ]

        for student in students:
            self.students[student["id"]] = student

        teachers = [
            {
                "id": "tch_001",
                "employee_number": "DOC001",
                "name": "Dr. Carlos Manuel",
                "email": "carlos.manuel@smartedu.local",
                "department": "Tecnologias de InformaÃ§Ã£o",
                "status": "active",
                "created_at": self._now(),
            },
            {
                "id": "tch_002",
                "employee_number": "DOC002",
                "name": "MSc. JoÃ£o Ernesto",
                "email": "joao.ernesto@smartedu.local",
                "department": "Redes e Sistemas",
                "status": "active",
                "created_at": self._now(),
            },
        ]

        for teacher in teachers:
            self.teachers[teacher["id"]] = teacher

        cards = [
            {
                "id": "card_001",
                "uid": "A4:92:17:3B",
                "holder_type": "student",
                "holder_id": "std_001",
                "status": "active",
                "last_seen": self._now(),
            },
            {
                "id": "card_002",
                "uid": "B8:21:44:9C",
                "holder_type": "student",
                "holder_id": "std_002",
                "status": "active",
                "last_seen": self._now(),
            },
            {
                "id": "card_003",
                "uid": "C1:73:52:8A",
                "holder_type": "student",
                "holder_id": "std_003",
                "status": "active",
                "last_seen": self._now(),
            },
            {
                "id": "card_004",
                "uid": "D9:64:11:EF",
                "holder_type": "student",
                "holder_id": "std_004",
                "status": "active",
                "last_seen": self._now(),
            },
        ]

        for card in cards:
            self.cards[card["id"]] = card

        rooms = [
            {
                "id": "room_001",
                "code": "LAB-NET-01",
                "name": "LaboratÃ³rio de Redes",
                "building": "Bloco A",
                "floor": 1,
                "capacity": 32,
                "occupancy": 18,
                "status": "online",
            },
            {
                "id": "room_002",
                "code": "LAB-SYS-01",
                "name": "LaboratÃ³rio de Sistemas",
                "building": "Bloco A",
                "floor": 1,
                "capacity": 28,
                "occupancy": 11,
                "status": "online",
            },
            {
                "id": "room_003",
                "code": "AUD-01",
                "name": "AuditÃ³rio Principal",
                "building": "Bloco B",
                "floor": 0,
                "capacity": 180,
                "occupancy": 74,
                "status": "online",
            },
        ]

        for room in rooms:
            self.rooms[room["id"]] = room

        devices = [
            {
                "id": "dev_001",
                "device_code": "RFID-GW-001",
                "name": "Gateway RFID Entrada Principal",
                "type": "rfid_gateway",
                "room_id": "room_001",
                "ip_address": "192.168.10.21",
                "status": "online",
                "signal": 96,
                "last_heartbeat": self._now(),
                "firmware": "2.4.1",
            },
            {
                "id": "dev_002",
                "device_code": "RFID-GW-002",
                "name": "Gateway RFID Bloco B",
                "type": "rfid_gateway",
                "room_id": "room_003",
                "ip_address": "192.168.10.22",
                "status": "online",
                "signal": 91,
                "last_heartbeat": self._now(),
                "firmware": "2.4.1",
            },
            {
                "id": "dev_003",
                "device_code": "IOT-SENSOR-001",
                "name": "Sensor de PresenÃ§a LAB-NET",
                "type": "presence_sensor",
                "room_id": "room_001",
                "ip_address": "192.168.10.31",
                "status": "online",
                "signal": 88,
                "last_heartbeat": self._now(),
                "firmware": "1.8.0",
            },
            {
                "id": "dev_004",
                "device_code": "IOT-SENSOR-002",
                "name": "Sensor Ambiental AuditÃ³rio",
                "type": "environment_sensor",
                "room_id": "room_003",
                "ip_address": "192.168.10.32",
                "status": "warning",
                "signal": 61,
                "last_heartbeat": self._now(),
                "firmware": "1.7.4",
            },
        ]

        for device in devices:
            self.devices[device["id"]] = device

        self.users["usr_001"] = {
            "id": "usr_001",
            "name": "Administrador",
            "email": "admin@smartedu.local",
            "role": "admin",
            "status": "active",
            "password_hash": None,
            "created_at": self._now(),
        }

        self.settings = {
            "institution_name": "SmartEdu Campus",
            "system_name": "SmartEdu Access",
            "maintenance_mode": False,
            "rfid_enabled": True,
            "iot_enabled": True,
            "notifications_enabled": True,
        }

        self._seed_access_logs()
        self._seed_attendance()

    # ------------------------------------------------------------------
    # ACCESS
    # ------------------------------------------------------------------

    def _seed_access_logs(self) -> None:
        events = [
            ("std_001", "card_001", "RFID-GW-001", "granted"),
            ("std_002", "card_002", "RFID-GW-001", "granted"),
            ("std_003", "card_003", "RFID-GW-002", "granted"),
            ("std_004", "card_004", "RFID-GW-001", "granted"),
        ]

        for student_id, card_id, device_code, result in events:
            self.access_logs.append(
                {
                    "id": self._id("access"),
                    "student_id": student_id,
                    "card_id": card_id,
                    "device_code": device_code,
                    "result": result,
                    "direction": "entry",
                    "timestamp": self._now(),
                }
            )

        self.access_logs.append(
            {
                "id": self._id("access"),
                "student_id": None,
                "card_id": None,
                "device_code": "RFID-GW-001",
                "result": "denied",
                "direction": "entry",
                "reason": "CartÃ£o nÃ£o reconhecido",
                "timestamp": self._now(),
            }
        )

    def record_access(
        self,
        *,
        card_uid: str,
        device_code: str | None = None,
        direction: str = "entry",
    ) -> dict:
        with self._lock:
            card = next(
                (
                    item
                    for item in self.cards.values()
                    if item["uid"].lower() == card_uid.lower()
                ),
                None,
            )

            timestamp = self._now()

            if not card:
                event = {
                    "id": self._id("access"),
                    "student_id": None,
                    "card_id": None,
                    "device_code": device_code,
                    "result": "denied",
                    "direction": direction,
                    "reason": "CartÃ£o nÃ£o registado",
                    "timestamp": timestamp,
                }

                self.access_logs.insert(0, event)

                return self._copy(event)

            if card["status"] != "active":
                event = {
                    "id": self._id("access"),
                    "student_id": card["holder_id"],
                    "card_id": card["id"],
                    "device_code": device_code,
                    "result": "denied",
                    "direction": direction,
                    "reason": "CartÃ£o inativo",
                    "timestamp": timestamp,
                }

                self.access_logs.insert(0, event)

                return self._copy(event)

            card["last_seen"] = timestamp

            event = {
                "id": self._id("access"),
                "student_id": card["holder_id"],
                "card_id": card["id"],
                "device_code": device_code,
                "result": "granted",
                "direction": direction,
                "timestamp": timestamp,
            }

            self.access_logs.insert(0, event)

            return self._copy(event)

    # ------------------------------------------------------------------
    # ATTENDANCE
    # ------------------------------------------------------------------

    def _seed_attendance(self) -> None:
        now = datetime.now()

        for student_id in self.students:
            self.attendance.append(
                {
                    "id": self._id("att"),
                    "student_id": student_id,
                    "date": now.date().isoformat(),
                    "status": "present",
                    "check_in": now.replace(
                        hour=7,
                        minute=40,
                        second=0,
                        microsecond=0,
                    ).isoformat(timespec="seconds"),
                    "check_out": None,
                }
            )

    # ------------------------------------------------------------------
    # GENERIC COLLECTION OPERATIONS
    # ------------------------------------------------------------------

    def list_collection(
        self,
        collection: str,
    ) -> list[dict]:
        with self._lock:
            data = getattr(self, collection)

            if isinstance(data, dict):
                return self._copy(list(data.values()))

            return self._copy(data)

    def get(
        self,
        collection: str,
        item_id: str,
    ) -> dict | None:
        with self._lock:
            data = getattr(self, collection)

            if isinstance(data, dict):
                item = data.get(item_id)

                return self._copy(item) if item else None

            for item in data:
                if item.get("id") == item_id:
                    return self._copy(item)

            return None

    def create(
        self,
        collection: str,
        payload: dict,
        prefix: str,
    ) -> dict:
        with self._lock:
            data = getattr(self, collection)

            item = self._copy(payload)

            item["id"] = item.get(
                "id",
                self._id(prefix),
            )

            item.setdefault(
                "created_at",
                self._now(),
            )

            if isinstance(data, dict):
                data[item["id"]] = item
            else:
                data.insert(0, item)

            return self._copy(item)

    def update(
        self,
        collection: str,
        item_id: str,
        payload: dict,
    ) -> dict | None:
        with self._lock:
            data = getattr(self, collection)

            if isinstance(data, dict):
                if item_id not in data:
                    return None

                data[item_id].update(
                    self._copy(payload)
                )

                data[item_id]["id"] = item_id

                return self._copy(
                    data[item_id]
                )

            for item in data:
                if item.get("id") == item_id:
                    item.update(
                        self._copy(payload)
                    )

                    item["id"] = item_id

                    return self._copy(item)

            return None

    def delete(
        self,
        collection: str,
        item_id: str,
    ) -> bool:
        with self._lock:
            data = getattr(self, collection)

            if isinstance(data, dict):
                return data.pop(
                    item_id,
                    None,
                ) is not None

            for index, item in enumerate(data):
                if item.get("id") == item_id:
                    data.pop(index)
                    return True

            return False

    # ------------------------------------------------------------------
    # DASHBOARD
    # ------------------------------------------------------------------

    def dashboard(self) -> dict:
        with self._lock:
            online_devices = sum(
                1
                for device in self.devices.values()
                if device["status"] == "online"
            )

            active_cards = sum(
                1
                for card in self.cards.values()
                if card["status"] == "active"
            )

            granted = sum(
                1
                for event in self.access_logs
                if event["result"] == "granted"
            )

            denied = sum(
                1
                for event in self.access_logs
                if event["result"] == "denied"
            )

            return {
                "mode": "demo",
                "institution": self.settings[
                    "institution_name"
                ],
                "statistics": {
                    "students": len(
                        self.students
                    ),
                    "teachers": len(
                        self.teachers
                    ),
                    "active_cards": active_cards,
                    "devices": len(
                        self.devices
                    ),
                    "online_devices": online_devices,
                    "rooms": len(
                        self.rooms
                    ),
                    "access_granted": granted,
                    "access_denied": denied,
                    "attendance": len(
                        self.attendance
                    ),
                },
                "recent_access": self._copy(
                    self.access_logs[:10]
                ),
                "devices": self._copy(
                    list(
                        self.devices.values()
                    )
                ),
                "rooms": self._copy(
                    list(
                        self.rooms.values()
                    )
                ),
                "settings": self._copy(
                    self.settings
                ),
            }


store = MemoryStore()
