"""Voice command service adapter."""

from __future__ import annotations


def process_command(command_text, context=None):
    from backend.app.voice.command_parser import parse_command
    from backend.app.voice.command_actions import execute_action

    action = parse_command(command_text)
    return execute_action(action, context or {})
