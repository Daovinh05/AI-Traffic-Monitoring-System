"""Placeholder WebSocket manager.

The current UI polls HTTP endpoints. This module marks the future migration
point for WebSocket/SSE without changing current behavior.
"""

from __future__ import annotations


class WebSocketManager:
    def __init__(self):
        self.clients = set()

    def register(self, client):
        self.clients.add(client)

    def unregister(self, client):
        self.clients.discard(client)

    def broadcast(self, message):
        for client in list(self.clients):
            client.send(message)
