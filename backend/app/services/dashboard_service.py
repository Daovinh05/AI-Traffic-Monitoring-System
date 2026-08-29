"""Dashboard business logic."""

from __future__ import annotations

from backend.app.repositories import dashboard_repository


ALLOWED_VEHICLE_TYPES = {"car", "bus", "truck", "taxi"}
ALLOWED_VEHICLE_STATUSES = {"Đang hoạt động", "Bảo trì", "Ngừng hoạt động"}
LEGACY_VEHICLE_STATUSES = {
    "Đang chạy": "Đang hoạt động",
    "Đang dừng": "Bảo trì",
    "Mất tín hiệu": "Ngừng hoạt động",
}
ALLOWED_DRIVER_STATUSES = {"Đang làm việc", "Đang nghỉ"}


def _normalize_vehicle_status(status):
    return LEGACY_VEHICLE_STATUSES.get(status, status or "Ngừng hoạt động")


def _format_vehicle(vehicle):
    return {
        "id": vehicle["id"],
        "plate": vehicle["plate"],
        "type": vehicle["type"],
        "image": vehicle["image"],
        "driver_id": vehicle["driver_id"],
        "driver_name": vehicle["driver_name"],
        "driver_phone": vehicle["driver_phone"],
        "route_id": vehicle["route_id"],
        "route_name": vehicle["route_name"],
        "location": vehicle["location"],
        "status": _normalize_vehicle_status(vehicle["status"]),
        "speed": int(vehicle["speed"] or 0),
        "lat": float(vehicle["lat"]) if vehicle["lat"] is not None else None,
        "lng": float(vehicle["lng"]) if vehicle["lng"] is not None else None,
    }


def _validate_vehicle_data(data):
    plate = (data.get("plate") or "").strip().upper()
    vehicle_type = (data.get("type") or "car").strip().lower()
    location = (data.get("location") or "").strip()
    status = (data.get("status") or "Đang hoạt động").strip()

    if not plate or not location:
        raise ValueError("Vui lòng nhập biển số và vị trí xe")
    if len(plate) > 20:
        raise ValueError("Biển số xe không được vượt quá 20 ký tự")
    if vehicle_type not in ALLOWED_VEHICLE_TYPES:
        raise ValueError("Loại xe không hợp lệ")
    if status not in ALLOWED_VEHICLE_STATUSES:
        raise ValueError("Trạng thái xe không hợp lệ")

    try:
        driver_id = int(data["driver_id"]) if data.get("driver_id") else None
        latitude = float(data.get("lat") or 21.0285)
        longitude = float(data.get("lng") or 105.8542)
    except (TypeError, ValueError) as exc:
        raise ValueError("Tài xế hoặc tọa độ không hợp lệ") from exc

    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Tọa độ xe không hợp lệ")

    return {
        "plate": plate,
        "vehicle_type": vehicle_type,
        "driver_id": driver_id,
        "route_id": (data.get("route_id") or "").strip() or None,
        "location": location,
        "status": status,
        "latitude": latitude,
        "longitude": longitude,
    }


def build_stats():
    vehicles = dashboard_repository.list_vehicle_statuses()
    statuses = [_normalize_vehicle_status(vehicle["status"]) for vehicle in vehicles]
    return {
        "total_vehicles": len(vehicles),
        "running": statuses.count("Đang hoạt động"),
        "stopped": statuses.count("Bảo trì"),
        "offline": statuses.count("Ngừng hoạt động"),
        "alerts": 0,
        "violations": 0,
        "quality": 86.0,
    }


def get_vehicle_page(page: int, per_page: int = 5):
    offset = (page - 1) * per_page
    vehicles = dashboard_repository.list_dashboard_vehicles(per_page, offset)
    all_vehicles = dashboard_repository.list_dashboard_vehicles()
    total_pages = (len(all_vehicles) + per_page - 1) // per_page
    return {
        "vehicles": vehicles,
        "all_vehicles": all_vehicles,
        "page": page,
        "total_pages": total_pages,
    }


def build_dashboard(page: int, per_page: int = 5):
    vehicle_page = get_vehicle_page(page, per_page)
    routes = dashboard_repository.list_routes()
    for route in routes:
        route["path"] = [
            [float(point["latitude"]), float(point["longitude"])]
            for point in dashboard_repository.list_route_path(route["code"])
        ]

    return {
        **vehicle_page,
        "stats": build_stats(),
        "drivers": dashboard_repository.list_drivers(),
        "routes": routes,
        "warnings": dashboard_repository.list_recent_warnings(),
        "admin_alerts": dashboard_repository.list_recent_admin_alerts(),
    }


