"""Warning cooldown adapter."""

from __future__ import annotations

from backend.app.ai import runtime


def can_play_warning(warning_type):
    return runtime.can_play_warning(warning_type)
