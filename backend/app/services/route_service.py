"""Route management business logic."""

from __future__ import annotations

import json
import re
import ssl
import threading
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi

from backend.app.repositories import route_repository


ALLOWED_ROUTE_STATUSES = {"active", "waiting", "offline"}
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
HTTP_USER_AGENT = "AI-Traffic-Monitoring-System/1.0"
_geocode_cache = {}
_geocode_lock = threading.Lock()
_last_geocode_request = 0.0


def _float_or_none(value):
    return float(value) if value is not None else None


def _get_json(url, params=None):
    if params:
        url = f"{url}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "User-Agent": HTTP_USER_AGENT,
            "Accept": "application/json",
            "Accept-Language": "vi,en;q=0.8",
        },
    )
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    with urlopen(request, timeout=15, context=ssl_context) as response:
        return json.loads(response.read().decode("utf-8"))


def _geocode(address):
    global _last_geocode_request

    address = (address or "").strip()
    cache_key = address.casefold()
    if not address:
        raise ValueError("Vui lòng nhập đầy đủ điểm đi và điểm đến")

    coordinate_match = re.fullmatch(
        r"\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*",
        address,
    )
    if coordinate_match:
        latitude = float(coordinate_match.group(1))
        longitude = float(coordinate_match.group(2))
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("Tọa độ GPS không hợp lệ")
        return {
            "address": f"Vị trí GPS ({latitude:.6f}, {longitude:.6f})",
            "lat": latitude,
            "lng": longitude,
        }

    with _geocode_lock:
        if cache_key in _geocode_cache:
            return _geocode_cache[cache_key]

        address_parts = [part.strip() for part in address.split(",") if part.strip()]
        candidates = [address]
        if len(address_parts) >= 2:
            candidates.append(f"{address_parts[0]}, {address_parts[-1]}, Việt Nam")
        elif "việt nam" not in address.casefold():
            candidates.append(f"{address}, Việt Nam")

        results = []
        for candidate in dict.fromkeys(candidates):
            wait_time = 1.05 - (time.monotonic() - _last_geocode_request)
            if wait_time > 0:
                time.sleep(wait_time)
            results = _get_json(
                NOMINATIM_URL,
                {
                    "q": candidate,
                    "format": "jsonv2",
                    "limit": 1,
                    "countrycodes": "vn",
                    "addressdetails": 1,
                },
            )
            _last_geocode_request = time.monotonic()
            if results:
                break

        if not results:
            raise ValueError(f"Không tìm thấy địa chỉ: {address}")

        result = {
            "address": results[0]["display_name"],
            "lat": float(results[0]["lat"]),
            "lng": float(results[0]["lon"]),
        }
        _geocode_cache[cache_key] = result
        return result


def plan_route(start_address, end_address):
    start = _geocode(start_address)
    end = _geocode(end_address)
    coordinates = f"{start['lng']},{start['lat']};{end['lng']},{end['lat']}"
    result = _get_json(
        f"{OSRM_URL}/{coordinates}",
        {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
        },
    )
    if result.get("code") != "Ok" or not result.get("routes"):
        raise ValueError("Không tìm thấy đường lái xe phù hợp giữa hai địa điểm")

    route = result["routes"][0]
    path = [
        [float(latitude), float(longitude)]
        for longitude, latitude in route["geometry"]["coordinates"]
    ]
    return {
        "start": start,
        "end": end,
        "path": path,
        "distance": round(float(route["distance"]) / 1000, 1),
        "duration": max(1, round(float(route["duration"]) / 60)),
    }


def _format_route(route, path=None):
    return {
        "id": route["id"],
        "code": route["id"],
        "name": route["ten_tuyen"],
        "description": route["mo_ta"],
        "start": route.get("start_address") or "Chưa cập nhật địa chỉ",
        "end": route.get("end_address") or "Chưa cập nhật địa chỉ",
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
        "status": (
            "Hoạt động"
            if route.get("trang_thai") == "active"
            else "Chờ triển khai"
            if route.get("trang_thai") == "waiting"
            else "Ngừng hoạt động"
        ),
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
        "start_address": route.get("start_address"),
        "end_address": route.get("end_address"),
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
    if data.get("status", "active") not in ALLOWED_ROUTE_STATUSES:
        return "Trạng thái tuyến đường không hợp lệ"
    try:
        distance = float(data.get("distance") or 0)
        duration = int(data.get("duration") or 0)
        if distance < 0 or duration < 0:
            return "Khoảng cách và thời gian không được là số âm"
        for point in path:
            if len(point) != 2:
                return "Mỗi điểm tuyến đường phải gồm vĩ độ và kinh độ"
            latitude, longitude = float(point[0]), float(point[1])
            if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
                return "Tọa độ tuyến đường không hợp lệ"
    except (TypeError, ValueError):
        return "Khoảng cách, thời gian hoặc tọa độ không hợp lệ"
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
        (data.get("start_address") or "").strip(),
        (data.get("end_address") or "").strip(),
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
        (data.get("start_address") or "").strip(),
        (data.get("end_address") or "").strip(),
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
