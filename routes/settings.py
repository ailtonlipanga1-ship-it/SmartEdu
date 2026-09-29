from flask import Blueprint, jsonify, request

from services.memory_store import store


settings_bp = Blueprint(
    "settings",
    __name__,
    url_prefix="/api/v1/settings",
)


@settings_bp.get("/")
def get_settings():
    return jsonify({
        "success": True,
        "data": store.settings,
    })


@settings_bp.put("/")
def update_settings():
    payload = request.get_json(silent=True) or {}

    for key, value in payload.items():
        store.settings[key] = value

    return jsonify({
        "success": True,
        "message": "Configurações atualizadas com sucesso.",
        "data": store.settings,
    })


@settings_bp.get("/<key>")
def get_setting(key):
    if key not in store.settings:
        return jsonify({
            "success": False,
            "message": "Configuração não encontrada.",
        }), 404

    return jsonify({
        "success": True,
        "data": {
            "key": key,
            "value": store.settings[key],
        },
    })