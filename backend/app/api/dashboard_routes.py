"""Dashboard API and frontend redirect handlers."""

from __future__ import annotations

from datetime import datetime
from functools import wraps
from pathlib import Path
from uuid import uuid4

from flask import jsonify, redirect, render_template, request, session, url_for
from pymysql.err import IntegrityError
from werkzeug.utils import secure_filename

from backend.app.core.config import settings
from backend.app.services import dashboard_service

from .route_registry import AppRoute


VEHICLE_IMAGE_DIR = (
    Path(__file__).resolve().parents[3] / "frontend" / "public" / "legacy" / "images"
)
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_VEHICLE_IMAGE_SIZE = 5 * 1024 * 1024


def _save_image(image, prefix, label):
    if not image or not image.filename:
        return None, None

    extension = Path(secure_filename(image.filename)).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(f"{label} chỉ hỗ trợ JPG, PNG hoặc WebP")

    image.stream.seek(0, 2)
    image_size = image.stream.tell()
    image.stream.seek(0)
    if image_size > MAX_VEHICLE_IMAGE_SIZE:
        raise ValueError(f"{label} không được vượt quá 5 MB")

    VEHICLE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    image_filename = f"{prefix}-{uuid4().hex}{extension}"
    saved_image = VEHICLE_IMAGE_DIR / image_filename
    image.save(saved_image)
    return image_filename, saved_image


def _save_vehicle_image(image):
    return _save_image(image, "vehicle", "Ảnh xe")


def _save_driver_avatar(image):
    return _save_image(image, "driver", "Ảnh đại diện")


def _delete_uploaded_vehicle_image(filename):
    if filename and Path(filename).name.startswith("vehicle-"):
        (VEHICLE_IMAGE_DIR / Path(filename).name).unlink(missing_ok=True)


def _delete_uploaded_driver_avatar(filename):
    if filename and Path(filename).name.startswith("driver-"):
        (VEHICLE_IMAGE_DIR / Path(filename).name).unlink(missing_ok=True)


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
    if session.get("role") != "admin":
        return redirect(f"{settings.frontend_url}/user/dashboard")
    try:
        page = request.args.get("page", 1, type=int)
        context = dashboard_service.build_dashboard(page)
        return render_template(
            "Dashboard.html",
            **context,
            user=session.get("username"),
            user_role=session.get("role"),
            now=datetime.now().strftime("%H:%M %d/%m/%Y"),
        )
    except Exception as exc:
        return f"Lỗi tải dashboard: {exc}", 500


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
def create_vehicle():
    if session.get("role") != "admin":
        return jsonify(success=False, message="Không có quyền truy cập"), 403

    image = request.files.get("image")
    image_filename = None
    saved_image = None

    try:
        image_filename, saved_image = _save_vehicle_image(image)

        vehicle = dashboard_service.create_vehicle(request.form, image_filename)
        return jsonify(
            success=True,
            message="Đã thêm xe mới thành công",
            vehicle=vehicle,
        ), 201
    except ValueError as exc:
        if saved_image:
            saved_image.unlink(missing_ok=True)
        return jsonify(success=False, message=str(exc)), 400
    except IntegrityError:
        if saved_image:
            saved_image.unlink(missing_ok=True)
        return jsonify(
            success=False,
            message="Biển số xe đã tồn tại trong hệ thống",
        ), 409
    except Exception as exc:
        if saved_image:
            saved_image.unlink(missing_ok=True)
        return jsonify(success=False, message=f"Không thể thêm xe: {exc}"), 500


@login_required
def get_vehicle(vehicle_id):
    if session.get("role") != "admin":
        return jsonify(success=False, message="Không có quyền truy cập"), 403
    try:
        vehicle = dashboard_service.get_vehicle(vehicle_id)
        if not vehicle:
            return jsonify(success=False, message="Phương tiện không tồn tại"), 404
        return jsonify(success=True, vehicle=vehicle)
    except Exception as exc:
        return jsonify(success=False, message=f"Không thể tải thông tin xe: {exc}"), 500


@login_required
def update_vehicle(vehicle_id):
    if session.get("role") != "admin":
        return jsonify(success=False, message="Không có quyền truy cập"), 403

    image_filename = None
    saved_image = None
    current = dashboard_service.get_vehicle(vehicle_id)
    if not current:
        return jsonify(success=False, message="Phương tiện không tồn tại"), 404

    try:
        image_filename, saved_image = _save_vehicle_image(request.files.get("image"))
        vehicle = dashboard_service.update_vehicle(
            vehicle_id,
            request.form,
            image_filename,
        )
        if image_filename:
            _delete_uploaded_vehicle_image(current["image"])
        return jsonify(
            success=True,
            message="Đã cập nhật phương tiện",
            vehicle=vehicle,
        )
    except ValueError as exc:
        if saved_image:
            saved_image.unlink(missing_ok=True)
        return jsonify(success=False, message=str(exc)), 400
    except IntegrityError:
        if saved_image:
            saved_image.unlink(missing_ok=True)
        return jsonify(
            success=False,
            message="Biển số xe đã tồn tại trong hệ thống",
        ), 409
    except Exception as exc:
        if saved_image:
            saved_image.unlink(missing_ok=True)
        return jsonify(success=False, message=f"Không thể cập nhật xe: {exc}"), 500


@login_required
def delete_vehicle(vehicle_id):
    if session.get("role") != "admin":
        return jsonify(success=False, message="Không có quyền truy cập"), 403
    try:
        vehicle = dashboard_service.delete_vehicle(vehicle_id)
        if not vehicle:
            return jsonify(success=False, message="Phương tiện không tồn tại"), 404
        _delete_uploaded_vehicle_image(vehicle["image"])
        return jsonify(success=True, message="Đã xóa phương tiện")
    except Exception as exc:
        return jsonify(success=False, message=f"Không thể xóa xe: {exc}"), 500


