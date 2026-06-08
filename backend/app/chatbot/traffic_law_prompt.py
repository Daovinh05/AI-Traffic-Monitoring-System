"""Traffic law fallback response adapter."""

from __future__ import annotations

from backend.app.ai import runtime


def generate_law_response_fallback(question):
    return runtime.generate_law_response_fallback(question)
