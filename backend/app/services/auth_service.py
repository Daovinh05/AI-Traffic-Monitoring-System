"""Authentication business logic."""

from __future__ import annotations

from backend.app.repositories import user_repository


def authenticate(username: str, password: str, password_hasher):
    username = (username or "").strip()
    if not username or not password:
        return {"success": False, "message": "Vui lòng nhập đầy đủ", "status": 400}

    user = user_repository.find_user_by_username(username)
    if not user:
        return {"success": False, "message": "Tên đăng nhập không tồn tại", "status": 401}

    if not user["is_active"]:
        return {"success": False, "message": "Tài khoản đã bị khóa", "status": 403}

    if not password_hasher.check_password_hash(user["password"], password):
        return {"success": False, "message": "Mật khẩu không đúng", "status": 401}

    session_data = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "full_name": user["full_name"],
    }

    if user["role"] == "user":
        driver = user_repository.find_driver_by_user_id(user["id"])
        if driver:
            session_data["tai_xe_id"] = driver["id"]
            vehicle = user_repository.find_vehicle_by_driver_id(driver["id"])
            if vehicle:
                session_data["vehicle_id"] = vehicle["id"]

    return {
        "success": True,
        "message": "Đăng nhập thành công",
        "status": 200,
        "redirect": "/dashboard" if user["role"] == "admin" else "/trang_chu",
        "session": session_data,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
        },
    }


def update_profile(user_id: int, data, avatar_filename=None):
    user = user_repository.find_user_by_id(user_id)
    driver = user_repository.find_driver_profile_by_user_id(user_id)
    if not user or not driver:
        raise ValueError("Không tìm thấy hồ sơ tài xế")

    full_name = (data.get("full_name") or "").strip()
    phone = (data.get("phone") or "").strip()
    license_number = (data.get("license_number") or "").strip().upper()
    if not full_name or not phone or not license_number:
        raise ValueError("Vui lòng nhập đầy đủ họ tên, số điện thoại và GPLX")
    if len(full_name) > 100 or len(phone) > 20 or len(license_number) > 50:
        raise ValueError("Thông tin tài khoản vượt quá độ dài cho phép")

    user_repository.update_user_profile(
        user_id,
        full_name,
        phone,
        license_number,
        avatar_filename if avatar_filename is not None else driver["avatar"],
    )
    return user_repository.find_driver_profile_by_user_id(user_id)


def change_password(user_id: int, data, password_hasher):
    user = user_repository.find_user_by_id(user_id)
    if not user:
        raise ValueError("Không tìm thấy tài khoản")

    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""
    confirm_password = data.get("confirm_password") or ""
    if not current_password or not new_password or not confirm_password:
        raise ValueError("Vui lòng nhập đầy đủ thông tin mật khẩu")
    if not password_hasher.check_password_hash(user["password"], current_password):
        raise ValueError("Mật khẩu hiện tại không đúng")
    if len(new_password) < 6:
        raise ValueError("Mật khẩu mới phải có ít nhất 6 ký tự")
    if new_password != confirm_password:
        raise ValueError("Xác nhận mật khẩu mới không khớp")
    if current_password == new_password:
        raise ValueError("Mật khẩu mới phải khác mật khẩu hiện tại")

    password_hash = password_hasher.generate_password_hash(new_password).decode("utf-8")
    user_repository.update_user_password(user_id, password_hash)
