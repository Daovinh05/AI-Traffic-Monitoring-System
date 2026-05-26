"""Traffic counter adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def stream():
    return load_models_module().traffic_monitor()


def counter_class():
    return load_models_module().MultipleObjectCounter


def reset_temporary_counts():
    return load_models_module().reset_temporary_counts()
