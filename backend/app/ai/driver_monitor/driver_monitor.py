"""Driver monitoring adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def stream(vehicle_id=None):
    return load_models_module().driver_monitor(vehicle_id)


def hand_detector():
    return load_models_module().hand_detector


def hand_tracking_class():
    return load_models_module().HandAndArmTracking
