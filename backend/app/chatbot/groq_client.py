"""Groq client adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def call_llm_api(message, vehicle_id=None):
    return load_models_module().call_llm_api(message, vehicle_id)


def call_groq_law_advisor(question):
    return load_models_module().call_groq_law_advisor(question)
