"""Video stream and monitoring control route group."""

from .route_registry import LegacyRoute


ROUTES = (
    LegacyRoute("/api/set_monitoring_vehicle", "set_monitoring_vehicle", "set_monitoring_vehicle", ("POST",)),
    LegacyRoute("/api/set_monitoring_vehicle", "api_set_monitoring_vehicle", "api_set_monitoring_vehicle", ("POST",)),
    LegacyRoute("/video_driver", "video_driver", "video_driver"),
    LegacyRoute("/video_traffic", "video_traffic", "video_traffic"),
    LegacyRoute("/video_sign", "video_sign", "video_sign"),
    LegacyRoute("/video_vacham", "video_vacham", "video_vacham"),
    LegacyRoute("/recordings/<path:filename>", "serve_video", "serve_video"),
    LegacyRoute("/change_region_points", "change_region_points", "change_region_points", ("POST",)),
    LegacyRoute("/toggle_warning", "toggle_warning", "toggle_warning", ("POST",)),
    LegacyRoute("/get_warnings", "get_warnings", "get_warnings"),
    LegacyRoute("/get_latest_sign_image", "get_latest_sign_image", "get_latest_sign_image"),
    LegacyRoute("/get_stats", "get_stats", "get_stats"),
    LegacyRoute("/set_mode", "set_mode", "set_mode", ("POST",)),
    LegacyRoute("/start_recording", "start_recording", "start_recording"),
    LegacyRoute("/stop_recording", "stop_recording", "stop_recording"),
    LegacyRoute("/get_video_source/<region_type>", "get_video_source", "get_video_source"),
)
