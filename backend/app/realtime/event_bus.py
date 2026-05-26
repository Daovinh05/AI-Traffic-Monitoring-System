"""Simple in-process event bus placeholder for future WebSocket/SSE migration."""

from __future__ import annotations

from collections import defaultdict


_subscribers = defaultdict(list)


def subscribe(event_name, handler):
    _subscribers[event_name].append(handler)


def publish(event_name, payload):
    for handler in list(_subscribers[event_name]):
        handler(payload)
