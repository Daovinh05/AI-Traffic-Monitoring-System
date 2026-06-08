"""Traffic law fallback response adapter."""

from __future__ import annotations


def generate_law_response_fallback(question):
    from backend.app.ai import runtime

    return runtime.generate_law_response_fallback(question)
