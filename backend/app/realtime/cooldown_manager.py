"""Warning cooldown adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def can_play_warning(warning_type):
    return load_models_module().can_play_warning(warning_type)
