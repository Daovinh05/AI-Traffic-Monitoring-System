"""Groq client adapter."""

from __future__ import annotations

from backend.app.ai import runtime


def call_llm_api(message, vehicle_id=None):
    return runtime.call_llm_api(message, vehicle_id)


def call_groq_law_advisor(question):
    return runtime.call_groq_law_advisor(question)
