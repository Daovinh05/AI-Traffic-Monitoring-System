"""Dashboard API and frontend redirect handlers."""

from __future__ import annotations

from functools import wraps
from flask import jsonify, redirect, request, session, url_for

from backend.app.core.config import settings
from backend.app.services import dashboard_service

from .route_registry import AppRoute


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify(success=False, message="Vui lòng đăng nhập"), 401
            return redirect(url_for("login_page"))
        return view(*args, **kwargs)

    return wrapped


def _user_context():
    return {
        "user": session.get("user"),
        "tai_xe_id": session.get("tai_xe_id"),
        "vehicle_id": session.get("vehicle_id"),
    }


@login_required
def dashboard():
    return redirect(f"{settings.frontend_url}/admin/dashboard")


@login_required
def dashboard_data():
    if session.get("role") != "admin":
        return jsonify(success=False, message="Không có quyền truy cập"), 403
    try:
        page = request.args.get("page", 1, type=int)
        return jsonify(success=True, **dashboard_service.build_dashboard(page))
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


@login_required
def trang_chu_page():
    return redirect(f"{settings.frontend_url}/user/dashboard")


@login_required
def tu_van_page():
    return redirect(f"{settings.frontend_url}/user/chatbot")


@login_required
def tu_van_html():
    return redirect(f"{settings.frontend_url}/user/chatbot")


@login_required
def lai_xe_page():
    return redirect(f"{settings.frontend_url}/user/drive")


@login_required
def lai_xe_v2_page():
    return redirect(f"{settings.frontend_url}/user/drive")


@login_required
def lich_su_page():
    return redirect(f"{settings.frontend_url}/user/history")


@login_required
def traffic_bus():
    return redirect(f"{settings.frontend_url}/admin/dashboard")


ROUTES = (
    AppRoute("/dashboard", "dashboard", "dashboard", handler=dashboard),
    AppRoute(
        "/api/dashboard",
        "dashboard_data",
        "dashboard_data",
        handler=dashboard_data,
    ),
    AppRoute(
        "/trang_chu",
        "trang_chu_page",
        "trang_chu_page",
        handler=trang_chu_page,
    ),
    AppRoute("/tu_van", "tu_van_page", "tu_van_page", handler=tu_van_page),
    AppRoute("/tu_van.html", "tu_van_html", "tu_van_html", handler=tu_van_html),
    AppRoute("/lai_xe", "lai_xe_page", "lai_xe_page", handler=lai_xe_page),
    AppRoute(
        "/lai_xe_v2",
        "lai_xe_v2_page",
        "lai_xe_v2_page",
        handler=lai_xe_v2_page,
    ),
    AppRoute("/lich_su", "lich_su_page", "lich_su_page", handler=lich_su_page),
    AppRoute("/traffic_bus", "traffic_bus", "traffic_bus", handler=traffic_bus),
)
