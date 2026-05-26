"""Traffic law fallback response adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def generate_law_response_fallback(question):
    return load_models_module().generate_law_response_fallback(question)
