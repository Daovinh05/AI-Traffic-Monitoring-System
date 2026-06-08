"""Face and fatigue detector helpers."""

from __future__ import annotations

from backend.app.ai import runtime


def eye_aspect_ratio(eye):
    return runtime.eye_aspect_ratio(eye)


def detect_yawn(points):
    return runtime.detect_yawn(points)


def get_head_pose(points, frame_size):
    return runtime.get_head_pose(points, frame_size)
