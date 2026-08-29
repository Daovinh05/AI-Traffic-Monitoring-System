"""MQTT lifecycle adapter."""

from __future__ import annotations

from backend.app.mqtt import client


def init_mqtt():
    return client.init_mqtt()


def stop_mqtt():
    return client.stop_mqtt()
