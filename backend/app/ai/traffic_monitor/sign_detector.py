"""Traffic sign detector adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def stream(vehicle_id=None):
    return load_models_module().traffic_sign_monitor(vehicle_id)


def latest_sign():
    models = load_models_module()
    return {
        "path": models.latest_sign_image_path,
        "label": models.latest_sign_label,
    }
