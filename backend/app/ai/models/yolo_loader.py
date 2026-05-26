"""YOLO model accessors for the legacy runtime."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def phone_model():
    return load_models_module().phone_mau


def seatbelt_model():
    return load_models_module().seatbelt_mau


def traffic_sign_model():
    return load_models_module().bienbao_model


def vehicle_model():
    return load_models_module().model_vehicle


def lane_model():
    return load_models_module().model_lane


def obstacle_model():
    return load_models_module().model_hole
