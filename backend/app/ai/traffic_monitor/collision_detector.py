"""Collision detector adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def stream(vehicle_id=None):
    return load_models_module().collision_monitor(vehicle_id)
