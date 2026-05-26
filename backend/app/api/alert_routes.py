"""Alert, warning, chatbot, and history API route group."""

from .route_registry import LegacyRoute


ROUTES = (
    LegacyRoute("/api/alerts", "get_alerts", "get_alerts"),
    LegacyRoute(
        "/api/alerts/<int:alert_id>/read",
        "mark_alert_as_read",
        "mark_alert_as_read",
        ("POST",),
    ),
    LegacyRoute("/api/videos", "get_videos", "get_videos"),
    LegacyRoute("/api/admin-warnings", "get_admin_warnings", "get_admin_warnings"),
    LegacyRoute("/api/all-alerts", "get_all_alerts", "get_all_alerts"),
    LegacyRoute(
        "/api/admin-warnings/<int:warning_id>/read",
        "mark_warning_as_read",
        "mark_warning_as_read",
        ("POST",),
    ),
    LegacyRoute(
        "/api/vehicle-cameras/<int:vehicle_id>",
        "get_vehicle_cameras",
        "get_vehicle_cameras",
    ),
    LegacyRoute("/api/send-warning", "send_warning_to_vehicle", "send_warning_to_vehicle", ("POST",)),
    LegacyRoute(
        "/api/mark-alert-processed",
        "mark_alert_as_processed",
        "mark_alert_as_processed",
        ("POST",),
    ),
    LegacyRoute("/api/get_ai_warnings", "api_get_ai_warnings", "api_get_ai_warnings"),
    LegacyRoute(
        "/api/get_ai_alerts_history",
        "api_get_ai_alerts_history",
        "api_get_ai_alerts_history",
    ),
    LegacyRoute(
        "/api/process_voice_command",
        "api_process_voice_command",
        "api_process_voice_command",
        ("POST",),
    ),
    LegacyRoute("/api/send_chat_message", "api_send_chat_message", "api_send_chat_message", ("POST",)),
    LegacyRoute("/api/groq_law_chat", "api_groq_law_chat", "api_groq_law_chat", ("POST",)),
)
