"""MQTT publisher adapter."""

from __future__ import annotations

from backend.app.mqtt import client


def publish_alert(alert_type, message, level="warning"):
    return client.publish_alert(alert_type, message, level)


def get_status():
    return client.get_status()
