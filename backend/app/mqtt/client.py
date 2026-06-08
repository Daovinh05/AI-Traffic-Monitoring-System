"""MQTT client for ESP32 traffic alerts.

Hỗ trợ các loại cảnh báo:
- eye: Nhắm mắt quá lâu (critical)
- yawn: Ngáp ngủ (warning)
- head: Mất tập trung (warning)
- phone: Dùng điện thoại (critical)
- seatbelt: Không đeo dây an toàn (critical)
- hand: Không cầm vô lăng (warning)
- collision: Va chạm (critical)
"""

import json
import threading
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Đảm bảo load cấu hình từ .env
load_dotenv()

# Flag để kiểm tra paho-mqtt đã cài chưa
_mqtt_available = False
_mqtt_client = None

try:
    import paho.mqtt.client as mqtt
    _mqtt_available = True
except ImportError:
    print("[MQTT] WARNING: paho-mqtt chưa được cài đặt. Chạy: pip install paho-mqtt==1.6.1")
    print("[MQTT] Hệ thống vẫn hoạt động bình thường nhưng không gửi cảnh báo đến ESP32.")


# ========================================
# MQTT CONFIGURATION
# ========================================
MQTT_BROKER = os.environ.get('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_TOPIC = os.environ.get('MQTT_TOPIC', 'traffic/alert')
MQTT_USERNAME = os.environ.get('MQTT_USERNAME', '')
MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD', '')
MQTT_ENABLED = os.environ.get('MQTT_ENABLED', 'true').lower() == 'true'

# Trạng thái kết nối
_is_connected = False
_lock = threading.Lock()


# ========================================
# MQTT CALLBACKS
# ========================================
def _on_connect(client, userdata, flags, rc):
    """Callback khi kết nối đến MQTT Broker"""
    global _is_connected
    if rc == 0:
        _is_connected = True
        print(f"[MQTT] ✅ Đã kết nối đến Broker: {MQTT_BROKER}:{MQTT_PORT}")
        # Subscribe topic phản hồi từ ESP32 (nếu cần)
        client.subscribe("traffic/esp32/status")
    else:
        _is_connected = False
        error_messages = {
            1: "Sai phiên bản protocol",
            2: "Client ID không hợp lệ",
            3: "Server không khả dụng",
            4: "Sai username/password",
            5: "Không có quyền truy cập"
        }
        print(f"[MQTT] ❌ Kết nối thất bại: {error_messages.get(rc, f'Lỗi không xác định (rc={rc})')}")


def _on_disconnect(client, userdata, rc):
    """Callback khi mất kết nối"""
    global _is_connected
    _is_connected = False
    if rc != 0:
        print(f"[MQTT] ⚠️ Mất kết nối bất thường (rc={rc}). Đang thử kết nối lại...")


def _on_message(client, userdata, msg):
    """Callback khi nhận message từ ESP32 (phản hồi trạng thái)"""
    try:
        payload = json.loads(msg.payload.decode())
        print(f"[MQTT] 📩 ESP32 phản hồi: {payload}")
    except Exception as e:
        print(f"[MQTT] Lỗi parse message từ ESP32: {e}")


# ========================================
# MQTT CLIENT INITIALIZATION
# ========================================
def init_mqtt():
    """Khởi tạo và kết nối MQTT client (chạy trong background thread)"""
    global _mqtt_client, _is_connected

    if not _mqtt_available:
        print("[MQTT] Bỏ qua khởi tạo - paho-mqtt chưa cài đặt.")
        return

    if not MQTT_ENABLED:
        print("[MQTT] MQTT đã bị tắt trong cấu hình (.env MQTT_ENABLED=false)")
        return

    try:
        # Tạo Client ID duy nhất bằng cách thêm timestamp để tránh trùng với ESP32
        unique_id = f"ai_monitor_{int(time.time())}"
        _mqtt_client = mqtt.Client(client_id=unique_id, clean_session=True)
        
        # Đặt callbacks
        _mqtt_client.on_connect = _on_connect
        _mqtt_client.on_disconnect = _on_disconnect
        _mqtt_client.on_message = _on_message

        # Đặt username/password nếu có
        if MQTT_USERNAME and MQTT_PASSWORD:
            _mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

        # Cấu hình auto-reconnect
        _mqtt_client.reconnect_delay_set(min_delay=1, max_delay=30)

        # Kết nối (non-blocking)
        _mqtt_client.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=60)
        
        # Chạy loop trong background thread
        _mqtt_client.loop_start()
        print(f"[MQTT] 🚀 Đang kết nối đến {MQTT_BROKER}:{MQTT_PORT}...")

    except Exception as e:
        print(f"[MQTT] ❌ Lỗi khởi tạo MQTT: {e}")
        _is_connected = False


def publish_alert(alert_type, message, level="warning"):
    """
    Gửi cảnh báo vi phạm đến ESP32 qua MQTT.
    
    Args:
        alert_type (str): Loại vi phạm ('eye', 'yawn', 'head', 'phone', 'seatbelt', 'hand', 'collision')
        message (str): Nội dung cảnh báo
        level (str): Mức độ ('critical' hoặc 'warning')
    """
    if not MQTT_ENABLED or not _mqtt_available:
        return

    if not _is_connected or _mqtt_client is None:
        print(f"[MQTT] ⚠️ Chưa kết nối Broker - bỏ qua alert: {alert_type}")
        return

    try:
        # Chuyển tin nhắn sang không dấu hoặc tiếng Anh để ESP32 dễ xử lý
        safe_message = message.replace("ả", "a").replace("ế", "e").replace("ô", "o").replace("ă", "a").replace("á", "a").replace("í", "i")
        
        payload = json.dumps({
            "type": alert_type,
            "message": safe_message,
            "level": level,
            "timestamp": datetime.now().strftime('%H:%M:%S')
        }, separators=(',', ':'))

        with _lock:
            result = _mqtt_client.publish(
                MQTT_TOPIC,
                payload,
                qos=0,  # Dùng QoS 0 cho nhẹ và giống lệnh pub thủ công
                retain=False
            )

        if result.rc == 0:
            print(f"[MQTT] 📤 Đã gửi alert (QoS 0) đến '{MQTT_TOPIC}': {alert_type}")
        else:
            print(f"[MQTT] ⚠️ Gửi thất bại (rc={result.rc})")

    except Exception as e:
        print(f"[MQTT] ❌ Lỗi publish: {e}")


def get_status():
    """Trả về trạng thái kết nối MQTT (dùng cho API/web)"""
    return {
        "enabled": MQTT_ENABLED,
        "available": _mqtt_available,
        "connected": _is_connected,
        "broker": f"{MQTT_BROKER}:{MQTT_PORT}",
        "topic": MQTT_TOPIC
    }


def stop_mqtt():
    """Dừng MQTT client (gọi khi tắt app)"""
    global _mqtt_client, _is_connected
    if _mqtt_client:
        _mqtt_client.loop_stop()
        _mqtt_client.disconnect()
        _is_connected = False
        print("[MQTT] 🛑 Đã ngắt kết nối MQTT.")


# ========================================
# AUTO-INIT KHI IMPORT MODULE
# ========================================
# Tự động khởi tạo kết nối khi module được import
init_mqtt()
