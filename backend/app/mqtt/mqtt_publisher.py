"""MQTT publisher adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_mqtt_client_module


def publish_alert(alert_type, message, level="warning"):
    return load_mqtt_client_module().publish_alert(alert_type, message, level)


def get_status():
    return load_mqtt_client_module().get_status()
