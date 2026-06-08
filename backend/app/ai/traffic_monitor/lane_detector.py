"""Lane detection adapter."""

from __future__ import annotations

from backend.app.ai import runtime


def estimate_distance(y1, y2):
    return runtime.estimate_distance(y1, y2)


def is_in_center_lane(x, width, margin=100):
    return runtime.is_in_center_lane(x, width, margin)


def draw_lane_points(image, results_l, width):
    return runtime.draw_lane_points(image, results_l, width)


def draw_lane_classic(image):
    return runtime.draw_lane_classic(image)


def detect_lane_deviation_combined(results_l, frame, width, classic_lines):
    return runtime.detect_lane_deviation_combined(
        results_l, frame, width, classic_lines
    )
