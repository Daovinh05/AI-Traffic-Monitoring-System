"""In-process Server-Sent Events broker for admin warnings."""

from __future__ import annotations

from collections import defaultdict
from queue import Queue
from threading import Lock


_subscribers: dict[int, set[Queue]] = defaultdict(set)
_admin_subscribers: set[Queue] = set()
_lock = Lock()


def subscribe(driver_id: int) -> Queue:
    events = Queue()
    with _lock:
        _subscribers[driver_id].add(events)
    return events


def unsubscribe(driver_id: int, events: Queue) -> None:
    with _lock:
        subscribers = _subscribers.get(driver_id)
        if not subscribers:
            return
        subscribers.discard(events)
        if not subscribers:
            _subscribers.pop(driver_id, None)


def publish(driver_id: int | None, warning: dict) -> None:
    if not driver_id:
        return
    with _lock:
        subscribers = list(_subscribers.get(driver_id, ()))
    for events in subscribers:
        events.put(warning)


def subscribe_admin() -> Queue:
    events = Queue()
    with _lock:
        _admin_subscribers.add(events)
    return events


def unsubscribe_admin(events: Queue) -> None:
    with _lock:
        _admin_subscribers.discard(events)


def publish_acknowledgement(acknowledgement: dict) -> None:
    with _lock:
        subscribers = list(_admin_subscribers)
    for events in subscribers:
        events.put(acknowledgement)
