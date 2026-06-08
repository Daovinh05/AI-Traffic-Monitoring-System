"""Realtime alert queue adapter."""

from __future__ import annotations

from backend.app.ai import runtime


def add_alert(alert_type, message, vehicle_id=None):
    return runtime.add_ai_alert(alert_type, message, vehicle_id)


def history():
    models = runtime
    with models.ai_alerts_lock:
        return list(models.ai_alerts_queue)
