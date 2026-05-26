"""Dlib model accessors for the legacy runtime."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def face_detector():
    return load_models_module().detector


def shape_predictor():
    return load_models_module().predictor
