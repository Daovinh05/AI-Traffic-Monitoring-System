"""Phone detector adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def model():
    return load_models_module().phone_mau
