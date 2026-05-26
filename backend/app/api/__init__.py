"""HTTP route modules grouped by feature."""

from . import alert_routes, auth_routes, dashboard_routes, route_routes, stream_routes
from .route_registry import iter_missing_routes

ROUTE_GROUPS = {
    "auth": auth_routes.ROUTES,
    "dashboard": dashboard_routes.ROUTES,
    "alerts": alert_routes.ROUTES,
    "stream": stream_routes.ROUTES,
    "routes": route_routes.ROUTES,
}


def validate_legacy_routes(app):
    missing = []
    for group, routes in ROUTE_GROUPS.items():
        for route in iter_missing_routes(app, routes):
            missing.append((group, route))
    return missing
