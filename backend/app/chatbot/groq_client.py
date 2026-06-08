"""Groq client adapter."""

from __future__ import annotations


def call_llm_api(message, vehicle_id=None):
    from backend.app.ai import runtime

    return runtime.call_llm_api(message, vehicle_id)


def call_groq_law_advisor(question):
    from backend.app.ai import runtime

    return runtime.call_groq_law_advisor(question)
