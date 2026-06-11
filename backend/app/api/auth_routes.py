"""Authentication and entry-page HTTP handlers."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from flask import jsonify, redirect, request, session, url_for
from werkzeug.utils import secure_filename

from backend.app.core.config import settings
from backend.app.extensions import bcrypt
from backend.app.repositories import user_repository
from backend.app.services import auth_service

from .route_registry import AppRoute


PROFILE_IMAGE_DIR = (
    Path(__file__).resolve().parents[3] / "frontend" / "public" / "legacy" / "images"
)
PROFILE_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_PROFILE_IMAGE_SIZE = 5 * 1024 * 1024


def _save_profile_image(image):
    if not image or not image.filename:
        return None, None
    extension = Path(secure_filename(image.filename)).suffix.lower()
    if extension not in PROFILE_IMAGE_EXTENSIONS:
        raise ValueError("Ảnh đại diện chỉ hỗ trợ JPG, PNG hoặc WebP")
    image.stream.seek(0, 2)
    image_size = image.stream.tell()
    image.stream.seek(0)
    if image_size > MAX_PROFILE_IMAGE_SIZE:
        raise ValueError("Ảnh đại diện không được vượt quá 5 MB")
    PROFILE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"driver-{uuid4().hex}{extension}"
    saved_image = PROFILE_IMAGE_DIR / filename
    image.save(saved_image)
    return filename, saved_image


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


def update_account_profile():
    if "user_id" not in session or session.get("role") != "user":
        return jsonify(success=False, message="Không có quyền truy cập"), 403
    current = user_repository.find_driver_profile_by_user_id(session["user_id"])
    saved_image = None
    try:
        avatar_filename, saved_image = _save_profile_image(request.files.get("avatar"))
        driver = auth_service.update_profile(
            session["user_id"],
            request.form,
            avatar_filename,
        )
        session["full_name"] = driver["name"]
        if (
            avatar_filename
            and current
            and current["avatar"]
            and Path(current["avatar"]).name.startswith("driver-")
        ):
            (PROFILE_IMAGE_DIR / Path(current["avatar"]).name).unlink(missing_ok=True)
        return jsonify(success=True, message="Đã cập nhật thông tin", driver=driver)
    except ValueError as exc:
        if saved_image:
            saved_image.unlink(missing_ok=True)
        return jsonify(success=False, message=str(exc)), 400
    except Exception as exc:
        if saved_image:
            saved_image.unlink(missing_ok=True)
        return jsonify(success=False, message=f"Không thể cập nhật tài khoản: {exc}"), 500


def change_account_password():
    if "user_id" not in session or session.get("role") != "user":
        return jsonify(success=False, message="Không có quyền truy cập"), 403
    try:
        auth_service.change_password(
            session["user_id"],
            request.get_json(silent=True) or {},
            bcrypt,
        )
        return jsonify(success=True, message="Đổi mật khẩu thành công")
    except ValueError as exc:
        return jsonify(success=False, message=str(exc)), 400
    except Exception as exc:
        return jsonify(success=False, message=f"Không thể đổi mật khẩu: {exc}"), 500


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
    AppRoute(
        "/api/account/profile",
        "update_account_profile",
        "update_account_profile",
        ("PUT",),
        handler=update_account_profile,
    ),
    AppRoute(
        "/api/account/password",
        "change_account_password",
        "change_account_password",
        ("PUT",),
        handler=change_account_password,
    ),
)
