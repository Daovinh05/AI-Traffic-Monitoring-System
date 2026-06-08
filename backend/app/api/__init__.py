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


def validate_routes(app):
    missing = []
    for group, routes in ROUTE_GROUPS.items():
        for route in iter_missing_routes(app, routes):
            missing.append((group, route))
    return missing


def register_app_routes(app):
    """Register every feature route on the backend-owned Flask app."""
    for routes in ROUTE_GROUPS.values():
        for route in routes:
            if route.handler is None:
                raise RuntimeError(f"Route has no backend handler: {route.endpoint}")
            app.add_url_rule(
                route.rule,
                endpoint=route.endpoint,
                view_func=route.handler,
                methods=route.methods,
            )
