"""YOLO model accessors."""

from __future__ import annotations

from backend.app.ai import runtime


def phone_model():
    return runtime.get_phone_model()


def seatbelt_model():
    return runtime.get_seatbelt_model()


def traffic_sign_model():
    return runtime.get_traffic_sign_model()


def vehicle_model():
    return runtime.get_vehicle_model()


def lane_model():
    return runtime.get_lane_model()


def obstacle_model():
    return runtime.get_obstacle_model()
