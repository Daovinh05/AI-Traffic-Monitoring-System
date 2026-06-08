"""Chatbot service adapter."""

from __future__ import annotations

from backend.app.ai import runtime


def process_ai_chat_message(message, vehicle_id=None):
    return runtime.process_ai_chat_message(message, vehicle_id)


def generate_bot_response(message, vehicle_id=None):
    return runtime.generate_bot_response(message, vehicle_id)