def create_vehicle(data, image_filename: str | None = None):
    values = _validate_vehicle_data(data)
    vehicle_id = dashboard_repository.create_vehicle(
        values["plate"],
        values["vehicle_type"],
        image_filename,
        values["driver_id"],
        values["route_id"],
        values["location"],
        values["status"],
        values["latitude"],
        values["longitude"],
    )
    return get_vehicle(vehicle_id)


def get_vehicle(vehicle_id: int):
    vehicle = dashboard_repository.get_vehicle(vehicle_id)
    return _format_vehicle(vehicle) if vehicle else None


def update_vehicle(vehicle_id: int, data, image_filename: str | None = None):
    current = dashboard_repository.get_vehicle(vehicle_id)
    if not current:
        return None

    values = _validate_vehicle_data(data)
    dashboard_repository.update_vehicle(
        vehicle_id,
        values["plate"],
        values["vehicle_type"],
        image_filename if image_filename is not None else current["image"],
        values["driver_id"],
        values["route_id"],
        values["location"],
        values["status"],
        values["latitude"],
        values["longitude"],
    )
    return get_vehicle(vehicle_id)


def delete_vehicle(vehicle_id: int):
    vehicle = dashboard_repository.get_vehicle(vehicle_id)
    if not vehicle:
        return None
    dashboard_repository.delete_vehicle(vehicle_id)
    return _format_vehicle(vehicle)


def _format_driver(driver):
    return {
        "id": driver["id"],
        "code": driver["code"],
        "name": driver["name"],
        "phone": driver["phone"] or "",
        "license_type": driver["license_type"] or "",
        "experience": int(driver["experience"] or 0),
        "rating": int(driver["rating"] or 0),
        "avatar": driver["avatar"],
        "status": driver["status"],
        "violations": int(driver["violations"] or 0),
        "monthly_violations": int(driver["monthly_violations"] or 0),
        "total_trips": int(driver["total_trips"] or 0),
    }


def _validate_driver_data(data):
    code = (data.get("code") or "").strip().upper()
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    license_number = (data.get("license_type") or "").strip().upper()
    status = (data.get("status") or "Đang làm việc").strip()

    if not code or not name or not phone or not license_number:
        raise ValueError("Vui lòng nhập đầy đủ mã, họ tên, SĐT và số GPLX")
    if len(code) > 20 or len(phone) > 20 or len(license_number) > 50:
        raise ValueError("Thông tin tài xế vượt quá độ dài cho phép")
    if status not in ALLOWED_DRIVER_STATUSES:
        raise ValueError("Trạng thái tài xế không hợp lệ")
    try:
        rating = int(data.get("rating") or 100)
        experience = int(data.get("experience") or 0)
        total_trips = int(data.get("total_trips") or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError("Điểm, kinh nghiệm hoặc số chuyến không hợp lệ") from exc
    if not 0 <= rating <= 100:
        raise ValueError("Điểm đánh giá phải từ 0 đến 100")
    if experience < 0 or total_trips < 0:
        raise ValueError("Kinh nghiệm và số chuyến không được là số âm")

    return {
        "code": code,
        "name": name,
        "phone": phone,
        "license_number": license_number,
        "rating": rating,
        "experience": experience,
        "total_trips": total_trips,
        "active": 1 if status == "Đang làm việc" else 0,
    }


def get_driver(driver_id: int):
    driver = dashboard_repository.get_driver(driver_id)
    return _format_driver(driver) if driver else None


def create_driver(data, avatar_filename=None):
    values = _validate_driver_data(data)
    driver_id = dashboard_repository.create_driver(
        values["code"],
        values["name"],
        values["phone"],
        values["license_number"],
        values["experience"],
        values["total_trips"],
        avatar_filename,
        values["rating"],
        values["active"],
    )
    return get_driver(driver_id)


def update_driver(driver_id: int, data, avatar_filename=None):
    current = dashboard_repository.get_driver(driver_id)
    if not current:
        return None
    values = _validate_driver_data(data)
    dashboard_repository.update_driver(
        driver_id,
        values["code"],
        values["name"],
        values["phone"],
        values["license_number"],
        values["experience"],
        values["total_trips"],
        avatar_filename if avatar_filename is not None else current["avatar"],
        values["rating"],
        values["active"],
    )
    return get_driver(driver_id)


def delete_driver(driver_id: int):
    driver = dashboard_repository.get_driver(driver_id)
    if not driver:
        return None
    dashboard_repository.delete_driver(driver_id)
    return _format_driver(driver)
