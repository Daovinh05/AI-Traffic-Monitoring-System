"""Application service for alerts emitted by AI streams."""

from __future__ import annotations

from backend.app.mqtt import mqtt_publisher
from backend.app.repositories import alert_repository
from backend.app.repositories import user_repository


CRITICAL_ALERT_TYPES = {"eye", "phone", "seatbelt", "collision"}


def alert_level(alert_type: str) -> str:
    return "critical" if alert_type in CRITICAL_ALERT_TYPES else "warning"


AUTO_WARNING_MESSAGES = {
    "eye": "Tài xế có dấu hiệu nhắm mắt quá lâu, nguy cơ buồn ngủ. Yêu cầu dừng xe nghỉ ngơi ngay.",
    "yawn": "Tài xế ngáp ngủ, mất tỉnh táo. Yêu cầu dừng xe nghỉ ngơi hoặc chuyển ca.",
    "head": "Tài xế mất tập trung khi lái xe. Yêu cầu tập trung quan sát phía trước.",
    "phone": "Tài xế sử dụng điện thoại khi lái xe, vi phạm luật giao thông. Yêu cầu dừng ngay hành vi này.",
    "seatbelt": "Tài xế không thắt dây an toàn. Yêu cầu thắt dây an toàn ngay lập tức.",
    "hand": "Tài xế không giữ vô lăng bằng hai tay. Yêu cầu giữ vô lăng đúng cách.",
    "lane": "Phương tiện bị lệch làn đường. Yêu cầu giữ đúng làn đường quy định.",
    "collision": "Cảnh báo nguy cơ va chạm. Yêu cầu giảm tốc độ và giữ khoảng cách an toàn.",
    "obstacle": "Phát hiện vật cản phía trước. Yêu cầu giảm tốc độ và quan sát kỹ.",
    "sign": "Phát hiện biển báo giao thông quan trọng. Yêu cầu tuân thủ biển báo.",
    "speed": "Phương tiện chạy quá tốc độ quy định. Yêu cầu giảm tốc độ ngay lập tức.",
}

AUTO_WARNING_PRIORITY = {
    "eye": "high",
    "phone": "high",
    "seatbelt": "high",
    "collision": "high",
    "speed": "high",
    "yawn": "medium",
    "head": "medium",
    "hand": "medium",
    "lane": "medium",
    "obstacle": "medium",
    "sign": "low",
}


def _auto_warning_message(alert_type: str) -> str:
    return AUTO_WARNING_MESSAGES.get(alert_type, f"Phát hiện vi phạm: {alert_type}. Yêu cầu chấp hành luật giao thông.")


def _auto_warning_priority(alert_type: str) -> str:
    return AUTO_WARNING_PRIORITY.get(alert_type, "medium")


def _auto_create_admin_warning(alert_type: str, persisted: dict):
    admin = user_repository.find_first_admin()
    if not admin:
        return

    content = _auto_warning_message(alert_type)
    priority = _auto_warning_priority(alert_type)
    plate = persisted.get("plate", "")
    alert_id = persisted.get("id")

    alert_repository.create_admin_warning(
        admin_id=admin["id"],
        alert_id=alert_id,
        plate=plate,
        content=content,
        priority=priority,
    )


def publish_and_store(alert_type: str, message: str, vehicle_id=None):
    level = alert_level(alert_type)
    mqtt_publisher.publish_alert(alert_type, message, level)
    persisted = alert_repository.create_ai_alert(
        alert_type,
        message,
        level,
        vehicle_id,
    )
    result = {"level": level, **persisted}

    try:
        _auto_create_admin_warning(alert_type, persisted)
    except Exception as e:
        print(f"[AI] Auto warning error: {e}")

    return result
