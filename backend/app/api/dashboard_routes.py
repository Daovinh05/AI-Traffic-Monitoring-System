"""Dashboard and page render route group."""

from .route_registry import LegacyRoute


ROUTES = (
    LegacyRoute("/dashboard", "dashboard", "dashboard"),
    LegacyRoute("/trang_chu", "trang_chu_page", "trang_chu_page"),
    LegacyRoute("/tu_van", "tu_van_page", "tu_van_page"),
    LegacyRoute("/tu_van.html", "tu_van_html", "tu_van_html"),
    LegacyRoute("/lai_xe", "lai_xe_page", "lai_xe_page"),
    LegacyRoute("/lai_xe_v2", "lai_xe_v2_page", "lai_xe_v2_page"),
    LegacyRoute("/lich_su", "lich_su_page", "lich_su_page"),
    LegacyRoute("/traffic_bus", "traffic_bus", "traffic_bus"),
)
