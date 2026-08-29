"""MediaPipe accessors."""

from __future__ import annotations

from backend.app.ai import runtime


def hand_detector():
    return runtime.get_hand_detector()


def hand_tracking_class():
    return runtime.HandAndArmTracking
