"""Voice command parser."""

from __future__ import annotations


def parse_command(command_text):
    text = (command_text or "").strip().lower()
    if "mở" in text or "bat" in text or "bật" in text:
        return {"type": "start", "raw": command_text}
    if "dừng" in text or "stop" in text or "tắt" in text:
        return {"type": "stop", "raw": command_text}
    return {"type": "unknown", "raw": command_text}
