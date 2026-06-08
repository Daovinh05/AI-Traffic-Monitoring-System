"""Route management business logic."""

from __future__ import annotations

from backend.app.repositories import route_repository


def _float_or_none(value):
    return float(value) if value is not None else None


def _format_route(route, path=None):
    return {
        "id": route["id"],
        "code": route["id"],
        "name": route["ten_tuyen"],
        "description": route["mo_ta"],
        "start_lat": _float_or_none(route.get("start_lat")),
        "start_lng": _float_or_none(route.get("start_lng")),
        "end_lat": _float_or_none(route.get("end_lat")),
        "end_lng": _float_or_none(route.get("end_lng")),
        "distance": float(route.get("distance") or 0),
        "duration": int(route.get("duration") or 0),
        "vehicles": route.get("vehicles"),
        "color": route.get("route_color") or "#4a9eff",
        "center_lat": _float_or_none(route.get("toa_do_lat")),
        "center_lng": _float_or_none(route.get("toa_do_lng")),
        "status": "Hoạt động" if route.get("trang_thai") == "active" else "Ngừng hoạt động",
        "path": path or [],
    }


def list_routes():
    formatted = []
    for route in route_repository.list_routes():
        path = [
            [float(point["latitude"]), float(point["longitude"])]
            for point in route_repository.list_route_path(route["id"])
        ]
        formatted.append(_format_route(route, path))
    return formatted


def get_route_detail(route_id):
    route = route_repository.get_route(route_id)
    if not route:
        return None
    return {
        "id": route["id"],
        "name": route["ten_tuyen"],
        "description": route["mo_ta"],
        "start_lat": _float_or_none(route.get("start_lat")),
        "start_lng": _float_or_none(route.get("start_lng")),
        "end_lat": _float_or_none(route.get("end_lat")),
        "end_lng": _float_or_none(route.get("end_lng")),
        "center_lat": _float_or_none(route.get("toa_do_lat")),
        "center_lng": _float_or_none(route.get("toa_do_lng")),
        "status": route["trang_thai"],
    }


def validate_route_payload(data, require_path=False):
    route_id = (data.get("id") or "").strip()
    name = (data.get("name") or "").strip()
    path = data.get("path") or []
    if not name or (require_path and not route_id):
        return "Vui lòng nhập đầy đủ thông tin"
    if require_path and len(path) < 2:
        return "Tuyến đường cần ít nhất 2 điểm tọa độ"
    if path and len(path) < 2:
        return "Tuyến đường cần ít nhất 2 điểm tọa độ"
    return None


def create_route(data):
    error = validate_route_payload(data, require_path=True)
    if error:
        return {"success": False, "message": error, "status": 400}

    route_id = data["id"].strip()
    if route_repository.route_exists(route_id):
        return {
            "success": False,
            "message": "Mã tuyến đường đã tồn tại",
            "status": 400,
        }

    route_repository.create_route(
        route_id,
        data["name"].strip(),
        data.get("description", ""),
        data.get("distance", 0),
        data.get("duration", 0),
        data.get("vehicles", ""),
        data.get("color", "#4a9eff"),
        data.get("status", "active"),
        data["path"],
    )
    return {"success": True, "message": "Tạo tuyến đường thành công", "status": 200}


def update_route(route_id, data):
    error = validate_route_payload(data)
    if error:
        return {"success": False, "message": error, "status": 400}
    if not route_repository.route_exists(route_id):
        return {
            "success": False,
            "message": "Tuyến đường không tồn tại",
            "status": 404,
        }

    route_repository.update_route(
        route_id,
        data["name"].strip(),
        data.get("description", ""),
        data.get("distance", 0),
        data.get("duration", 0),
        data.get("vehicles", ""),
        data.get("color", "#4a9eff"),
        data.get("status", "active"),
        data.get("path") or [],
    )
    return {"success": True, "message": "Cập nhật tuyến đường thành công", "status": 200}


def delete_route(route_id):
    if not route_repository.route_exists(route_id):
        return {
            "success": False,
            "message": "Tuyến đường không tồn tại",
            "status": 404,
        }
    route_repository.delete_route(route_id)
    return {"success": True, "message": "Xóa tuyến đường thành công", "status": 200}
