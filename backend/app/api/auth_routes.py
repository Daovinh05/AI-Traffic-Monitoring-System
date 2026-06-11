"""Authentication and entry-page HTTP handlers."""

from __future__ import annotations

from flask import jsonify, redirect, request, session, url_for

from backend.app.core.config import settings
from backend.app.extensions import bcrypt
from backend.app.services import auth_service

from .route_registry import AppRoute


def index_page():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    if session.get("role") == "admin":
        return redirect(url_for("dashboard"))
    return redirect(url_for("trang_chu_page"))


def login_page():
    if "user_id" in session:
        return redirect(url_for("index_page"))
    return redirect(f"{settings.frontend_url}/login")


def api_login():
    try:
        data = request.get_json(silent=True) or {}
        result = auth_service.authenticate(
            data.get("username", ""),
            data.get("password", ""),
            bcrypt,
        )
        if not result["success"]:
            return jsonify(
                success=False,
                message=result["message"],
            ), result["status"]

        session.clear()
        session.permanent = True
        session.update(result["session"])
        return jsonify(
            success=True,
            message=result["message"],
            redirect=result["redirect"],
            user=result["user"],
        ), result["status"]
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


def api_logout():
    if "user_id" not in session:
        return jsonify(success=False, message="Vui lòng đăng nhập"), 401
    session.clear()
    return jsonify(
        success=True,
        message="Đăng xuất thành công",
        redirect="/login",
    )


def check_auth():
    if "user_id" not in session:
        return jsonify(authenticated=False)

    role = session.get("role")
    return jsonify(
        authenticated=True,
        user={
            "id": session.get("user_id"),
            "username": session.get("username"),
            "full_name": session.get("full_name"),
            "role": role,
            "driver_id": session.get("tai_xe_id"),
            "vehicle_id": session.get("vehicle_id"),
        },
        redirect="/dashboard" if role == "admin" else "/trang_chu",
    )


ROUTES = (
    AppRoute("/", "index_page", "index_page", handler=index_page),
    AppRoute("/login", "login_page", "login_page", handler=login_page),
    AppRoute(
        "/api/login",
        "api_login",
        "api_login",
        ("POST",),
        handler=api_login,
    ),
    AppRoute(
        "/api/logout",
        "api_logout",
        "api_logout",
        ("POST",),
        handler=api_logout,
    ),
    AppRoute(
        "/api/check-auth",
        "check_auth",
        "check_auth",
        handler=check_auth,
    ),
)
