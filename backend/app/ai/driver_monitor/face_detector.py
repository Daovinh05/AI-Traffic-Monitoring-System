"""Face and fatigue detector helpers."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def eye_aspect_ratio(eye):
    return load_models_module().eye_aspect_ratio(eye)


def detect_yawn(points):
    return load_models_module().detect_yawn(points)


def get_head_pose(points, frame_size):
    return load_models_module().get_head_pose(points, frame_size)
