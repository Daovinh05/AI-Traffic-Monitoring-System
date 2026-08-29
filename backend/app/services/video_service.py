"""Video and camera service helpers."""

from __future__ import annotations

import os
from datetime import datetime

from backend.app.repositories import camera_repository


DEFAULT_CAMERAS = {
    "tai_xe": {"ten": "Camera Tài Xế", "video": "ca_bin.mp4"},
    "truoc": {"ten": "Camera Trước", "video": "lech_lan.mp4"},
    "hanh_khach": {"ten": "Camera Hành Khách", "video": "passenger.mp4"},
    "lui": {"ten": "Camera Lùi", "video": "car1.mp4"},
}


def get_vehicle_cameras(vehicle_id: int):
    cameras = camera_repository.list_active_vehicle_cameras(vehicle_id)
    if not cameras:
        return {"vehicle_id": vehicle_id, "plate": "", "driver": "", "cameras": DEFAULT_CAMERAS}

    cam_dict = {}
    plate = ""
    driver = ""
    for cam in cameras:
        plate = cam["bien_so"]
        driver = cam["driver_name"] or ""
        cam_dict[cam["vi_tri"]] = {"ten": cam["ten_camera"], "video": cam["video_file"]}
    return {"vehicle_id": vehicle_id, "plate": plate, "driver": driver, "cameras": cam_dict}


def list_recorded_videos(video_dir: str = "recordings", limit: int = 50):
    videos = []
    if os.path.exists(video_dir):
        for filename in os.listdir(video_dir):
            if not filename.endswith(".mp4"):
                continue
            filepath = os.path.join(video_dir, filename)
            stat = os.stat(filepath)
            videos.append(
                {
                    "id": filename,
                    "title": filename.replace(".mp4", "").replace("_", " ").title(),
                    "path": f"/{filepath}",
                    "thumbnail": "/static/video-thumbnail.png",
                    "timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "duration": "N/A",
                    "size": stat.st_size,
                }
            )
    videos.sort(key=lambda item: item["timestamp"], reverse=True)
    return videos[:limit]
