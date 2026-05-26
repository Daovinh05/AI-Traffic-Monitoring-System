"""Alert and warning business logic."""

from __future__ import annotations

import math

from backend.app.repositories import alert_repository


def _format_alert(alert):
    return {
        "id": alert["id"],
        "type": alert["type"],
        "message": alert["message"],
        "level": alert["level"],
        "timestamp": alert["timestamp"].isoformat() if alert["timestamp"] else None,
        "vehicle_plate": alert["vehicle_plate"],
        "driver_name": alert["driver_name"],
        "is_read": bool(alert["is_read"]),
        "video_path": alert["video_path"],
    }


def get_driver_alert_page(driver_id: int, page: int, per_page: int = 10):
    total = alert_repository.count_driver_alerts(driver_id)
    offset = (page - 1) * per_page
    alerts = alert_repository.list_driver_alerts(driver_id, per_page, offset)
    return {
        "alerts": [_format_alert(alert) for alert in alerts],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": math.ceil(total / per_page) if per_page else 0,
    }


def get_all_alert_page(page: int, per_page: int = 15):
    total = alert_repository.count_all_alerts()
    offset = (page - 1) * per_page
    alerts = alert_repository.list_all_alerts(per_page, offset)
    return {
        "alerts": [_format_alert(alert) for alert in alerts],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": math.ceil(total / per_page) if per_page else 0,
    }


def send_admin_warning(admin_id, alert_id, plate: str, content: str, priority: str):
    plate = (plate or "").strip()
    content = (content or "").strip()
    if not plate or not content:
        return {"success": False, "message": "Vui lòng nhập đầy đủ thông tin", "status": 400}

    warning_id = alert_repository.create_admin_warning(
        admin_id, alert_id, plate, content, priority or "medium"
    )
    return {
        "success": True,
        "message": "Đã gửi cảnh báo thành công",
        "warning_id": warning_id,
        "status": 200,
    }
