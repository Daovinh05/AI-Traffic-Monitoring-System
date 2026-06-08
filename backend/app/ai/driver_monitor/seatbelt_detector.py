"""Seatbelt detector adapter."""

from __future__ import annotations

from backend.app.ai import runtime


def model():
    return runtime.seatbelt_mau
