"""MJPEG stream adapters."""

from __future__ import annotations

from backend.app.ai.driver_monitor.driver_monitor import stream as driver_stream
from backend.app.ai.traffic_monitor.collision_detector import stream as collision_stream
from backend.app.ai.traffic_monitor.sign_detector import stream as sign_stream
from backend.app.ai.traffic_monitor.traffic_counter import stream as traffic_stream

__all__ = ["driver_stream", "traffic_stream", "sign_stream", "collision_stream"]
