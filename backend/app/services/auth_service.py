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
