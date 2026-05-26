"""Chatbot service adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def process_ai_chat_message(message, vehicle_id=None):
    return load_models_module().process_ai_chat_message(message, vehicle_id)


def generate_bot_response(message, vehicle_id=None):
    return load_models_module().generate_bot_response(message, vehicle_id)
