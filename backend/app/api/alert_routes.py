"""Alert, warning, camera, chatbot, and history HTTP routes."""

from __future__ import annotations

from functools import wraps
import json
from queue import Empty
import re

from flask import Response, jsonify, request, session, stream_with_context

from backend.app.chatbot import chatbot_service, groq_client
from backend.app.repositories import alert_repository
from backend.app.realtime import admin_warning_stream
from backend.app.services import alert_service, video_service

from .route_registry import AppRoute


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify(success=False, message="Vui lòng đăng nhập"), 401
        return view(*args, **kwargs)

    return wrapped


@login_required
def get_alerts():
    driver_id = session.get("tai_xe_id")
    if not driver_id:
        return jsonify(success=False, message="Không tìm thấy thông tin tài xế"), 400
    try:
        page = request.args.get("page", 1, type=int)
        return jsonify(success=True, **alert_service.get_driver_alert_page(driver_id, page))
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


@login_required
def get_all_alerts():
    if session.get("role") != "admin":
        return jsonify(success=False, message="Không có quyền truy cập"), 403
    try:
        page = request.args.get("page", 1, type=int)
        plate = request.args.get("plate", "")
        return jsonify(
            success=True,
            **alert_service.get_all_alert_page(page, plate=plate),
        )
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


@login_required
def get_admin_warnings():
    driver_id = None
    if session.get("role") != "admin":
        driver_id = session.get("tai_xe_id")
        if not driver_id:
            return jsonify(
                success=False,
                message="Không tìm thấy thông tin tài xế",
            ), 400
    try:
        page = request.args.get("page", 1, type=int)
        plate = request.args.get("plate", "")
        return jsonify(
            success=True,
            **alert_service.get_admin_warning_page(
                page,
                driver_id,
                plate=plate,
            ),
        )
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


@login_required
def stream_admin_warnings():
    if session.get("role") == "admin":
        return jsonify(success=False, message="Luồng này chỉ dành cho tài xế"), 403

    driver_id = session.get("tai_xe_id")
    if not driver_id:
        return jsonify(success=False, message="Không tìm thấy thông tin tài xế"), 400

    @stream_with_context
    def generate():
        events = admin_warning_stream.subscribe(driver_id)
        try:
            yield "retry: 2000\n\n"
            while True:
                try:
                    warning = events.get(timeout=20)
                    payload = json.dumps(warning, ensure_ascii=False)
                    yield f"event: admin-warning\ndata: {payload}\n\n"
                except Empty:
                    yield ": keep-alive\n\n"
        finally:
            admin_warning_stream.unsubscribe(driver_id, events)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@login_required
def stream_admin_warning_acknowledgements():
    if session.get("role") != "admin":
        return jsonify(success=False, message="Không có quyền truy cập"), 403

    @stream_with_context
    def generate():
        events = admin_warning_stream.subscribe_admin()
        try:
            yield "retry: 2000\n\n"
            while True:
                try:
                    acknowledgement = events.get(timeout=20)
                    payload = json.dumps(acknowledgement, ensure_ascii=False)
                    yield f"event: warning-acknowledged\ndata: {payload}\n\n"
                except Empty:
                    yield ": keep-alive\n\n"
        finally:
            admin_warning_stream.unsubscribe_admin(events)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@login_required
def mark_alert_as_read(alert_id):
    try:
        alert_repository.mark_alert_read(alert_id)
        return jsonify(success=True, message="Đã đánh dấu đã đọc")
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


@login_required
def mark_warning_as_read(warning_id):
    try:
        if session.get("role") == "admin":
            alert_repository.mark_admin_warning_read(warning_id)
        else:
            driver_id = session.get("tai_xe_id")
            if not driver_id:
                return jsonify(
                    success=False,
                    message="Không tìm thấy thông tin tài xế",
                ), 400
            acknowledgement = alert_repository.acknowledge_driver_admin_warning(
                warning_id,
                driver_id,
            )
            if not acknowledgement:
                return jsonify(
                    success=False,
                    message="Không tìm thấy cảnh báo của tài xế",
                ), 404
            admin_warning_stream.publish_acknowledgement(acknowledgement)
            return jsonify(
                success=True,
                message="Đã xác nhận cảnh báo",
                alert_id=acknowledgement["alert_id"],
            )
        return jsonify(success=True, message="Đã đánh dấu đã đọc")
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


@login_required
def get_videos():
    try:
        return jsonify(success=True, videos=video_service.list_recorded_videos())
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


@login_required
def get_vehicle_cameras(vehicle_id):
    try:
        return jsonify(success=True, **video_service.get_vehicle_cameras(vehicle_id))
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


@login_required
def send_warning_to_vehicle():
    if session.get("role") != "admin":
        return jsonify(success=False, message="Không có quyền truy cập"), 403
    try:
        data = request.get_json(silent=True) or {}
        result = alert_service.send_admin_warning(
            session.get("user_id"),
            data.get("alert_id"),
            data.get("plate"),
            data.get("content"),
            data.get("priority", "medium"),
        )
        payload = {key: value for key, value in result.items() if key != "status"}
        return jsonify(payload), result["status"]
    except Exception as exc:
        return jsonify(success=False, message=f"Lỗi: {exc}"), 500


