"""Realtime alert queue adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def add_alert(alert_type, message, vehicle_id=None):
    return load_models_module().add_ai_alert(alert_type, message, vehicle_id)


def history():
    models = load_models_module()
    with models.ai_alerts_lock:
        return list(models.ai_alerts_queue)
