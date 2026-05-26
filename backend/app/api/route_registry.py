"""Helpers for grouping legacy routes during gradual migration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass(frozen=True)
class LegacyRoute:
    rule: str
    endpoint: str
    view_name: str
    methods: tuple[str, ...] = ("GET",)


def iter_missing_routes(app, routes: Iterable[LegacyRoute]):
    existing = {
        (rule.rule, rule.endpoint)
        for rule in app.url_map.iter_rules()
    }
    for route in routes:
        if (route.rule, route.endpoint) not in existing:
            yield route


def resolve_view(legacy_module, route: LegacyRoute) -> Callable:
    return getattr(legacy_module, route.view_name)
