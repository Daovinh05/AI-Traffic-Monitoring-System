"""Auth and page-entry route group.

Routes are still served by legacy view functions from ``py/Web/drive_auth.py``.
This module records the group boundaries so endpoints can be migrated without
renaming URLs or changing existing templates.
"""

from .route_registry import LegacyRoute


ROUTES = (
    LegacyRoute("/", "index_page", "index_page"),
    LegacyRoute("/login", "login_page", "login_page"),
    LegacyRoute("/api/login", "api_login", "api_login", ("POST",)),
    LegacyRoute("/api/logout", "api_logout", "api_logout", ("POST",)),
    LegacyRoute("/api/check-auth", "check_auth", "check_auth"),
)
