"""Route-management HTTP handlers."""

from __future__ import annotations

from functools import wraps

from flask import jsonify, request, session

from backend.app.services import route_service

from .route_registry import AppRoute


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify(success=False, message="Vui lòng đăng nhập"), 401
        return view(*args, **kwargs)

    return wrapped


@login_required
def get_routes():
    try:
        return jsonify(success=True, routes=route_service.list_routes())
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


@login_required
def get_route_detail(route_id):
    try:
        route = route_service.get_route_detail(route_id)
        if not route:
            return jsonify(success=False, message="Tuyến đường không tồn tại"), 404
        return jsonify(success=True, route=route)
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


@login_required
def plan_route():
    if session.get("role") != "admin":
        return jsonify(success=False, message="Không có quyền truy cập"), 403
    try:
        data = request.get_json(silent=True) or {}
        plan = route_service.plan_route(
            data.get("start_address"),
            data.get("end_address"),
        )
        return jsonify(success=True, plan=plan)
    except ValueError as exc:
        return jsonify(success=False, message=str(exc)), 400
    except Exception as exc:
        return jsonify(
            success=False,
            message=f"Không thể kết nối dịch vụ bản đồ: {exc}",
        ), 502


@login_required
def create_route():
    try:
        result = route_service.create_route(request.get_json(silent=True) or {})
        return jsonify(
            success=result["success"],
            message=result["message"],
        ), result["status"]
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


@login_required
def update_route(route_id):
    try:
        result = route_service.update_route(
            route_id,
            request.get_json(silent=True) or {},
        )
        return jsonify(
            success=result["success"],
            message=result["message"],
        ), result["status"]
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


@login_required
def delete_route(route_id):
    try:
        result = route_service.delete_route(route_id)
        return jsonify(
            success=result["success"],
            message=result["message"],
        ), result["status"]
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


ROUTES = (
    AppRoute("/api/routes", "get_routes", "get_routes", handler=get_routes),
    AppRoute(
        "/api/routes/plan",
        "plan_route",
        "plan_route",
        ("POST",),
        handler=plan_route,
    ),
    AppRoute(
        "/api/routes/<route_id>",
        "get_route_detail",
        "get_route_detail",
        handler=get_route_detail,
    ),
    AppRoute(
        "/api/routes",
        "create_route",
        "create_route",
        ("POST",),
        handler=create_route,
    ),
    AppRoute(
        "/api/routes/<route_id>",
        "update_route",
        "update_route",
        ("PUT",),
        handler=update_route,
    ),
    AppRoute(
        "/api/routes/<route_id>",
        "delete_route",
        "delete_route",
        ("DELETE",),
        handler=delete_route,
    ),
)