@login_required
def create_driver():
    if session.get("role") != "admin":
        return jsonify(success=False, message="Không có quyền truy cập"), 403
    saved_avatar = None
    try:
        avatar_filename, saved_avatar = _save_driver_avatar(
            request.files.get("avatar")
        )
        driver = dashboard_service.create_driver(request.form, avatar_filename)
        return jsonify(
            success=True,
            message="Đã thêm tài xế mới",
            driver=driver,
        ), 201
    except ValueError as exc:
        if saved_avatar:
            saved_avatar.unlink(missing_ok=True)
        return jsonify(success=False, message=str(exc)), 400
    except IntegrityError:
        if saved_avatar:
            saved_avatar.unlink(missing_ok=True)
        return jsonify(success=False, message="Mã tài xế đã tồn tại"), 409
    except Exception as exc:
        if saved_avatar:
            saved_avatar.unlink(missing_ok=True)
        return jsonify(success=False, message=f"Không thể thêm tài xế: {exc}"), 500


@login_required
def get_driver(driver_id):
    if session.get("role") != "admin":
        return jsonify(success=False, message="Không có quyền truy cập"), 403
    try:
        driver = dashboard_service.get_driver(driver_id)
        if not driver:
            return jsonify(success=False, message="Tài xế không tồn tại"), 404
        return jsonify(success=True, driver=driver)
    except Exception as exc:
        return jsonify(success=False, message=f"Không thể tải tài xế: {exc}"), 500


@login_required
def update_driver(driver_id):
    if session.get("role") != "admin":
        return jsonify(success=False, message="Không có quyền truy cập"), 403
    current = dashboard_service.get_driver(driver_id)
    if not current:
        return jsonify(success=False, message="Tài xế không tồn tại"), 404
    saved_avatar = None
    try:
        avatar_filename, saved_avatar = _save_driver_avatar(
            request.files.get("avatar")
        )
        driver = dashboard_service.update_driver(
            driver_id, request.form, avatar_filename
        )
        if avatar_filename:
            _delete_uploaded_driver_avatar(current["avatar"])
        return jsonify(success=True, message="Đã cập nhật tài xế", driver=driver)
    except ValueError as exc:
        if saved_avatar:
            saved_avatar.unlink(missing_ok=True)
        return jsonify(success=False, message=str(exc)), 400
    except IntegrityError:
        if saved_avatar:
            saved_avatar.unlink(missing_ok=True)
        return jsonify(success=False, message="Mã tài xế đã tồn tại"), 409
    except Exception as exc:
        if saved_avatar:
            saved_avatar.unlink(missing_ok=True)
        return jsonify(success=False, message=f"Không thể cập nhật tài xế: {exc}"), 500


@login_required
def delete_driver(driver_id):
    if session.get("role") != "admin":
        return jsonify(success=False, message="Không có quyền truy cập"), 403
    try:
        driver = dashboard_service.delete_driver(driver_id)
        if not driver:
            return jsonify(success=False, message="Tài xế không tồn tại"), 404
        _delete_uploaded_driver_avatar(driver["avatar"])
        return jsonify(success=True, message="Đã xóa tài xế")
    except Exception as exc:
        return jsonify(success=False, message=f"Không thể xóa tài xế: {exc}"), 500


@login_required
def legacy_admin_dashboard():
    return dashboard()


@login_required
def trang_chu_page():
    return render_template("trang_chu.html", **_user_context())


@login_required
def tu_van_page():
    return render_template("tu_van.html", **_user_context())


@login_required
def tu_van_html():
    return tu_van_page()


@login_required
def lai_xe_page():
    return render_template("lai_xe.html", **_user_context())


@login_required
def lai_xe_v2_page():
    return lai_xe_page()


@login_required
def lich_su_page():
    return render_template("lich_su.html", **_user_context())


@login_required
def traffic_bus():
    return dashboard()


ROUTES = (
    AppRoute("/dashboard", "dashboard", "dashboard", handler=dashboard),
    AppRoute(
        "/api/dashboard",
        "dashboard_data",
        "dashboard_data",
        handler=dashboard_data,
    ),
    AppRoute(
        "/api/vehicles",
        "create_vehicle",
        "create_vehicle",
        ("POST",),
        handler=create_vehicle,
    ),
    AppRoute(
        "/api/vehicles/<int:vehicle_id>",
        "get_vehicle",
        "get_vehicle",
        handler=get_vehicle,
    ),
    AppRoute(
        "/api/vehicles/<int:vehicle_id>",
        "update_vehicle",
        "update_vehicle",
        ("PUT",),
        handler=update_vehicle,
    ),
    AppRoute(
        "/api/vehicles/<int:vehicle_id>",
        "delete_vehicle",
        "delete_vehicle",
        ("DELETE",),
        handler=delete_vehicle,
    ),
    AppRoute(
        "/api/drivers",
        "create_driver",
        "create_driver",
        ("POST",),
        handler=create_driver,
    ),
    AppRoute(
        "/api/drivers/<int:driver_id>",
        "get_driver",
        "get_driver",
        handler=get_driver,
    ),
    AppRoute(
        "/api/drivers/<int:driver_id>",
        "update_driver",
        "update_driver",
        ("PUT",),
        handler=update_driver,
    ),
    AppRoute(
        "/api/drivers/<int:driver_id>",
        "delete_driver",
        "delete_driver",
        ("DELETE",),
        handler=delete_driver,
    ),
    AppRoute(
        "/legacy/admin-dashboard",
        "legacy_admin_dashboard",
        "legacy_admin_dashboard",
        handler=legacy_admin_dashboard,
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
