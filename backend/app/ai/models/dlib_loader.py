"""Dlib model accessors."""

from __future__ import annotations

from backend.app.ai import runtime


def face_detector():
    return runtime.get_face_detector()


def shape_predictor():
    return runtime.get_shape_predictor()
