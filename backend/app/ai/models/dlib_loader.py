"""Dlib model accessors."""

from __future__ import annotations

from backend.app.ai import runtime


def face_detector():
    return runtime.detector


def shape_predictor():
    return runtime.predictor
