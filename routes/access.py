from __future__ import annotations

from flask import Blueprint, jsonify, request

from services.access_service import (
    access_log_to_dict,
    access_statistics as get_access_statistics,
    get_access_log,
    list_access_logs,
)
from services.auth_service import login_required


access_bp = Blueprint(
    "access",
    __name__,
    url_prefix="/api/v1/access",
)


def current_institution_id():
    """
    Obtém a instituição associada à sessão autenticada.
    Mantém o isolamento entre instituições.
    """
    from flask import session

    user = session.get("user")

    if isinstance(user, dict):
        return user.get("institution_id")

    return session.get("institution_id")


def enrich_access_log(log):
    """
    Converte um AccessLog persistente para uma resposta de API
    enriquecida com os dados atuais do titular e do dispositivo.
    """

    data = access_log_to_dict(log)

    holder_name = None
    holder_type = None

    if log.student is not None:
        holder_name = log.student.name
        holder_type = "student"

    elif log.teacher is not None:
        holder_name = log.teacher.name
        holder_type = "teacher"

    data["holder_name"] = holder_name
    data["holder_type"] = holder_type

    if log.card is not None:
        data["card"] = {
            "id": log.card.id,
            "uid": log.card.uid,
            "status": log.card.status,
        }
    else:
        data["card"] = None

    if log.device is not None:
        data["device"] = {
            "id": log.device.id,
            "name": log.device.name,
            "type": log.device.type,
            "status": log.device.status,
            "location": log.device.location,
        }
    else:
        data["device"] = None

    return data


@access_bp.get("/")
@login_required
def access_history():
    """
    Histórico completo de acessos persistidos no SQLite.

    Suporta filtros:
        result
        direction
        student_id
        teacher_id
        card_id
        device_id
        card_uid
        limit
    """

    institution_id = current_institution_id()

    result = request.args.get("result")
    direction = request.args.get("direction")
    card_uid = request.args.get("card_uid")

    student_id = request.args.get(
        "student_id",
        type=int,
    )

    teacher_id = request.args.get(
        "teacher_id",
        type=int,
    )

    card_id = request.args.get(
        "card_id",
        type=int,
    )

    device_id = request.args.get(
        "device_id",
        type=int,
    )

    limit = request.args.get(
        "limit",
        default=100,
        type=int,
    )

    limit = max(1, min(limit, 1000))

    logs = list_access_logs(
        institution_id=institution_id,
        result=result,
        student_id=student_id,
        teacher_id=teacher_id,
        card_id=card_id,
        device_id=device_id,
        card_uid=card_uid,
        direction=direction,
        limit=limit,
    )

    return jsonify(
        {
            "success": True,
            "count": len(logs),
            "limit": limit,
            "filters": {
                "result": result,
                "direction": direction,
                "student_id": student_id,
                "teacher_id": teacher_id,
                "card_id": card_id,
                "device_id": device_id,
                "card_uid": card_uid,
            },
            "data": [
                enrich_access_log(log)
                for log in logs
            ],
        }
    )


@access_bp.get("/live")
@login_required
def live_access():
    """
    Últimos eventos RFID da instituição.
    """

    institution_id = current_institution_id()

    limit = request.args.get(
        "limit",
        default=10,
        type=int,
    )

    limit = max(1, min(limit, 100))

    logs = list_access_logs(
        institution_id=institution_id,
        limit=limit,
    )

    return jsonify(
        {
            "success": True,
            "count": len(logs),
            "data": [
                enrich_access_log(log)
                for log in logs
            ],
        }
    )


@access_bp.get("/statistics")
@login_required
def access_statistics():
    """
    Estatísticas reais calculadas a partir dos AccessLogs persistentes.
    """

    institution_id = current_institution_id()

    statistics = get_access_statistics(
        institution_id=institution_id,
    )

    return jsonify(
        {
            "success": True,
            "data": statistics,
        }
    )


@access_bp.get("/<int:event_id>")
@login_required
def get_access(event_id):
    """
    Consulta um evento persistente específico.

    O evento só pode ser consultado se pertencer
    à instituição da sessão atual.
    """

    institution_id = current_institution_id()

    event = get_access_log(event_id)

    if event is None:
        return jsonify(
            {
                "success": False,
                "message": "Registo de acesso não encontrado.",
            }
        ), 404

    if event.institution_id != institution_id:
        return jsonify(
            {
                "success": False,
                "message": "Registo de acesso não encontrado.",
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "data": enrich_access_log(event),
        }
    )