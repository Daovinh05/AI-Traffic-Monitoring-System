"""MediaPipe accessors for the legacy runtime."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def hand_detector():
    return load_models_module().hand_detector


def hand_tracking_class():
    return load_models_module().HandAndArmTracking