def api_get_ai_warnings():
    from backend.app.ai import runtime

    return jsonify(runtime.warnings)


def api_get_ai_alerts_history():
    from backend.app.ai import runtime

    with runtime.ai_alerts_lock:
        return jsonify(status="success", alerts=runtime.ai_alerts_queue[-20:])


def api_ai_status():
    from backend.app.ai import status

    return jsonify(status.snapshot())


def api_process_voice_command():
    try:
        data = request.get_json(silent=True) or {}
        command = data.get("command", "").lower()
        response = {"status": "success", "action": "unknown", "message": ""}

        if "hiển thị xe" in command or "tìm xe" in command:
            plate_match = re.search(
                r"(\d{1,2}[a-z]-\d{3}\.\d{2})",
                command,
                re.IGNORECASE,
            )
            if plate_match:
                plate = plate_match.group(0).upper()
                response.update(
                    action="focus_vehicle",
                    plate=plate,
                    message=f"Tìm xe biển số {plate}",
                )
            elif "gần nhất" in command:
                response.update(action="find_nearest", message="Tìm xe gần nhất")
            else:
                response.update(action="help", message="Vui lòng nói biển số xe")
        elif "camera" in command or "video" in command:
            response.update(action="open_camera", message="Mở camera tài xế")
        elif "hỗ trợ" in command or "chat" in command or "nhắn tin" in command:
            response.update(action="open_chat", message="Mở chat hỗ trợ")
        elif "cảnh báo" in command:
            response.update(action="show_alerts", message="Hiển thị cảnh báo")
        else:
            response["message"] = (
                "Không hiểu lệnh. Thử: hiển thị xe, mở camera, gọi hỗ trợ"
            )
        return jsonify(response)
    except Exception as exc:
        return jsonify(status="error", message=str(exc)), 400


def api_send_chat_message():
    try:
        data = request.get_json(silent=True) or {}
        response = chatbot_service.process_ai_chat_message(
            data.get("message", ""),
            data.get("vehicle_id"),
        )
        return jsonify(status="success", bot_response=response)
    except Exception as exc:
        return jsonify(status="error", message=str(exc)), 400


def api_groq_law_chat():
    try:
        data = request.get_json(silent=True) or {}
        response = groq_client.call_groq_law_advisor(data.get("message", ""))
        return jsonify(status="success", response=response)
    except Exception as exc:
        return jsonify(status="error", message=str(exc)), 400


ROUTES = (
    AppRoute("/api/alerts", "get_alerts", "get_alerts", handler=get_alerts),
    AppRoute(
        "/api/alerts/<int:alert_id>/read",
        "mark_alert_as_read",
        "mark_alert_as_read",
        ("POST",),
        handler=mark_alert_as_read,
    ),
    AppRoute("/api/videos", "get_videos", "get_videos", handler=get_videos),
    AppRoute(
        "/api/admin-warnings",
        "get_admin_warnings",
        "get_admin_warnings",
        handler=get_admin_warnings,
    ),
    AppRoute(
        "/api/admin-warnings/stream",
        "stream_admin_warnings",
        "stream_admin_warnings",
        handler=stream_admin_warnings,
    ),
    AppRoute(
        "/api/admin-warnings/admin-stream",
        "stream_admin_warning_acknowledgements",
        "stream_admin_warning_acknowledgements",
        handler=stream_admin_warning_acknowledgements,
    ),
    AppRoute(
        "/api/all-alerts",
        "get_all_alerts",
        "get_all_alerts",
        handler=get_all_alerts,
    ),
    AppRoute(
        "/api/admin-warnings/<int:warning_id>/read",
        "mark_warning_as_read",
        "mark_warning_as_read",
        ("POST",),
        handler=mark_warning_as_read,
    ),
    AppRoute(
        "/api/vehicle-cameras/<int:vehicle_id>",
        "get_vehicle_cameras",
        "get_vehicle_cameras",
        handler=get_vehicle_cameras,
    ),
    AppRoute(
        "/api/send-warning",
        "send_warning_to_vehicle",
        "send_warning_to_vehicle",
        ("POST",),
        handler=send_warning_to_vehicle,
    ),
    AppRoute(
        "/api/get_ai_warnings",
        "api_get_ai_warnings",
        "api_get_ai_warnings",
        handler=api_get_ai_warnings,
    ),
    AppRoute(
        "/api/get_ai_alerts_history",
        "api_get_ai_alerts_history",
        "api_get_ai_alerts_history",
        handler=api_get_ai_alerts_history,
    ),
    AppRoute(
        "/api/ai-status",
        "api_ai_status",
        "api_ai_status",
        handler=api_ai_status,
    ),
    AppRoute(
        "/api/process_voice_command",
        "api_process_voice_command",
        "api_process_voice_command",
        ("POST",),
        handler=api_process_voice_command,
    ),
    AppRoute(
        "/api/send_chat_message",
        "api_send_chat_message",
        "api_send_chat_message",
        ("POST",),
        handler=api_send_chat_message,
    ),
    AppRoute(
        "/api/groq_law_chat",
        "api_groq_law_chat",
        "api_groq_law_chat",
        ("POST",),
        handler=api_groq_law_chat,
    ),
)
