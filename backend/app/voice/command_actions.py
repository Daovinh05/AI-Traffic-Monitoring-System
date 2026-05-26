"""Voice command actions."""

from __future__ import annotations


def execute_action(action, context):
    return {
        "success": action["type"] != "unknown",
        "action": action["type"],
        "raw": action["raw"],
        "context": context,
    }
