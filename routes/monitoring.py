from __future__ import annotations

from flask import Blueprint, render_template

from services.auth_service import login_required


monitoring_bp = Blueprint(
    "monitoring",
    __name__,
    url_prefix="/monitoring",
)


@monitoring_bp.get("/")
@login_required
def index():
    return render_template("monitoring/index.html")