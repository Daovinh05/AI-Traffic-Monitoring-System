"""MQTT lifecycle adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_mqtt_client_module


def init_mqtt():
    return load_mqtt_client_module().init_mqtt()


def stop_mqtt():
    return load_mqtt_client_module().stop_mqtt()
