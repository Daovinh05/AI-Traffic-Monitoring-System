"""Collision detector adapter."""

from __future__ import annotations

from backend.app.ai import runtime


def stream(vehicle_id=None):
    return runtime.collision_monitor(vehicle_id)
