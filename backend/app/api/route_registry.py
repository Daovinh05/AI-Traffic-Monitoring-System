"""Route declarations shared by feature modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass(frozen=True)
class AppRoute:
    rule: str
    endpoint: str
    view_name: str
    methods: tuple[str, ...] = ("GET",)
    handler: Callable | None = None


def iter_missing_routes(app, routes: Iterable[AppRoute]):
    existing = {
        (rule.rule, rule.endpoint)
        for rule in app.url_map.iter_rules()
    }
    for route in routes:
        if (route.rule, route.endpoint) not in existing:
            yield route
