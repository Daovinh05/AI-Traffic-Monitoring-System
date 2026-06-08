"""Application service for alerts emitted by AI streams."""

from __future__ import annotations

from backend.app.mqtt import mqtt_publisher
from backend.app.repositories import alert_repository


CRITICAL_ALERT_TYPES = {"eye", "phone", "seatbelt", "collision"}


def alert_level(alert_type: str) -> str:
    return "critical" if alert_type in CRITICAL_ALERT_TYPES else "warning"


def publish_and_store(alert_type: str, message: str, vehicle_id=None):
    level = alert_level(alert_type)
    mqtt_publisher.publish_alert(alert_type, message, level)
    persisted = alert_repository.create_ai_alert(
        alert_type,
        message,
        level,
        vehicle_id,
    )
    return {"level": level, **persisted}
