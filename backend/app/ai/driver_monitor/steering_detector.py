"""Steering/hand detector adapter."""

from __future__ import annotations

from backend.app.ai import runtime


def can_play_hand_warning():
    return runtime.can_play_warning("hand")


def hand_tracking_class():
    return runtime.HandAndArmTracking
