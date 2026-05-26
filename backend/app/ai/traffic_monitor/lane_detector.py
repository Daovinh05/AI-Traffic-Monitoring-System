"""Lane detection adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def estimate_distance(y1, y2):
    return load_models_module().estimate_distance(y1, y2)


def is_in_center_lane(x, width, margin=100):
    return load_models_module().is_in_center_lane(x, width, margin)


def draw_lane_points(image, results_l, width):
    return load_models_module().draw_lane_points(image, results_l, width)


def draw_lane_classic(image):
    return load_models_module().draw_lane_classic(image)


def detect_lane_deviation_combined(results_l, frame, width, classic_lines):
    return load_models_module().detect_lane_deviation_combined(
        results_l, frame, width, classic_lines
    )
