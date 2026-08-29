"""Video stream and monitoring-control HTTP handlers."""

from __future__ import annotations

from functools import wraps
from datetime import datetime
from pathlib import Path
import os
import shutil
import subprocess
import threading
import time

import cv2

from flask import Response, jsonify, request, send_file, session

from backend.app.repositories import recording_repository

from .route_registry import AppRoute


ROOT_DIR = Path(__file__).resolve().parents[3]
MAX_RECORDING_SECONDS = 10


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify(success=False, message="Vui lòng đăng nhập"), 401
        return view(*args, **kwargs)

    return wrapped


@login_required
def set_monitoring_vehicle():
    from backend.app.ai import runtime

    data = request.get_json(silent=True) or {}
    vehicle_id = data.get("vehicle_id")
    runtime.current_monitoring_vehicle_id = int(vehicle_id) if vehicle_id else None
    return jsonify(
        success=True,
        vehicle_id=runtime.current_monitoring_vehicle_id,
    )


def api_set_monitoring_vehicle():
    from backend.app.ai import runtime

    try:
        vehicle_id = (request.get_json(silent=True) or {}).get("vehicle_id")
        runtime.current_monitoring_vehicle_id = vehicle_id
        return jsonify(
            status="success",
            vehicle_id=vehicle_id,
            message=f"Đang giám sát xe {vehicle_id}",
        )
    except Exception as exc:
        return jsonify(status="error", message=str(exc)), 400


