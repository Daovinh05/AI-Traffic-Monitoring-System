"""YOLO model accessors."""

from __future__ import annotations

from backend.app.ai import runtime


def phone_model():
    return runtime.phone_mau


def seatbelt_model():
    return runtime.seatbelt_mau


def traffic_sign_model():
    return runtime.bienbao_model


def vehicle_model():
    return runtime.model_vehicle


def lane_model():
    return runtime.model_lane


def obstacle_model():
    return runtime.model_hole
