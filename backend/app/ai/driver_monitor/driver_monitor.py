"""Driver monitoring adapter."""

from __future__ import annotations

from backend.app.ai import runtime


def stream(vehicle_id=None):
    return runtime.driver_monitor(vehicle_id)


def hand_detector():
    return runtime.get_hand_detector()


def hand_tracking_class():
    return runtime.HandAndArmTracking
