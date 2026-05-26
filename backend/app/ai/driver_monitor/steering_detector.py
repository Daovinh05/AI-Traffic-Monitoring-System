"""Steering/hand detector adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def can_play_hand_warning():
    return load_models_module().can_play_warning("hand")


def hand_tracking_class():
    return load_models_module().HandAndArmTracking
