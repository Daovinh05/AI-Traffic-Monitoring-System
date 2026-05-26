"""Route-management API route group."""

from .route_registry import LegacyRoute


ROUTES = (
    LegacyRoute("/api/routes", "get_routes", "get_routes"),
    LegacyRoute("/api/routes/<route_id>", "get_route_detail", "get_route_detail"),
    LegacyRoute("/api/routes", "create_route", "create_route", ("POST",)),
    LegacyRoute("/api/routes/<route_id>", "update_route", "update_route", ("PUT",)),
    LegacyRoute("/api/routes/<route_id>", "delete_route", "delete_route", ("DELETE",)),
)
