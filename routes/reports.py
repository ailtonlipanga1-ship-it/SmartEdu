from __future__ import annotations

from flask import Blueprint, jsonify

from services.memory_store import store


reports_bp = Blueprint(
    "reports",
    __name__,
    url_prefix="/api/v1/reports",
)


@reports_bp.get("/overview")
def overview():
    dashboard = store.dashboard()

    return jsonify(
        {
            "success": True,
            "generated_at": store._now(),
            "data": dashboard["statistics"],
        }
    )


@reports_bp.get("/access")
def access_report():
    events = store.list_collection(
        "access_logs"
    )

    granted = [
        event
        for event in events
        if event["result"] == "granted"
    ]

    denied = [
        event
        for event in events
        if event["result"] == "denied"
    ]

    return jsonify(
        {
            "success": True,
            "report": "access",
            "data": {
                "total": len(events),
                "granted": len(granted),
                "denied": len(denied),
                "events": events,
            },
        }
    )


@reports_bp.get("/attendance")
def attendance_report():
    records = store.list_collection(
        "attendance"
    )

    present = sum(
        record["status"] == "present"
        for record in records
    )

    absent = sum(
        record["status"] == "absent"
        for record in records
    )

    return jsonify(
        {
            "success": True,
            "report": "attendance",
            "data": {
                "total": len(records),
                "present": present,
                "absent": absent,
                "records": records,
            },
        }
    )