"""Video recording state adapter."""

from __future__ import annotations

from backend.app.legacy.loaders import load_models_module


def state():
    models = load_models_module()
    return {
        "is_recording": models.is_recording,
        "recording_start_time": models.recording_start_time,
        "current_video_filename": models.current_video_filename,
        "current_video_path": models.current_video_path,
        "current_video_cam_id": models.current_video_cam_id,
    }
