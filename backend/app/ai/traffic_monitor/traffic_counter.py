"""Traffic counter adapter."""

from __future__ import annotations

from backend.app.ai import runtime


def stream():
    return runtime.traffic_monitor()


def counter_class():
    return runtime.MultipleObjectCounter


def reset_temporary_counts():
    return runtime.reset_temporary_counts()
