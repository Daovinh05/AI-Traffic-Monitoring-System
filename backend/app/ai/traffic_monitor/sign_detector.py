"""Traffic sign detector adapter."""

from __future__ import annotations

from backend.app.ai import runtime


def stream(vehicle_id=None):
    return runtime.traffic_sign_monitor(vehicle_id)


def latest_sign():
    models = runtime
    return {
        "path": models.latest_sign_image_path,
        "label": models.latest_sign_label,
    }