def video_driver():
    from backend.app.ai import runtime

    vehicle_id = session.get("vehicle_id") or runtime.current_monitoring_vehicle_id
    return Response(
        runtime.driver_monitor(vehicle_id),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def video_traffic():
    from backend.app.ai import runtime

    vehicle_id = session.get("vehicle_id") or runtime.current_monitoring_vehicle_id
    return Response(
        runtime.traffic_sign_monitor(vehicle_id),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def video_vacham():
    from backend.app.ai import runtime

    return Response(
        runtime.collision_monitor(session.get("vehicle_id")),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def video_sign():
    from backend.app.ai import runtime

    location_id = request.args.get("location")
    if location_id and location_id in runtime.location_video_map:
        region_type = runtime.location_video_map[location_id]
        runtime.current_location_id = location_id
        if region_type != runtime.current_region_type:
            runtime.active_video_stream = None
            time.sleep(0.5)
            if runtime.video_capture is not None:
                runtime.video_capture.release()

            runtime.current_region_type = region_type
            region_data = runtime.get_region_points(region_type)
            runtime.video_capture = cv2.VideoCapture(region_data["video_source"])
            runtime.counter = runtime.MultipleObjectCounter(
                regions=region_data["regions"],
                classes=[2, 3, 5, 7],
            )
            runtime.active_video_stream = "traffic"

    return Response(
        runtime.traffic_monitor(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


def serve_video(filename):
    candidates = (
        ROOT_DIR / "recordings" / filename,
        ROOT_DIR / "backend" / "assets" / "videos" / filename,
    )
    for path in candidates:
        if path.is_file():
            return send_file(path, mimetype="video/mp4", conditional=True)
    return "Video not found", 404


def serve_sound(filename):
    path = ROOT_DIR / "backend" / "assets" / "sounds" / filename
    if path.is_file():
        return send_file(path)
    return "Sound not found", 404


@login_required
def change_region_points():
    from backend.app.ai import runtime

    try:
        data = request.get_json(silent=True) or {}
        region_type = data.get("type")
        location_id = data.get("location")

        if location_id and location_id in runtime.location_video_map:
            region_type = runtime.location_video_map[location_id]
            runtime.current_location_id = location_id
        elif region_type in runtime.location_video_map.values():
            runtime.current_location_id = next(
                key
                for key, value in runtime.location_video_map.items()
                if value == region_type
            )
        else:
            return jsonify(status="error", message="Invalid region type")

        runtime.active_video_stream = None
        time.sleep(1)
        if runtime.video_capture is not None:
            runtime.video_capture.release()

        region_data = runtime.get_region_points(region_type)
        video_source = Path(region_data["video_source"])
        if not video_source.is_file():
            return jsonify(
                status="error",
                message=f"Không tìm thấy file video: {video_source}",
            )

        capture = cv2.VideoCapture(str(video_source))
        if not capture.isOpened():
            return jsonify(
                status="error",
                message=f"Không thể mở video: {video_source}",
            )
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 560)
        capture.set(cv2.CAP_PROP_FPS, 20)

        runtime.current_region_type = region_type
        runtime.video_capture = capture
        runtime.counter = runtime.MultipleObjectCounter(
            regions=region_data["regions"],
            classes=[2, 3, 5, 7],
        )
        runtime.active_video_stream = "traffic"
        return jsonify(status="success")
    except Exception as exc:
        return jsonify(status="error", message=str(exc))


@login_required
def toggle_warning():
    from backend.app.ai import runtime

    data = request.get_json(silent=True) or {}
    warning_type = data.get("warning_type")
    if warning_type not in runtime.warning_states:
        return jsonify(status="error", message="Invalid warning type")
    enabled = data.get("enabled", True)
    runtime.warning_states[warning_type] = enabled
    return jsonify(status="success", enabled=enabled)


@login_required
def get_warnings():
    from backend.app.ai import runtime

    payload = runtime.warnings.copy()
    payload["sign_image"] = runtime.latest_sign_image_path
    payload["sign_label"] = runtime.latest_sign_label
    return jsonify(payload)


@login_required
def get_latest_sign_image():
    from backend.app.ai import runtime

    path = runtime.latest_sign_image_path
    if path and Path(path).is_file():
        return send_file(path, mimetype="image/jpeg")
    return "", 404


def _default_stats():
    return {
        "total_vehicles": 0,
        "lane_counts": [],
        "vehicle_types": {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0},
        "region_details": [],
        "traffic_status": {
            "level": "normal",
            "message": "Giao thông thông thoáng, di chuyển bình thường",
            "color": "green",
        },
    }


@login_required
def get_stats():
    from backend.app.ai import runtime

    defaults = _default_stats()
    if runtime.counter is None:
        return jsonify(defaults)

    stats = runtime.counter.get_stats() or {}
    defaults.update(stats)
    defaults["vehicle_types"] = stats.get("vehicle_types") or defaults["vehicle_types"]
    defaults["region_details"] = stats.get("region_details") or defaults["region_details"]
    defaults["traffic_status"] = stats.get("traffic_status") or defaults["traffic_status"]
    return jsonify(defaults)


@login_required
def set_mode():
    from backend.app.ai import runtime

    try:
        runtime.active_video_stream = None
        time.sleep(0.5)
        runtime.current_mode = (request.get_json(silent=True) or {}).get(
            "mode",
            "driver",
        )
        return jsonify(status="success")
    except Exception as exc:
        return jsonify(status="error", message=str(exc))


@login_required
def start_recording():
    from backend.app.ai import runtime

    section_id = request.args.get("section_id", "driver")
    vehicle_id = session.get("vehicle_id") or runtime.current_monitoring_vehicle_id

    with runtime.recording_lock:
        if runtime.is_recording:
            return jsonify(success=False, message="Hệ thống đang ghi hình"), 409

        runtime.current_video_cam_id = {
            "driver": 1,
            "vacham": 2,
            "traffic": 3,
            "sign": 4,
        }.get(section_id, 1)
        runtime.current_video_filename = (
            f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        )
        path = ROOT_DIR / "recordings" / runtime.current_video_filename
        path.parent.mkdir(parents=True, exist_ok=True)
        runtime.current_video_path = str(path)
        runtime.video_writer = cv2.VideoWriter(
            str(path),
            runtime.video_codec,
            runtime.fps,
            (runtime.frame_width, runtime.frame_height),
        )
        if not runtime.video_writer.isOpened():
            runtime.video_writer = None
            runtime.current_video_path = None
            runtime.current_video_filename = None
            return jsonify(
                success=False,
                message="Không thể khởi tạo file ghi hình",
            ), 500

        runtime.is_recording = True
        runtime.recording_start_time = datetime.now()
        runtime.recording_frame_count = 0
        runtime.recording_timer = threading.Timer(
            MAX_RECORDING_SECONDS,
            _auto_stop_recording,
            args=(vehicle_id,),
        )
        runtime.recording_timer.daemon = True
        runtime.recording_timer.start()

    return jsonify(
        success=True,
        message=f"Đã bắt đầu ghi hình, tự động dừng sau {MAX_RECORDING_SECONDS} giây",
        filename=runtime.current_video_filename,
    )


def _finish_recording(vehicle_id=None):
    from backend.app.ai import runtime

    with runtime.recording_lock:
        if not runtime.is_recording or runtime.video_writer is None:
            return None

        timer = runtime.recording_timer
        runtime.recording_timer = None
        if timer is not None and timer is not threading.current_thread():
            timer.cancel()

        runtime.video_writer.release()
        runtime.video_writer = None
        runtime.is_recording = False
        recording = {
            "camera_id": runtime.current_video_cam_id,
            "filename": runtime.current_video_filename,
            "path": runtime.current_video_path,
            "started_at": runtime.recording_start_time,
            "frame_count": runtime.recording_frame_count,
        }

    ended_at = datetime.now()
    path = Path(recording["path"])
    if recording["frame_count"] <= 0:
        if path.is_file():
            path.unlink()
        raise ValueError("Không nhận được khung hình nào từ camera")

    _optimize_video_for_browser(path)
    file_size = path.stat().st_size if path.is_file() else 0
    video_id = recording_repository.save_recording(
        recording["camera_id"],
        recording["filename"],
        f"/recordings/{recording['filename']}",
        recording["started_at"],
        ended_at,
        file_size,
        vehicle_id,
    )
    return {
        "video_id": video_id,
        "video_path": f"/recordings/{recording['filename']}",
    }


def _optimize_video_for_browser(path: Path):
    converter = shutil.which("avconvert")
    if not converter:
        return

    converted_path = path.with_suffix(".web.m4v")
    try:
        subprocess.run(
            [
                converter,
                "--source",
                str(path),
                "--preset",
                "PresetAppleM4V720pHD",
                "--output",
                str(converted_path),
                "--replace",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if converted_path.is_file() and converted_path.stat().st_size > 0:
            os.replace(converted_path, path)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[VIDEO] Browser optimization skipped: {exc}")
    finally:
        if converted_path.is_file():
            converted_path.unlink()


def _auto_stop_recording(vehicle_id=None):
    try:
        _finish_recording(vehicle_id)
    except Exception as exc:
        print(f"[VIDEO] Automatic recording failed: {exc}")


@login_required
def stop_recording():
    from backend.app.ai import runtime

    vehicle_id = session.get("vehicle_id") or runtime.current_monitoring_vehicle_id
    try:
        recording = _finish_recording(vehicle_id)
        if recording is None:
            return jsonify(success=False, message="Hệ thống chưa ghi hình"), 409
        return jsonify(
            success=True,
            message="Đã dừng và lưu video",
            **recording,
        )
    except Exception as exc:
        return jsonify(
            success=False,
            message=f"Không thể lưu video: {exc}",
        ), 500


@login_required
def stop_camera():
    from backend.app.ai import runtime

    try:
        runtime.active_video_stream = None
        if runtime.video_capture is not None:
            runtime.video_capture.release()
            runtime.video_capture = None
        return jsonify(success=True, message="Đã dừng camera")
    except Exception as exc:
        return jsonify(success=False, message=str(exc)), 500


@login_required
def get_video_source(region_type):
    from backend.app.ai import runtime

    try:
        return jsonify(video_source=runtime.get_region_points(region_type)["video_source"])
    except Exception as exc:
        return jsonify(error=str(exc)), 400


ROUTES = (
    AppRoute(
        "/api/set_monitoring_vehicle",
        "set_monitoring_vehicle",
        "set_monitoring_vehicle",
        ("POST",),
        handler=set_monitoring_vehicle,
    ),
    AppRoute(
        "/api/set_monitoring_vehicle",
        "api_set_monitoring_vehicle",
        "api_set_monitoring_vehicle",
        ("POST",),
        handler=api_set_monitoring_vehicle,
    ),
    AppRoute("/video_driver", "video_driver", "video_driver", handler=video_driver),
    AppRoute(
        "/video_traffic",
        "video_traffic",
        "video_traffic",
        handler=video_traffic,
    ),
    AppRoute("/video_sign", "video_sign", "video_sign", handler=video_sign),
    AppRoute(
        "/video_vacham",
        "video_vacham",
        "video_vacham",
        handler=video_vacham,
    ),
    AppRoute(
        "/recordings/<path:filename>",
        "serve_video",
        "serve_video",
        handler=serve_video,
    ),
    AppRoute(
        "/sound/<path:filename>",
        "serve_sound",
        "serve_sound",
        handler=serve_sound,
    ),
    AppRoute(
        "/change_region_points",
        "change_region_points",
        "change_region_points",
        ("POST",),
        handler=change_region_points,
    ),
    AppRoute(
        "/toggle_warning",
        "toggle_warning",
        "toggle_warning",
        ("POST",),
        handler=toggle_warning,
    ),
    AppRoute("/get_warnings", "get_warnings", "get_warnings", handler=get_warnings),
    AppRoute(
        "/get_latest_sign_image",
        "get_latest_sign_image",
        "get_latest_sign_image",
        handler=get_latest_sign_image,
    ),
    AppRoute("/get_stats", "get_stats", "get_stats", handler=get_stats),
    AppRoute(
        "/set_mode",
        "set_mode",
        "set_mode",
        ("POST",),
        handler=set_mode,
    ),
    AppRoute(
        "/start_recording",
        "start_recording",
        "start_recording",
        handler=start_recording,
    ),
    AppRoute(
        "/stop_recording",
        "stop_recording",
        "stop_recording",
        handler=stop_recording,
    ),
    AppRoute("/stop_camera", "stop_camera", "stop_camera", handler=stop_camera),
    AppRoute(
        "/get_video_source/<region_type>",
        "get_video_source",
        "get_video_source",
        handler=get_video_source,
    ),
)
