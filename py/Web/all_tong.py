from flask import Flask, render_template, Response, jsonify, request, send_file
from flask_cors import CORS
import cv2
import dlib
import numpy as np
import pygame
import threading
import time
from datetime import datetime
from ultralytics import YOLO
import os
from shapely.geometry import Point, Polygon
import mediapipe as mp
import pyttsx3


app = Flask(__name__)
CORS(app)  # Cho phép frontend từ port khác gọi API

# ==================== BIẾN TOÀN CỤC CHO CHATBOT & GIỌNG NÓI ====================

# Hàng đợi cảnh báo AI để gửi vào chatbot
ai_alerts_queue = []
ai_alerts_lock = threading.Lock()

# Lịch sử cảnh báo (tối đa 50 cảnh báo)
MAX_ALERTS_HISTORY = 50

# Biến để lưu vehicle_id hiện tại đang được giám sát
current_monitoring_vehicle_id = None

def add_ai_alert(alert_type, message, vehicle_id=None):
    """Thêm cảnh báo AI vào hàng đợi"""
    global ai_alerts_queue
    with ai_alerts_lock:
        alert = {
            'type': alert_type,
            'message': message,
            'vehicle_id': vehicle_id,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': 'critical' if alert_type in ['eye', 'phone', 'seatbelt', 'collision'] else 'warning'
        }
        ai_alerts_queue.append(alert)
        # Giới hạn số lượng cảnh báo
        if len(ai_alerts_queue) > MAX_ALERTS_HISTORY:
            ai_alerts_queue = ai_alerts_queue[-MAX_ALERTS_HISTORY:]
        print(f"[AI ALERT] {alert_type}: {message}")

# ======================= Âm thanh & Cảnh báo ===========================
latest_warning = ""
lock = threading.Lock()
pygame.init()
chopmat_sound = pygame.mixer.Sound("py/Sound/nham_mat.wav")
ngap_sound = pygame.mixer.Sound("py/Sound/buon_ngu.wav")
phone_baodong = pygame.mixer.Sound("py/Sound/not_phone.wav")
seatbelt_baodong = pygame.mixer.Sound("py/Sound/seatbelt_alert.wav")
dau_quay_sound = pygame.mixer.Sound("py/Sound/chuylaixe.wav")
bienbao_sound = pygame.mixer.Sound("py/Sound/chu_y_bien_bao.wav")
tay_lai_sound = pygame.mixer.Sound("py/Sound/tay_lai_xe.wav")
lech_lan_sounds = pygame.mixer.Sound("py/Sound/lech_lan.wav")
va_cham_sound = pygame.mixer.Sound("py/Sound/va_cham.wav")

# Thời gian tối thiểu giữa các cảnh báo (giây)
WARNING_INTERVALS = {
    "eye": 2,
    "yawn": 3,
    "head": 3,
    "phone": 3,
    "seatbelt": 4,
    "hand": 4
}

# Thời gian cảnh báo cuối cùng cho mỗi loại
last_warning_times = {
    "eye": 0,
    "yawn": 0,
    "head": 0,
    "phone": 0,
    "seatbelt": 0,
    "hand": 0
}

def can_play_warning(warning_type):
    current_time = time.time()
    if current_time - last_warning_times[warning_type] >= WARNING_INTERVALS[warning_type]:
        last_warning_times[warning_type] = current_time
        return True
    return False

# ======================= Biến ghi hình ===========================
video_writer = None
is_recording = False
recording_start_time = None
fps = 30.0  # Tăng FPS lên 30 để video mượt hơn
frame_width = 1280  # Tăng độ phân giải
frame_height = 720
video_codec = cv2.VideoWriter_fourcc(*'avc1')  # Sử dụng codec H.264 cho chất lượng tốt hơn
recording_mode = None  # Lưu chế độ đang ghi (driver, sign, vacham, road)

# Tạo thư mục recordings nếu chưa tồn tại
if not os.path.exists('recordings'):
    os.makedirs('recordings')

# Dlib & YOLO models
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("py/shape_predictor_68_face_landmarks.dat")
phone_mau = YOLO("py/weights/yolov8n.pt")
seatbelt_mau = YOLO("py/weights/lasttx.pt")
bienbao_model = YOLO("py/weights/best2.pt")
model_vehicle = YOLO("py/weights/yolov8n.pt")   # Phát hiện phương tiện
model_lane = YOLO("py/weights/lech_lan.pt")
       # Mô hình YOLO đã huấn luyện lại vạch kẻ đường

# ======================= Các thông số ===========================
EAR_THRESHOLD = 0.30
EAR_MIN_DURATION = 2
YAWN_THRESHOLD = 25
YAWN_CONSEC_FRAMES = 15

left_eye_indexes = [36, 37, 38, 39, 40, 41]
right_eye_indexes = [42, 43, 44, 45, 46, 47]
mouth_indexes = [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]

# ======================= Hàm hỗ trợ ===========================
def eye_aspect_ratio(eye):
    A = np.linalg.norm(np.array(eye[1]) - np.array(eye[5]))
    B = np.linalg.norm(np.array(eye[2]) - np.array(eye[4]))
    C = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))
    return (A + B) / (2.0 * C)

def detect_yawn(points):
    top_lip = [points[i][1] for i in [50, 51, 52, 61, 62]]
    bottom_lip = [points[i][1] for i in [56, 57, 58, 65, 66]]
    return np.mean(bottom_lip) - np.mean(top_lip)

def get_head_pose(points, frame_size):
    model_points = np.array([
        (0.0, 0.0, 0.0),
        (0.0, -330.0, -65.0),
        (-225.0, 170.0, -135.0),
        (225.0, 170.0, -135.0),
        (-150.0, -150.0, -125.0),
        (150.0, -150.0, -125.0)
    ], dtype="double")

    image_points = np.array([
        points[30], points[8], points[36],
        points[45], points[48], points[54]
    ], dtype="double")

    focal_length = frame_size[1]
    center = (focal_length / 2, frame_size[0] / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype="double")

    dist_coeffs = np.zeros((4, 1))
    success, rvec, tvec = cv2.solvePnP(model_points, image_points, camera_matrix, dist_coeffs)
    rmat, _ = cv2.Rodrigues(rvec)
    proj_matrix = np.hstack((rmat, tvec))
    eulerAngles = cv2.decomposeProjectionMatrix(proj_matrix)[6]
    return [float(x) for x in eulerAngles]

# ======================= Giám sát tay lái ===========================
class HandAndArmTracking:
    def __init__(self, detectionCon=0.5):
        self.mpPose = mp.solutions.pose
        self.mpHands = mp.solutions.hands
        self.pose = self.mpPose.Pose(min_detection_confidence=detectionCon)
        self.hands = self.mpHands.Hands(min_detection_confidence=detectionCon)
        self.mpDraw = mp.solutions.drawing_utils

        self.no_fist_start_time = None
        self.last_warning_time = None
        self.warning_duration = 3
        self.warning_interval = 5
        self.is_playing = False

    def is_fist(self, hand_landmarks):
        tips_ids = [4, 8, 12, 16, 20]
        pip_ids = [3, 6, 10, 14, 18]

        fist_score = 0
        for tip, pip in zip(tips_ids[1:], pip_ids[1:]):
            if hand_landmarks.landmark[tip].y > hand_landmarks.landmark[pip].y:
                fist_score += 1

        return fist_score >= 3

    def findArmsAndHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.pose_results = self.pose.process(imgRGB)
        self.hand_results = self.hands.process(imgRGB)

        h, w, _ = img.shape

        if draw and self.pose_results.pose_landmarks:
            arm_landmarks = [
                self.mpPose.PoseLandmark.LEFT_SHOULDER,
                self.mpPose.PoseLandmark.RIGHT_SHOULDER,
                self.mpPose.PoseLandmark.LEFT_ELBOW,
                self.mpPose.PoseLandmark.RIGHT_ELBOW,
                self.mpPose.PoseLandmark.LEFT_WRIST,
                self.mpPose.PoseLandmark.RIGHT_WRIST
            ]
            connections = [(11, 13), (13, 15), (12, 14), (14, 16)]

            for landmark in arm_landmarks:
                lm = self.pose_results.pose_landmarks.landmark[landmark]
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(img, (cx, cy), 5, (0, 255, 0), cv2.FILLED)

            for (start, end) in connections:
                s_lm = self.pose_results.pose_landmarks.landmark[start]
                e_lm = self.pose_results.pose_landmarks.landmark[end]
                sx, sy = int(s_lm.x * w), int(s_lm.y * h)
                ex, ey = int(e_lm.x * w), int(e_lm.y * h)
                cv2.line(img, (sx, sy), (ex, ey), (0, 255, 255), 3)

            left_shoulder = self.pose_results.pose_landmarks.landmark[self.mpPose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = self.pose_results.pose_landmarks.landmark[self.mpPose.PoseLandmark.RIGHT_SHOULDER]
            lx, ly = int(left_shoulder.x * w), int(left_shoulder.y * h)
            rx, ry = int(right_shoulder.x * w), int(right_shoulder.y * h)
            cv2.line(img, (lx, ly), (rx, ry), (255, 0, 0), 3)

        has_fist = False
        if self.hand_results.multi_hand_landmarks:
            for handLms in self.hand_results.multi_hand_landmarks:
                if self.is_fist(handLms):
                    has_fist = True
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)

        current_time = time.time()
        if not has_fist:
            if self.no_fist_start_time is None:
                self.no_fist_start_time = current_time
            elif current_time - self.no_fist_start_time > self.warning_duration:
                cv2.putText(img, "WARNING: Khong cam vo lang xe !", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)
                
                
                if self.last_warning_time is None or current_time - self.last_warning_time >= self.warning_interval:
                    tay_lai_sound.play()
                    self.last_warning_time = current_time
                    warnings["hand"] = "CẢNH BÁO: KHÔNG CẦM VÔ LĂNG!"
        else:
            self.no_fist_start_time = None
            self.last_warning_time = None
            warnings["hand"] = ""

        return img

# Khởi tạo detector tay lái
hand_detector = HandAndArmTracking()

# ======================= Biến toàn cục ===========================
current_mode = "driver"
warning_states = {
    "eye": True,
    "yawn": True,
    "head": True,
    "phone": True,
    "seatbelt": True,
    "hand": True
}

warnings = {
    "eye": "",
    "yawn": "",
    "head": "",
    "phone": "",
    "seatbelt": "",
    "traffic": "",
    "congestion": "",
    "speed": "",
    "sign": "",
    "hand": "",
    "collision": "",
    "lane": ""
}

# Thêm biến để kiểm soát luồng video
active_video_stream = None

# Cảnh báo cũ để so sánh (tránh spam cảnh báo giống nhau)
previous_warnings = {
    "eye": "",
    "yawn": "",
    "head": "",
    "phone": "",
    "seatbelt": "",
    "hand": "",
    "collision": "",
    "lane": ""
}

# ======================= Video giám sát tài xế ===========================
def driver_monitor():
    global latest_warning, warnings, video_writer, is_recording, active_video_stream, warning_states
    try:
        active_video_stream = 'driver'
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 20)
        
        eye_closed_time = None
        counter_yawn = 0
        alarm_yawn_on = False

        while active_video_stream == 'driver':
            success, frame = cap.read()
            if not success:
                print("Failed to grab frame from driver camera")
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            try:
                faces = detector(gray)
            except:
                faces = []

            # Reset warnings
            warnings["eye"] = ""
            warnings["yawn"] = ""
            warnings["head"] = ""
            warnings["phone"] = ""
            warnings["seatbelt"] = ""
            warnings["hand"] = ""

            # Phát hiện các cảnh báo
            for face in faces:
                shape = predictor(gray, face)
                points = [(shape.part(i).x, shape.part(i).y) for i in range(68)]

                for idx in left_eye_indexes + right_eye_indexes + mouth_indexes:
                    x, y = points[idx]
                    cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

                # Ngủ gật - chỉ kiểm tra nếu cảnh báo mắt được bật
                if warning_states["eye"]:
                    left_eye = [points[i] for i in left_eye_indexes]
                    right_eye = [points[i] for i in right_eye_indexes]
                    ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0
                    if ear < EAR_THRESHOLD:
                        if eye_closed_time is None:
                            eye_closed_time = time.time()
                        elif time.time() - eye_closed_time > EAR_MIN_DURATION:
                            if can_play_warning("eye"):
                                chopmat_sound.play()
                            warnings["eye"] = "NHẮM MẮT QUÁ LÂU!"
                            # Gửi cảnh báo vào chatbot
                            if previous_warnings["eye"] != "NHẮM MẮT QUÁ LÂU!":
                                add_ai_alert("eye", "Tài xế đang nhắm mắt quá lâu!", current_monitoring_vehicle_id)
                    else:
                        eye_closed_time = None

                # Ngáp - chỉ kiểm tra nếu cảnh báo ngáp được bật
                if warning_states["yawn"]:
                    yawn_ratio = detect_yawn(points)
                    if yawn_ratio > YAWN_THRESHOLD:
                        counter_yawn += 1
                        if counter_yawn >= YAWN_CONSEC_FRAMES:
                            if not alarm_yawn_on and can_play_warning("yawn"):
                                alarm_yawn_on = True
                                ngap_sound.play()
                            warnings["yawn"] = "NGÁP NGỦ!"
                            if previous_warnings["yawn"] != "NGÁP NGỦ!":
                                add_ai_alert("yawn", "Tài xế đang ngáp ngủ!", current_monitoring_vehicle_id)
                    else:
                        counter_yawn = 0
                        alarm_yawn_on = False

                # Đầu quay ngang ngửa
                if warning_states["head"]:
                    pitch, yaw, roll = get_head_pose(points, frame.shape)
                    # Cảnh báo nếu quay trái/phải (yaw) lớn hơn 35 độ hoặc cúi xuống (pitch) lớn hơn 25 độ
                    if abs(yaw) > 40 or pitch > 35:
                        if can_play_warning("head"):
                            dau_quay_sound.play()
                        warnings["head"] = "MẤT TẬP TRUNG !"
                        if previous_warnings["head"] != "MẤT TẬP TRUNG !":
                            add_ai_alert("head", "Tài xế mất tập trung (quay đầu/ngửa đầu)!", current_monitoring_vehicle_id)

            # Phát hiện dùng điện thoại - chỉ kiểm tra nếu cảnh báo điện thoại được bật
            if warning_states["phone"]:
                results = phone_mau(frame)
                for result in results:
                    for box in result.boxes.data:
                        x1, y1, x2, y2, conf, cls = box
                        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                        label = phone_mau.names[int(cls)]
                        if "phone" in label.lower() and conf > 0.5:
                            if can_play_warning("phone"):
                                phone_baodong.play()
                            warnings["phone"] = "DÙNG ĐIỆN THOẠI!"
                            if previous_warnings["phone"] != "DÙNG ĐIỆN THOẠI!":
                                add_ai_alert("phone", "Tài xế đang dùng điện thoại!", current_monitoring_vehicle_id)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                            cv2.putText(frame, label, (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Phát hiện dây an toàn - chỉ kiểm tra nếu cảnh báo dây an toàn được bật
            if warning_states["seatbelt"]:
                seatbelt_detected = False
                seatbelt_results = seatbelt_mau.predict(source=frame, stream=False)
                for result in seatbelt_results:
                    for box in result.boxes.data:
                        x1, y1, x2, y2, conf, cls = box
                        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                        label = result.names[int(cls)]
                        if "seat_belt" in label.lower() and conf > 0.5:
                            seatbelt_detected = True
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame, label, (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                if not seatbelt_detected:
                    if can_play_warning("seatbelt"):
                        seatbelt_baodong.play()
                    warnings["seatbelt"] = "KHÔNG ĐEO DÂY AN TOÀN!"
                    if previous_warnings["seatbelt"] != "KHÔNG ĐEO DÂY AN TOÀN!":
                        add_ai_alert("seatbelt", "Tài xế không đeo dây an toàn!", current_monitoring_vehicle_id)

            # Giám sát tay lái - chỉ kiểm tra nếu cảnh báo tay lái được bật
            if warning_states["hand"]:
                frame = hand_detector.findArmsAndHands(frame)
                # Cảnh báo tay lái đã được thêm vào warnings["hand"] từ hand_detector
                if warnings["hand"] and previous_warnings["hand"] != warnings["hand"]:
                    add_ai_alert("hand", warnings["hand"], current_monitoring_vehicle_id)

            # Cập nhật previous_warnings
            for key in previous_warnings:
                previous_warnings[key] = warnings[key] if warnings[key] else ""

            # Resize frame trước khi ghi
            frame = cv2.resize(frame, (frame_width, frame_height))

            # Ghi frame nếu đang trong chế độ ghi hình
            if is_recording and video_writer is not None:
                video_writer.write(frame)

            # Encode frame
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        print(f"Error in driver_monitor: {str(e)}")
    finally:
        cap.release()
        active_video_stream = None

# ======================= Biến toàn cục cho biển báo ===========================
# Đường dẫn tuyệt đối cho thư mục pictures
PICTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pictures')
latest_sign_image_path = None
latest_sign_label = ""

# Đảm bảo thư mục pictures tồn tại
if not os.path.exists(PICTURES_DIR):
    os.makedirs(PICTURES_DIR)

# ======================= Video cảnh báo biển báo ===========================
def traffic_sign_monitor():
    global warnings, video_writer, is_recording, active_video_stream, latest_sign_image_path, latest_sign_label
    try:
        active_video_stream = 'sign'
        cap = cv2.VideoCapture("py/video_input/bien_bao.mp4")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 20)

        last_sign_time = None

        while active_video_stream == 'sign':
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame from traffic sign camera")
                break
            results = bienbao_model(frame, imgsz=640, conf=0.4)
            boxes = results[0].boxes
            annotated = results[0].plot()
            num_detections = len(boxes) if boxes is not None else 0
            cv2.putText(annotated, f'So bien bao: {num_detections}', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

            # Reset warnings
            warnings["speed"] = ""
            warnings["sign"] = ""
            latest_sign_label = ""

            # Cập nhật cảnh báo
            current_time = time.time()
            if boxes is not None:
                for i in range(len(boxes)):
                    cls_id = int(boxes.cls[i])
                    label = bienbao_model.names[cls_id]
                    x1, y1, x2, y2 = map(int, boxes.xyxy[i])

                    # Xử lý biển báo tốc độ
                    if "speed" in label.lower():
                        warnings["speed"] = f"BIỂN BÁO TỐC ĐỘ: {label}"
                        latest_sign_label = label
                        # Phát âm thanh nếu chưa phát trong 3 giây qua
                        if last_sign_time is None or current_time - last_sign_time > 3:
                            bienbao_sound.play()
                            last_sign_time = current_time
                    else:
                        warnings["sign"] = f"{label}"
                        latest_sign_label = label
                        # Phát âm thanh nếu chưa phát trong 3 giây qua
                        if last_sign_time is None or current_time - last_sign_time > 3:
                            bienbao_sound.play()
                            last_sign_time = current_time

                    # Cắt và lưu hình ảnh biển báo
                    try:
                        # Đảm bảo tọa độ không vượt ra ngoài khung hình
                        h, w = frame.shape[:2]
                        x1 = max(0, min(x1, w))
                        y1 = max(0, min(y1, h))
                        x2 = max(0, min(x2, w))
                        y2 = max(0, min(y2, h))

                        # Chỉ cắt nếu vùng hợp lệ
                        if x2 > x1 and y2 > y1:
                            sign_crop = frame[y1:y2, x1:x2]
                            # Resize để dễ nhìn hơn
                            sign_crop = cv2.resize(sign_crop, (200, 200))
                            # Lưu vào thư mục pictures với đường dẫn tuyệt đối
                            latest_sign_image_path = os.path.join(PICTURES_DIR, 'latest_sign.jpg')
                            cv2.imwrite(latest_sign_image_path, sign_crop)
                            print(f"Saved sign image to: {latest_sign_image_path}")
                    except Exception as e:
                        print(f"Error cropping sign image: {e}")

            # Resize frame trước khi ghi
            annotated = cv2.resize(annotated, (frame_width, frame_height))

            # Ghi frame nếu đang trong chế độ ghi hình
            if is_recording and video_writer is not None:
                video_writer.write(annotated)

            ret, buffer = cv2.imencode('.jpg', annotated)
            frame = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        print(f"Error in traffic_sign_monitor: {str(e)}")
    finally:
        cap.release()
        active_video_stream = None

# ======================= Video giám sát va cham và cảnh báo lệch làn ===========================
# ====== Hàm hỗ trợ ======
def estimate_distance(y1, y2):
    box_height = y2 - y1
    return 2500 / box_height if box_height != 0 else 999

def is_in_center_lane(x, width, margin=100):
    center = width // 2
    return center - margin < x < center + margin

def draw_lane_points(image, results_l, width):
    for box in results_l.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        if is_in_center_lane(cx, width):
            cv2.ellipse(image, (cx, cy), (6, 6), 0, 0, 360, (255, 255, 0), 2)
    return image

def draw_lane_classic(image):
    height, width = image.shape[:2]
    roi_vertices = [(0, height), (width // 2, int(height * 0.6)), (width, height)]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    mask = np.zeros_like(edges)
    cv2.fillPoly(mask, [np.array(roi_vertices, np.int32)], 255)
    cropped = cv2.bitwise_and(edges, mask)

    lines = cv2.HoughLinesP(cropped, 1, np.pi / 180, 100, minLineLength=50, maxLineGap=30)
    left_lane, right_lane = [], []

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            slope = (y2 - y1) / (x2 - x1 + 1e-6)
            if abs(slope) < 0.5:
                continue
            if slope < 0:
                left_lane.append((x1, y1, x2, y2))
            else:
                right_lane.append((x1, y1, x2, y2))

        if left_lane and right_lane:
            left_avg = np.mean(left_lane, axis=0).astype(int)
            right_avg = np.mean(right_lane, axis=0).astype(int)

            pts = np.array([[left_avg[0:2], left_avg[2:4], right_avg[2:4], right_avg[0:2]]], dtype=np.int32)
            overlay = image.copy()
            cv2.fillPoly(overlay, pts, (0, 255, 0))
            image = cv2.addWeighted(image, 0.8, overlay, 0.4, 0)

    return image, left_lane + right_lane

# Biến toàn cục cho cảnh báo va chạm
last_collision_warning = 0
warning_interval = 1.0  # Khoảng thời gian giữa các cảnh báo (giây)

# Biến để theo dõi trạng thái cảnh báo va chạm/lệch làn đã gửi
collision_alert_sent = False
lane_alert_sent = False

def process_collision_warning(frame, distance, current_time):
    global last_collision_warning, warnings, collision_alert_sent

    if distance < 8:
        warnings["collision"] = "CẢNH BÁO VA CHẠM!"
        if current_time - last_collision_warning >= warning_interval:
            va_cham_sound.play()
            last_collision_warning = current_time
            # Gửi cảnh báo vào chatbot
            if not collision_alert_sent:
                add_ai_alert("collision", "🚨 CẢNH BÁO VA CHẠM SẮP XẢY RA!", current_monitoring_vehicle_id)
                collision_alert_sent = True
    elif distance < 15:
        warnings["collision"] = "GIỮ KHOẢNG CÁCH!"
    else:
        warnings["collision"] = ""
        collision_alert_sent = False  # Reset khi không còn nguy hiểm

def process_lane_warning(frame, left_found, right_found):
    global warnings, lane_alert_sent

    if not (left_found and right_found):
        warnings["lane"] = "CẢNH BÁO LỆCH LÀN!"
        if not pygame.mixer.get_busy():
            lech_lan_sounds.play()
        # Gửi cảnh báo vào chatbot
        if not lane_alert_sent:
            add_ai_alert("lane", "⚠️ Xe đang LỆCH LÀN!", current_monitoring_vehicle_id)
            lane_alert_sent = True
    else:
        warnings["lane"] = ""
        lane_alert_sent = False  # Reset khi trở lại làn

def detect_lane_deviation_combined(results_l, frame, width, classic_lines):
    center_x = width // 2
    left_found, right_found = False, False

    # Từ YOLO
    for box in results_l.boxes:
        x1, _, x2, _ = map(int, box.xyxy[0])
        cx = (x1 + x2) // 2
        if cx < center_x - 50:
            left_found = True
        elif cx > center_x + 50:
            right_found = True

    # Từ Hough Line
    for line in classic_lines:
        x1, _, x2, _ = line
        cx = (x1 + x2) // 2
        if cx < center_x - 50:
            left_found = True
        elif cx > center_x + 50:
            right_found = True

    process_lane_warning(frame, left_found, right_found)
    return frame

def collision_monitor():
    global warnings, video_writer, is_recording, active_video_stream, last_collision_warning
    try:
        active_video_stream = 'vacham'
        cap = cv2.VideoCapture("py/video_input/lech_lan.mp4")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 20)
        
        while active_video_stream == 'vacham':
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame from collision camera")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame = cv2.resize(frame, (960, 540))
            height, width = frame.shape[:2]
            current_time = time.time()

            # Reset warnings
            warnings["collision"] = ""
            warnings["lane"] = ""

            # Phát hiện phương tiện
            results_v = model_vehicle(frame)[0]
            for box in results_v.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = model_vehicle.names[cls]

                if label in ['car', 'truck', 'bus', 'motorbike']:
                    distance = estimate_distance(y1, y2)
                    process_collision_warning(frame, distance, current_time)

                    # Chọn màu và cảnh báo dựa trên khoảng cách
                    if distance < 8:
                        color = (0, 0, 255)  # Đỏ
                    elif distance < 15:
                        color = (0, 255, 255)  # Vàng
                    else:
                        color = (0, 255, 0)  # Xanh lá

                    # Vẽ bounding box, nhãn và khoảng cách
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f'{label} {conf:.2f} | {distance:.1f}m', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Nhận diện làn bằng YOLO
            results_l = model_lane(frame)[0]
            frame = draw_lane_points(frame, results_l, width)

            # Nhận diện làn bằng Hough truyền thống
            frame, classic_lines = draw_lane_classic(frame)

            # Kết hợp cảnh báo lệch làn từ cả 2 nguồn
            frame = detect_lane_deviation_combined(results_l, frame, width, classic_lines)

            # Resize frame trước khi ghi
            frame = cv2.resize(frame, (frame_width, frame_height))

            # Ghi frame nếu đang trong chế độ ghi hình
            if is_recording and video_writer is not None:
                video_writer.write(frame)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        print(f"Error in collision_monitor: {str(e)}")
    finally:
        cap.release()
        active_video_stream = None


# phần điểu chỉnh cử chỉ và giọng nói 


from flask import Flask, render_template, Response, jsonify, request
import cv2
import numpy as np
import HandTrackingModule as htm
import os
import base64
import threading
import time
import math
import sys
from ctypes import cast, POINTER
import speech_recognition as sr
import queue

# Windows-only imports - chỉ import khi chạy trên Windows
if sys.platform == "win32":
    try:
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        import screen_brightness_control as sbc
        WINDOWS_AUDIO_AVAILABLE = True
        WINDOWS_BRIGHTNESS_AVAILABLE = True
    except ImportError:
        WINDOWS_AUDIO_AVAILABLE = False
        WINDOWS_BRIGHTNESS_AVAILABLE = False
        print("Warning: Windows-only libraries not available. Audio and brightness control will be disabled.")
else:
    # macOS/Linux - sử dụng các thư viện thay thế nếu có
    WINDOWS_AUDIO_AVAILABLE = False
    WINDOWS_BRIGHTNESS_AVAILABLE = False
    try:
        import screen_brightness_control as sbc  # type: ignore
        WINDOWS_BRIGHTNESS_AVAILABLE = True
        print("Note: Using cross-platform brightness control")
    except ImportError:
        print("Note: Brightness control not available on this platform")

# ======================= Hand Tracking Variables =======================
# Thông số video
wCam, hCam = 640, 480  # Giảm kích thước xuống để tăng hiệu suất

# Cấu hình camera
hand_cap = cv2.VideoCapture(0)
hand_cap.set(3, wCam)
hand_cap.set(4, hCam)

# Biến điều khiển
current_page = 0
total_pages = 3  # Số lượng trang HTML
gestureThreshold = int(hCam * 0.90)
buttonPresses = False
buttonCounter = 0
buttonDelay = 30
clicked_button = None

# Biến cho lịch sử thao tác
action_history = []  # Lưu lịch sử các thao tác
current_action_index = -1  # Vị trí hiện tại trong lịch sử

# Biến cho vẽ
annotations = [[]]
annotationsNumber = 0
annotationsStart = False

# Biến cho điều khiển âm thanh và ánh sáng
volume = None
minVol = -65.25  # Giá trị mặc định cho Windows
maxVol = 0.0     # Giá trị mặc định cho Windows
vol = 0
volBar = 400
volPer = 0
brightBar = 400
brightnessPer = 0

# Khởi tạo điều khiển âm thanh (chỉ trên Windows)
if WINDOWS_AUDIO_AVAILABLE:
    try:
        devices = AudioUtilities.GetSpeakers()  # type: ignore
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)  # type: ignore
        volume = cast(interface, POINTER(IAudioEndpointVolume))  # type: ignore
        volScope = volume.GetVolumeRange()
        minVol = volScope[0]
        maxVol = volScope[1]
    except Exception as e:
        print(f"Warning: Could not initialize audio control: {e}")
        volume = None

# Định nghĩa vị trí các button
buttons = [
    {"id": "button1", "x1": 10, "y1": 0, "x2": 200, "y2": 50, "text": "Phone"},
    {"id": "button2", "x1": 10, "y1": 50, "x2": 200, "y2": 100, "text": "Google map"},
    {"id": "button3", "x1": 10, "y1": 100, "x2": 200, "y2": 150, "text": "Youtube"}
]

# Khởi tạo đối tượng hand detector
detector = htm.HandDetector(detectionCon=0.7, maxHands=1)

# Thêm biến cho nhận diện giọng nói
voice_queue = queue.Queue()
recognizer = sr.Recognizer()
is_listening = True

def get_frame():
    success, frame = hand_cap.read()
    if not success:
        return None
    return cv2.flip(frame, 1)

def draw_buttons(img):
    """Hàm vẽ các button lên frame"""
    for button in buttons:
        # Vẽ khung button
        cv2.rectangle(img, (button["x1"], button["y1"]), (button["x2"], button["y2"]), (0, 255, 0), 2)
        # Vẽ text button
        text_size = cv2.getTextSize(button["text"], cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        text_x = button["x1"] + (button["x2"] - button["x1"] - text_size[0]) // 2
        text_y = button["y1"] + (button["y2"] - button["y1"] + text_size[1]) // 2
        cv2.putText(img, button["text"], (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)


prev_middle_pos = None
prev_index_pos = None
rotation_threshold = 30  # Ngưỡng để xác định quay

#xoay ngón tay
def calculate_rotation(prev_pos, current_pos, center):
    """Tính góc quay giữa hai vị trí"""
    if prev_pos is None:
        return 0
    
    # Tính vector từ tâm đến vị trí trước và hiện tại
    prev_vector = (prev_pos[0] - center[0], prev_pos[1] - center[1])
    current_vector = (current_pos[0] - center[0], current_pos[1] - center[1])
    
    # Tính góc giữa hai vector
    dot_product = prev_vector[0] * current_vector[0] + prev_vector[1] * current_vector[1]
    prev_magnitude = math.sqrt(prev_vector[0]**2 + prev_vector[1]**2)
    current_magnitude = math.sqrt(current_vector[0]**2 + current_vector[1]**2)
    
    # Tránh chia cho 0
    if prev_magnitude == 0 or current_magnitude == 0:
        return 0
        
    cos_angle = dot_product / (prev_magnitude * current_magnitude)
    cos_angle = max(-1, min(1, cos_angle))  # Giới hạn trong khoảng [-1, 1]
    angle = math.degrees(math.acos(cos_angle))
    
    # Xác định hướng quay (theo chiều kim đồng hồ hay ngược lại)
    cross_product = prev_vector[0] * current_vector[1] - prev_vector[1] * current_vector[0]
    if cross_product < 0:
        angle = -angle
        
    return angle
        

def listen_for_commands():
    """Hàm lắng nghe lệnh thoại trong một thread riêng"""
    global is_listening
    while is_listening:
        try:
            with sr.Microphone() as source:
                print("Đang lắng nghe...")
                # Điều chỉnh độ nhạy của microphone
                recognizer.dynamic_energy_threshold = True
                recognizer.energy_threshold = 300  # Giảm ngưỡng năng lượng để dễ nhận diện hơn
                recognizer.pause_threshold = 0.8  # Giảm thời gian chờ giữa các từ
                recognizer.adjust_for_ambient_noise(source, duration=1)
                
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    print("Đã ghi âm xong, đang xử lý...")
                    
                    try:
                        text = recognizer.recognize_google(audio, language="vi-VN")
                        print(f"Đã nhận lệnh: {text}")
                        voice_queue.put(text.lower())
                    except sr.UnknownValueError:
                        print("Không nhận diện được giọng nói. Vui lòng nói rõ ràng hơn.")
                    except sr.RequestError as e:
                        print(f"Lỗi kết nối đến dịch vụ nhận diện giọng nói: {e}")
                        print("Vui lòng kiểm tra kết nối internet của bạn.")
                except sr.WaitTimeoutError:
                    print("Hết thời gian chờ. Vui lòng thử lại.")
                except Exception as e:
                    print(f"Lỗi khi ghi âm: {e}")
                    print("Vui lòng kiểm tra microphone của bạn.")
        except Exception as e:
            print(f"Lỗi khi lắng nghe: {e}")
            print("Vui lòng kiểm tra lại thiết bị âm thanh của bạn.")
            time.sleep(1)  # Đợi 1 giây trước khi thử lại

def process_voice_command(command):
    global volPer, brightnessPer
    # Lệnh điều khiển âm thanh
    if "tăng âm thanh" in command or "tăng âm lượng" in command:
        volPer = min(100, volPer + 10)
        return f"Tăng âm thanh lên {volPer}%"
    elif "giảm âm thanh" in command or "giảm âm lượng" in command:
        volPer = max(0, volPer - 10)
        return f"Giảm âm thanh xuống {volPer}%"
    elif "âm thanh" in command and "mức" in command:
        try:
            level = int(''.join(filter(str.isdigit, command)))
            volPer = max(0, min(100, level))
            return f"Đặt âm thanh ở mức {volPer}%"
        except:
            return "Không hiểu mức âm thanh"
    # Lệnh điều khiển ánh sáng
    elif "tăng độ sáng" in command or "tăng ánh sáng" in command:
        brightnessPer = min(100, brightnessPer + 10)
        return f"Tăng độ sáng lên {brightnessPer}%"
    elif "giảm độ sáng" in command or "giảm ánh sáng" in command:
        brightnessPer = max(0, brightnessPer - 10)
        return f"Giảm độ sáng xuống {brightnessPer}%"
    elif "độ sáng" in command and "mức" in command:
        try:
            level = int(''.join(filter(str.isdigit, command)))
            brightnessPer = max(0, min(100, level))
            return f"Đặt độ sáng ở mức {brightnessPer}%"
        except:
            return "Không hiểu mức độ sáng"
    
    return None

def generate_camera_frames():
    global volBar, volPer, brightBar, brightnessPer
    pTime = 0
    
    # Bắt đầu thread lắng nghe giọng nói
    voice_thread = threading.Thread(target=listen_for_commands)
    voice_thread.daemon = True
    voice_thread.start()
    
    while True:
        try:
            img = get_frame()
            if img is None:
                continue
                
            height, width, _ = img.shape

            # Xử lý lệnh thoại từ queue
            try:
                while not voice_queue.empty():
                    command = voice_queue.get_nowait()
                    response = process_voice_command(command)
                    if response:
                        # Cập nhật âm thanh
                        if "âm thanh" in response:
                            vol = np.interp(volPer, [0, 100], [minVol, maxVol])
                            volBar = np.interp(volPer, [0, 100], [400, 150])
                            if WINDOWS_AUDIO_AVAILABLE and volume is not None:
                                try:
                                    volume.SetMasterVolumeLevel(vol, None)
                                except Exception as e:
                                    print(f"Error setting volume: {e}")
                            else:
                                print(f"Volume control not available (would set to {volPer}%)")
                        # Cập nhật độ sáng
                        elif "độ sáng" in response:
                            brightBar = np.interp(brightnessPer, [0, 100], [400, 150])
                            if WINDOWS_BRIGHTNESS_AVAILABLE:
                                try:
                                    sbc.set_brightness(int(brightnessPer))
                                except Exception as e:
                                    print(f"Error setting brightness: {e}")
                            else:
                                print(f"Brightness control not available (would set to {brightnessPer}%)")
                        
                        # Hiển thị thông báo
                        cv2.putText(img, response, (50, 100), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            except queue.Empty:
                pass
            
            # Phát hiện tay và vẽ đường kẻ
            try:
                hands, img = detector.findHands(img)
                cv2.line(img, (0, gestureThreshold), (width, gestureThreshold), (0, 255, 0), 5)

                # Vẽ thông tin cử chỉ
                if hands:
                    for hand in hands:
                        fingers = detector.fingersUp(hand)
                        cx, cy = hand['center']
                        lmList = hand['lmList']
                        hand_type = hand['label']  # "Left" hoặc "Right"
                        
                        # Hiển thị trạng thái các ngón tay
                        finger_status = "Ngon tay: "
                        if fingers[0]: finger_status += "Cai "
                        if fingers[1]: finger_status += "Tro "
                        if fingers[2]: finger_status += "Giữa "
                        if fingers[3]: finger_status += "Nhẫn "
                        if fingers[4]: finger_status += "Út "

                        # Xử lý theo loại tay
                        if hand_type == "Left":  # Tay trái - điều khiển âm thanh và ánh sáng
                            if len(lmList) != 0:
                                try:
                                    # Điều khiển âm thanh bằng ngón trỏ
                                    index_finger_pos = (lmList[8][1], lmList[8][2])
                                    index_center = (lmList[6][1], lmList[6][2])
                                    
                                    # Vẽ đường tròn và điểm cho ngón trỏ
                                    cv2.circle(img, index_center, 30, (0, 255, 0), 2)
                                    cv2.circle(img, index_finger_pos, 5, (0, 0, 255), -1)
                                    
                                    if prev_index_pos is not None:
                                        cv2.line(img, prev_index_pos, index_finger_pos, (255, 0, 0), 2)
                                        rotation = calculate_rotation(prev_index_pos, index_finger_pos, index_center)
                                        
                                        if abs(rotation) > 5:
                                            volume_change = rotation * 0.5
                                            volPer = max(0, min(100, volPer + volume_change))
                                            
                                            if volume_change > 0:
                                                cv2.putText(img, f"Tang am thanh: {int(volume_change)}%", (300, 100), 
                                                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                            else:
                                                cv2.putText(img, f"Giam am thanh: {int(abs(volume_change))}%", (300, 100), 
                                                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                            
                                            vol = np.interp(volPer, [0, 100], [minVol, maxVol])
                                            volBar = np.interp(volPer, [0, 100], [400, 150])
                                            if WINDOWS_AUDIO_AVAILABLE and volume is not None:
                                                try:
                                                    volume.SetMasterVolumeLevel(vol, None)
                                                except Exception as e:
                                                    print(f"Error setting volume: {e}")
                                            else:
                                                # Chỉ hiển thị giá trị, không thực sự thay đổi volume trên macOS
                                                pass
                                    
                                    prev_index_pos = index_finger_pos

                                    # Điều khiển ánh sáng bằng ngón giữa
                                    middle_finger_pos = (lmList[12][1], lmList[12][2])
                                    middle_center = (lmList[10][1], lmList[10][2])

                                    # Vẽ đường tròn và điểm cho ngón giữa
                                    cv2.circle(img, middle_center, 30, (0, 165, 255), 2)
                                    cv2.circle(img, middle_finger_pos, 5, (255, 192, 203), -1)

                                    if prev_middle_pos is not None:
                                        cv2.line(img, prev_middle_pos, middle_finger_pos, (0, 165, 255), 2)
                                        rotation = calculate_rotation(prev_middle_pos, middle_finger_pos, middle_center)

                                        if abs(rotation) > 5:
                                            brightness_change = rotation * 0.5
                                            brightnessPer = max(0, min(100, brightnessPer + brightness_change))

                                            if brightness_change > 0:
                                                cv2.putText(img, f"Tang do sang: {int(brightness_change)}%", (100, 150),
                                                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
                                            else:
                                                cv2.putText(img, f"Giam do sang: {int(abs(brightness_change))}%", (100, 150),
                                                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)

                                            brightBar = np.interp(brightnessPer, [0, 100], [400, 150])
                                            if WINDOWS_BRIGHTNESS_AVAILABLE:
                                                try:
                                                    sbc.set_brightness(int(brightnessPer))
                                                except Exception as e:
                                                    print(f"Error setting brightness: {e}")
                                            else:
                                                # Chỉ hiển thị giá trị, không thực sự thay đổi độ sáng trên macOS
                                                pass

                                    prev_middle_pos = middle_finger_pos

                                except Exception as e:
                                    print(f"Error in volume/brightness control: {e}")
                                    prev_index_pos = None
                                    prev_middle_pos = None



                        else:  # Tay phải - vẽ và tương tác với nút
                          

                                # Click button bằng ngón trỏ và ngón giữa
                                if fingers == [0, 1, 1, 0, 0]:
                                    index_finger = lmList[8]
                                    for button in buttons:
                                        if (button["x1"] <= index_finger[1] <= button["x2"] and 
                                            button["y1"] <= index_finger[2] <= button["y2"]):
                                            clicked_button = button["id"]
                                            # Thêm vào lịch sử thao tác
                                            action_history = action_history[:current_action_index + 1]
                                            action_history.append(clicked_button)
                                            current_action_index = len(action_history) - 1
                                            buttonPresses = True
                                            break

                                # Mở Button 1 bằng ngón giữa
                                if fingers == [0, 1, 0, 0, 0]:
                                    clicked_button = "button1"
                                    action_history = action_history[:current_action_index + 1]
                                    action_history.append(clicked_button)
                                    current_action_index = len(action_history) - 1
                                    buttonPresses = True

                                # Mở Button 2 bằng ngón nhẫn
                                if fingers == [0, 0, 1, 0, 0]:
                                    clicked_button = "button2"
                                    action_history = action_history[:current_action_index + 1]
                                    action_history.append(clicked_button)
                                    current_action_index = len(action_history) - 1
                                    buttonPresses = True

                                # Mở Button 3 bằng ngón nhẫn
                                if fingers == [0, 0, 0, 1, 0]:
                                    clicked_button = "button3"
                                    action_history = action_history[:current_action_index + 1]
                                    action_history.append(clicked_button)
                                    current_action_index = len(action_history) - 1
                                    buttonPresses = True

                                # Đóng modal khi giơ 4 ngón trỏ, giữa và nhẫn
                                if fingers == [0, 1, 1, 1, 1]:
                                    clicked_button = None
                                    buttonPresses = True
                                    # Thêm vào lịch sử thao tác
                                    action_history = action_history[:current_action_index + 1]
                                    action_history.append(None)
                                    current_action_index = len(action_history) - 1

                                
               

            except Exception as e:
                print(f"Error in hand detection: {e}")

            # Vẽ thanh âm thanh
            cv2.rectangle(img, (10, 160), (50, 400), (255, 255, 0), 3)
            cv2.rectangle(img, (10, int(volBar)), (50, 400), (255, 255, 0), cv2.FILLED)
            cv2.putText(img, f'Volume {int(volPer)} %', (150, 400), 
                        cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)

            # Vẽ thanh ánh sáng
            cv2.rectangle(img, (55, 160), (95, 400), (0, 165, 255), 3)
            cv2.rectangle(img, (55, int(brightBar)), (95, 400), (0, 165, 255), cv2.FILLED)
            cv2.putText(img, f'Light {int(brightnessPer)} %', (380, 400),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (0, 165, 255), 2)

            
            # FPS
            cTime = time.time()
            fps = 1 / (cTime - pTime + 1e-5)
            pTime = cTime
            cv2.putText(img, f'FPS {int(fps)}', (500, 50),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)

            #vẽ button
            draw_buttons(img)

            ret, buffer = cv2.imencode('.jpg', img)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            print(f"Error in generate_camera_frames: {e}")
            continue

def generate_interactive_frames():
    global current_page, buttonPresses, buttonCounter, clicked_button, action_history, current_action_index
    while True:
        try:
            img = get_frame()
            if img is None:
                continue
                
            height, width, _ = img.shape

            # Phát hiện tay
            hands, img = detector.findHands(img)
            cv2.line(img, (0, gestureThreshold), (width, gestureThreshold), (0, 255, 0), 5)

            if hands and buttonPresses is False:
                hand = hands[0]
                fingers = detector.fingersUp(hand)
                cx, cy = hand['center']
                lmList = hand['lmList']

                if cy <= gestureThreshold:
                    # Quay lại thao tác trước đó (ngón cái + ngón trỏ)
                    if fingers == [1, 0, 0, 0, 0]:
                        if current_action_index > 0:
                            current_action_index -= 1
                            # Khôi phục trạng thái từ lịch sử
                            if action_history[current_action_index]:
                                clicked_button = action_history[current_action_index]
                            buttonPresses = True
                    
                    # Đi đến thao tác tiếp theo (ngón trỏ + ngón út)
                    if fingers == [0, 0, 0, 0, 1]:
                        if current_action_index < len(action_history) - 1:
                            current_action_index += 1
                            # Khôi phục trạng thái từ lịch sử
                            if action_history[current_action_index]:
                                clicked_button = action_history[current_action_index]
                            buttonPresses = True

                    # Click button bằng ngón trỏ và ngón giữa
                    if fingers == [0, 1, 1, 0, 0]:
                        index_finger = lmList[8]
                        for button in buttons:
                            if (button["x1"] <= index_finger[1] <= button["x2"] and 
                                button["y1"] <= index_finger[2] <= button["y2"]):
                                clicked_button = button["id"]
                                # Thêm vào lịch sử thao tác
                                action_history = action_history[:current_action_index + 1]
                                action_history.append(clicked_button)
                                current_action_index = len(action_history) - 1
                                buttonPresses = True
                                break

                    # Mở Button 1 bằng ngón giữa
                    if fingers == [0, 1, 0, 0, 0]:
                        clicked_button = "button1"
                        action_history = action_history[:current_action_index + 1]
                        action_history.append(clicked_button)
                        current_action_index = len(action_history) - 1
                        buttonPresses = True

                    # Mở Button 2 bằng ngón nhẫn
                    if fingers == [0, 0, 1, 0, 0]:
                        clicked_button = "button2"
                        action_history = action_history[:current_action_index + 1]
                        action_history.append(clicked_button)
                        current_action_index = len(action_history) - 1
                        buttonPresses = True

                    # Mở Button 3 bằng ngón nhẫn
                    if fingers == [0, 0, 0, 1, 0]:
                        clicked_button = "button3"
                        action_history = action_history[:current_action_index + 1]
                        action_history.append(clicked_button)
                        current_action_index = len(action_history) - 1
                        buttonPresses = True

                    # Đóng modal khi giơ 4 ngón trỏ, giữa và nhẫn
                    if fingers == [0, 1, 1, 1, 1]:
                        clicked_button = None
                        buttonPresses = True
                        # Thêm vào lịch sử thao tác
                        action_history = action_history[:current_action_index + 1]
                        action_history.append(None)
                        current_action_index = len(action_history) - 1

            if buttonPresses:
                buttonCounter += 1
                if buttonCounter > buttonDelay:
                    buttonCounter = 0
                    buttonPresses = False

            # Vẽ các button
            draw_buttons(img)

            ret, buffer = cv2.imencode('.jpg', img)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            print(f"Error in generate_interactive_frames: {e}")
            continue



@app.route('/camera_feed')
def camera_feed():
    return Response(generate_camera_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/interactive_feed')
def interactive_feed():
    return Response(generate_interactive_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_current_page')
def get_current_page():
    return {'page': current_page, 'clicked_button': clicked_button}


# ======================= Video giám sát lưu lượng ===========================



region_colors = [
    (255, 0, 255),
    (0, 255, 255),
    (86, 0, 254),
    (0, 128, 255),
    (235, 183, 0),
    (255, 34, 134)
]

# Màu sắc cho các loại xe
vehicle_colors = {
    2: (255, 0, 0),    # car
    3: (255,255,0),    # motorcycle
    5: (0, 255, 0),    # bus
    7: (0, 0, 128)     # truck
}

class MultipleObjectCounter:
    def __init__(self, model_path="py/weights/yolov8n.pt", regions=None, classes=None):
        self.model = YOLO(model_path)
        self.regions = regions if regions is not None else []
        self.classes = classes if classes is not None else []
        
        # Khởi tạo bộ đếm cho từng vùng
        self.in_counts = [0] * len(self.regions)
        self.out_counts = [0] * len(self.regions)
        self.counted_ids = [set() for _ in range(len(self.regions))]
        
        # Lưu trữ lịch sử tracking
        self.tracking_history = {}
        
        # Thêm biến để lưu trữ số liệu thống kê chi tiết cho từng vùng
        self.region_stats = [{
            'car': 0,
            'motorcycle': 0,
            'bus': 0,
            'truck': 0,
            'total': 0
        } for _ in range(len(self.regions))]
        
        # Thêm biến để lưu trữ số liệu thống kê
        self.stats = {
            'total_vehicles': 0,
            'lane_counts': [0] * len(self.regions),
            'vehicle_types': {'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0},
            'region_details': self.region_stats,
            'traffic_status': {
                'level': 'normal',
                'message': 'Giao thông thông thoáng, di chuyển bình thường',
                'color': 'green'
            }
        }
        
        # Thêm biến cho đếm tạm thời
        self.temp_vehicle_type_counts = {'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0}
        self.lock = threading.Lock()
        
        # Thêm biến để theo dõi xe trong vùng
        self.vehicles_in_regions = [set() for _ in range(len(self.regions))]
        
    def update_traffic_status(self):
        # Tính tổng số xe thực tế trong các vùng
        total_vehicles = sum(region['total'] for region in self.region_stats)
        self.stats['total_vehicles'] = total_vehicles
        
        if total_vehicles < 10:
            self.stats['traffic_status'] = {
                'level': 'normal',
                'message': 'Giao thông thông thoáng, di chuyển bình thường',
                'color': 'green'
            }
        elif total_vehicles >= 10 and total_vehicles < 20:
            self.stats['traffic_status'] = {
                'level': 'warning',
                'message': 'Giao thông hơi đông, tốc độ chậm hơn bình thường một chút',
                'color': 'yellow'
            }
        elif total_vehicles >= 20 and total_vehicles < 30:
            self.stats['traffic_status'] = {
                'level': 'danger',
                'message': 'Giao thông đông, có dấu hiệu tắc nghẽn',
                'color': 'red'
            }
        else:
            self.stats['traffic_status'] = {
                'level': 'critical',
                'message': 'Giao thông rất đông hoặc kẹt xe nghiêm trọng, di chuyển rất chậm hoặc đứng yên',
                'color': 'dark-red'
            }

    def process(self, frame):
        # Dự đoán với YOLO
        results = self.model.track(frame, persist=True, classes=self.classes)
        
        if results[0].boxes.id is None:
            return frame
            
        # Lấy thông tin tracking
        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.cpu().numpy().astype(int)
        clss = results[0].boxes.cls.cpu().numpy().astype(int)
        
        # Reset số liệu thống kê cho frame mới
        self.stats['vehicle_types'] = {'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0}
        
        # Reset vehicles in regions
        for region_vehicles in self.vehicles_in_regions:
            region_vehicles.clear()
        
        # Vẽ các vùng đếm và hiển thị thông tin
        for i, region_points in enumerate(self.regions):
            color = region_colors[i % len(region_colors)]
            cv2.polylines(frame, [np.array(region_points)], True, color, 2)
            
            # Vẽ số đếm và thông tin chi tiết cho từng vùng
            xs = [pt[0] for pt in region_points]
            ys = [pt[1] for pt in region_points]
            cx = int(sum(xs) / len(xs))
            cy = int(sum(ys) / len(ys))
            
            # Hiển thị thông tin vùng
            cv2.putText(frame, f"Khu : {i+1}", (cx - 50, cy - 80), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.putText(frame, f"Sum : {self.region_stats[i]['total']}", 
                       (cx - 50, cy - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Xử lý từng đối tượng được phát hiện
        for box, track_id, cls in zip(boxes, track_ids, clss):
            # Vẽ bounding box
            color = vehicle_colors.get(cls, (255, 255, 255))
            cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), color, 2)
            
            # Thêm nhãn tên loại xe
            vehicle_type = "Car" if cls == 2 else "Motorcycle" if cls == 3 else "Bus" if cls == 5 else "Truck"
            label_size = cv2.getTextSize(vehicle_type, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(frame, 
                        (int(box[0]), int(box[1] - label_size[1] - 10)), 
                        (int(box[0] + label_size[0]), int(box[1])), 
                        color, -1)
            cv2.putText(frame, vehicle_type, 
                       (int(box[0]), int(box[1] - 5)), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Tính centroid
            current_centroid = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
            
            # Cập nhật tracking history
            if track_id not in self.tracking_history:
                self.tracking_history[track_id] = []
            self.tracking_history[track_id].append(current_centroid)
            
            # Giới hạn lịch sử tracking để tránh tràn bộ nhớ
            if len(self.tracking_history[track_id]) > 30:
                self.tracking_history[track_id] = self.tracking_history[track_id][-30:]
            
            # Kiểm tra và đếm cho từng vùng
            for r_idx, region_points in enumerate(self.regions):
                polygon = Polygon(region_points)
                if polygon.contains(Point(current_centroid)):
                    # Thêm xe vào danh sách xe trong vùng
                    self.vehicles_in_regions[r_idx].add(track_id)
                    
                    # Nếu xe chưa được đếm trong vùng này
                    if track_id not in self.counted_ids[r_idx]:
                        # Kiểm tra xem xe có đang đi vào vùng không
                        if len(self.tracking_history[track_id]) > 1:
                            prev_centroid = self.tracking_history[track_id][-2]
                            # Nếu xe đang đi vào vùng (từ ngoài vào trong)
                            if not polygon.contains(Point(prev_centroid)):
                                self.in_counts[r_idx] += 1
                                self.counted_ids[r_idx].add(track_id)
                                
                                # Cập nhật thống kê chi tiết cho vùng
                                self.region_stats[r_idx][vehicle_type.lower()] += 1
                                self.region_stats[r_idx]['total'] += 1
                                
                                # Cập nhật thống kê tổng
                                self.stats['lane_counts'][r_idx] = self.in_counts[r_idx]
                                self.stats['region_details'] = self.region_stats
                                
                                # Cập nhật trạng thái giao thông
                                self.update_traffic_status()
        
        # Cập nhật số liệu thống kê theo thời gian thực
        for r_idx, region_vehicles in enumerate(self.vehicles_in_regions):
            # Reset thống kê cho vùng
            self.region_stats[r_idx] = {
                'car': 0,
                'motorcycle': 0,
                'bus': 0,
                'truck': 0,
                'total': len(region_vehicles)
            }
            
            # Đếm số lượng từng loại xe trong vùng
            for track_id in region_vehicles:
                if track_id in self.tracking_history:
                    # Lấy thông tin loại xe từ tracking history
                    for box, tid, cls in zip(boxes, track_ids, clss):
                        if tid == track_id:
                            vehicle_type = "car" if cls == 2 else "motorcycle" if cls == 3 else "bus" if cls == 5 else "truck"
                            self.region_stats[r_idx][vehicle_type] += 1
                            break
        
        # Cập nhật thống kê tổng
        self.update_traffic_status()
        
        return frame

    def get_stats(self):
        return self.stats

counter = None
video_capture = None
current_region_type = 'single'  # Default to single region

def traffic_monitor():
    global counter, video_capture, active_video_stream, video_writer, is_recording
    try:
        active_video_stream = 'traffic'
        cap = video_capture
        if cap is None:
            print("Video capture is None, trying to initialize...")
            region_data = get_region_points(current_region_type)
            cap = cv2.VideoCapture(region_data['video_source'])
            if not cap.isOpened():
                print("Failed to initialize video capture")
                return
            video_capture = cap
            
        print(f"Starting traffic monitor with region type: {current_region_type}")
        
        while active_video_stream == 'traffic':
            if cap is None or not cap.isOpened():
                print("Video capture is not opened, trying to reopen...")
                region_data = get_region_points(current_region_type)
                cap = cv2.VideoCapture(region_data['video_source'])
                if not cap.isOpened():
                    print("Failed to reopen video capture")
                    time.sleep(1)
                    continue
                video_capture = cap
                
            success, frame = cap.read()
            if not success:
                print("Failed to grab frame, resetting video...")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
                
            if counter:
                try:
                    processed_frame = counter.process(frame)
                    
                    # Ghi frame nếu đang trong chế độ ghi hình
                    if is_recording and video_writer is not None:
                        resized_frame = cv2.resize(processed_frame, (frame_width, frame_height))
                        video_writer.write(resized_frame)
                    
                    ret, buffer = cv2.imencode('.jpg', processed_frame)
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                except Exception as e:
                    print(f"Error processing frame: {e}")
                    continue
    except Exception as e:
        print(f"Error in traffic_monitor: {str(e)}")
    finally:
        active_video_stream = None

def reset_temporary_counts():
    global counter
    while True:
        time.sleep(10)
        if counter:
            with counter.lock:
                print("Thống kê trong 10 giây qua:", counter.temp_vehicle_type_counts)
                counter.temp_vehicle_type_counts = {'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0}

def get_region_points(region_type):
    if region_type == 'single':
        return {
            'regions': [

                # np.array([[521, 74], [4, 571], [2, 382], [458, 64]]),
                # np.array([[581, 90], [167, 709], [4, 707], [5, 576], [520, 76]]),
                # np.array([[670, 96], [505, 712], [175, 712], [581, 88]]),
                # np.array([[772, 96], [885, 711], [508, 711], [670, 96]]),
                # np.array([[772, 96], [889, 712], [1267, 712], [1274, 407], [902, 58]])


                np.array([[443, 79], [4, 399], [4, 709], [1267, 711], [1272, 401], [877, 39], [475, 57]])
            ],
            'video_source': "py/video_input/ha_noi.mp4"
        }
    elif region_type == 'thanhxuan':
      
         return {
            'regions': [
                
                # các làn xe 
                np.array([[500, 87], [75, 717], [2, 713], [2, 420], [440, 82]]),
                np.array([[579, 90], [409, 717], [77, 717], [499, 87]]),
                np.array([[639, 95], [746, 717], [416, 717], [579, 90]]),
                np.array([[713, 95], [1088, 717], [750, 717], [639, 97]]),
                np.array([[713, 97], [1090, 717], [1275, 717], [1282, 515], [767, 84]])
   
            ],
            'video_source': "py/video_input/thanh_xuan.mp4"
        }
    elif region_type == 'multiple':
        return {
            'regions': [
                
                # các làn xe 
                np.array([[500, 87], [75, 717], [2, 713], [2, 420], [440, 82]]),
                np.array([[579, 90], [409, 717], [77, 717], [499, 87]]),
                np.array([[639, 95], [746, 717], [416, 717], [579, 90]]),
                np.array([[713, 95], [1088, 717], [750, 717], [639, 97]]),
                np.array([[713, 97], [1090, 717], [1275, 717], [1282, 515], [767, 84]])

                #np.array([[438, 86], [2, 421], [2, 712], [1271, 711], [1269, 506], [761, 74]])
                
               
            ],
            'video_source': "py/video_input/ha_dong.mp4"
        }
    elif region_type == 'ngatuso':
        return {
            'regions': [
                np.array([[410, 87], [510, 92], [89, 705], [4, 707], [2, 451]]),
                np.array([[509, 94], [614, 99], [455, 707], [86, 704]]),
                np.array([[614, 99], [746, 95], [844, 709], [453, 705]]),
                np.array([[842, 707], [1268, 710], [1276, 586], [897, 78], [747, 97]])
            ],
            'video_source': "py/video_input/ngatuso.mp4"
        }
    else:
        raise ValueError(f"Invalid region type: {region_type}")

def init_app():
    global counter, video_capture, current_region_type
    object_classes = [2, 3, 5, 7]
    
    # Set default region points and video source
    region_data = get_region_points(current_region_type)
    region_points = region_data['regions']
    video_source = region_data['video_source']
    
    video_capture = cv2.VideoCapture(video_source)

    if not video_capture.isOpened():
        raise Exception("Không thể mở video")
    counter = MultipleObjectCounter(model_path="py/weights/yolov8n.pt", regions=region_points, classes=object_classes)

@app.route('/change_region_points', methods=['POST'])
def change_region_points():
    global counter, current_region_type, video_capture, active_video_stream
    try:
        data = request.get_json()
        region_type = data.get('type')
        
        if region_type in ['single', 'multiple', 'thanhxuan', 'ngatuso']:
            print(f"Changing to region type: {region_type}")
            
            # Dừng luồng video hiện tại
            active_video_stream = None
            time.sleep(1)  # Đợi luồng cũ dừng hoàn toàn
            
            # Release current video capture
            if video_capture is not None:
                video_capture.release()
                video_capture = None
            
            current_region_type = region_type
            # Get new region points and video source
            region_data = get_region_points(region_type)
            region_points = region_data['regions']
            video_source = region_data['video_source']
            
            print(f"Using video source: {video_source}")  # Debug log
            
            # Kiểm tra file video tồn tại
            if not os.path.exists(video_source):
                print(f"Video file not found: {video_source}")  # Debug log
                return jsonify({"status": "error", "message": f"Không tìm thấy file video: {video_source}"})
            
            # Initialize new video capture
            video_capture = cv2.VideoCapture(video_source)
            if not video_capture.isOpened():
                print(f"Failed to open video: {video_source}")  # Debug log
                return jsonify({"status": "error", "message": f"Không thể mở video: {video_source}"})
            
            # Set video properties
            video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
            video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 560)
            video_capture.set(cv2.CAP_PROP_FPS, 20)
            
            print(f"Video capture initialized with properties: {video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)}x{video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)}")  # Debug log
                
            # Reinitialize counter with new region points
            object_classes = [2, 3, 5, 7]
            counter = MultipleObjectCounter(model_path="py/weights/yolov8n.pt", regions=region_points, classes=object_classes)
            
            # Khởi động lại luồng video
            active_video_stream = 'traffic'
            
            print("Region change completed successfully")  # Debug log
            return jsonify({"status": "success"})
            
        return jsonify({"status": "error", "message": "Invalid region type"})
    except Exception as e:
        print(f"Error in change_region_points: {str(e)}")  # Debug log
        return jsonify({"status": "error", "message": str(e)})

@app.route('/toggle_warning', methods=['POST'])
def toggle_warning():
    global warning_states
    try:
        data = request.get_json()
        warning_type = data.get('warning_type')
        enabled = data.get('enabled', True)
        
        if warning_type in warning_states:
            warning_states[warning_type] = enabled
            return jsonify({"status": "success", "enabled": enabled})
        else:
            return jsonify({"status": "error", "message": "Invalid warning type"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ======================= Flask Routes ===========================
@app.route('/')
def index():
    return render_template('trang_chu.html')

@app.route('/traffic_bus')
def traffic_bus():
    """Serve traffic_bus.html từ Flask"""
    # Serve file từ thư mục gốc (ngoài py/Web)
    return send_file(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'traffic_bus.html'))

@app.route('/lai_xe')
def settings():
    return render_template('lai_xe.html')

@app.route('/hands')
def settings_hands():
    return render_template('tay_o.html')



@app.route('/video_driver')
def video_driver():
    return Response(driver_monitor(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_traffic')
def video_traffic():
    return Response(traffic_sign_monitor(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_sign')
def video_sign():
    return Response(traffic_monitor(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_vacham')
def video_vacham():
    return Response(collision_monitor(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_warnings')
def get_warnings():
    # Thêm thông tin hình ảnh biển báo vào warnings
    warnings_with_image = warnings.copy()
    warnings_with_image['sign_image'] = latest_sign_image_path
    warnings_with_image['sign_label'] = latest_sign_label
    return jsonify(warnings_with_image)

@app.route('/get_latest_sign_image')
def get_latest_sign_image():
    """Trả về hình ảnh biển báo mới nhất"""
    global latest_sign_image_path
    if latest_sign_image_path and os.path.exists(latest_sign_image_path):
        return send_file(latest_sign_image_path, mimetype='image/jpeg')
    # Trả về ảnh placeholder nếu không có ảnh
    return "", 404

@app.route('/get_stats')
def get_stats():
    global counter
    return jsonify(counter.get_stats())

@app.route('/set_mode', methods=['POST'])
def set_mode():
    global current_mode, active_video_stream
    try:
        data = request.get_json()
        new_mode = data.get('mode', 'driver')
        
        # Dừng luồng video hiện tại
        active_video_stream = None
        time.sleep(0.5)  # Đợi luồng cũ dừng
        
        current_mode = new_mode
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error in set_mode: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/start_recording')
def start_recording():
    global video_writer, is_recording, recording_start_time
    
    if not is_recording:
        # Tạo tên file dựa trên thời gian
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'recordings/output_{timestamp}.mp4'
        
        # Khởi tạo video writer với cài đặt mới
        video_writer = cv2.VideoWriter(
            filename,
            video_codec,
            fps,
            (frame_width, frame_height)
        )
        
        is_recording = True
        recording_start_time = time.time()
        return "Recording started"
    return "Already recording"

@app.route('/stop_recording')
def stop_recording():
    global is_recording, video_writer
    
    if is_recording and video_writer is not None:
        video_writer.release()
        video_writer = None
        is_recording = False
        return "Recording stopped"
    return "Not recording"

@app.route('/get_video_source/<region_type>')
def get_video_source(region_type):
    try:
        region_data = get_region_points(region_type)
        return jsonify({"video_source": region_data['video_source']})
    except Exception as e:
        return jsonify({"error": str(e)}), 400




# cử chỉ
@app.route('/reset_clicked_button', methods=['POST'])
def reset_clicked_button():
    """Đặt lại trạng thái nút đã click"""
    global clicked_button
    clicked_button = None
    return jsonify({'status': 'success'})


# ==================== API CHO CHATBOT & ĐIỀU KHIỂN GIỌNG NÓI ====================

@app.route('/api/get_ai_warnings')
def api_get_ai_warnings():
    """API để frontend lấy cảnh báo AI hiện tại"""
    return jsonify(warnings)

@app.route('/api/get_ai_alerts_history')
def api_get_ai_alerts_history():
    """API lấy lịch sử cảnh báo AI"""
    with ai_alerts_lock:
        return jsonify({
            'status': 'success',
            'alerts': ai_alerts_queue[-20:]  # Trả về 20 cảnh báo gần nhất
        })

@app.route('/api/set_monitoring_vehicle', methods=['POST'])
def api_set_monitoring_vehicle():
    """API để thiết lập vehicle_id đang được giám sát"""
    global current_monitoring_vehicle_id
    try:
        data = request.get_json()
        vehicle_id = data.get('vehicle_id')
        current_monitoring_vehicle_id = vehicle_id
        return jsonify({
            'status': 'success',
            'vehicle_id': vehicle_id,
            'message': f'Đang giám sát xe {vehicle_id}'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/process_voice_command', methods=['POST'])
def api_process_voice_command():
    """API xử lý lệnh giọng nói từ frontend"""
    try:
        data = request.get_json()
        command = data.get('command', '').lower()
        
        response = {
            'status': 'success',
            'action': 'unknown',
            'message': ''
        }
        
        # Xử lý các lệnh cơ bản
        if 'hiển thị xe' in command or 'tìm xe' in command:
            # Tìm xe theo biển số
            import re
            plate_match = re.search(r'(\d{1,2}[a-z]-\d{3}\.\d{2})', command, re.IGNORECASE)
            if plate_match:
                response['action'] = 'focus_vehicle'
                response['plate'] = plate_match.group(0).upper()
                response['message'] = f'Tìm xe biển số {plate_match.group(0).upper()}'
            elif 'gần nhất' in command:
                response['action'] = 'find_nearest'
                response['message'] = 'Tìm xe gần nhất'
            else:
                response['action'] = 'help'
                response['message'] = 'Vui lòng nói biển số xe'
                
        elif 'camera' in command or 'video' in command:
            response['action'] = 'open_camera'
            response['message'] = 'Mở camera tài xế'
            
        elif 'hỗ trợ' in command or 'chat' in command or 'nhắn tin' in command:
            response['action'] = 'open_chat'
            response['message'] = 'Mở chat hỗ trợ'
            
        elif 'cảnh báo' in command:
            response['action'] = 'show_alerts'
            response['message'] = 'Hiển thị cảnh báo'
            
        else:
            response['action'] = 'unknown'
            response['message'] = 'Không hiểu lệnh. Thử: hiển thị xe, mở camera, gọi hỗ trợ'
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/send_chat_message', methods=['POST'])
def api_send_chat_message():
    """API gửi tin nhắn vào chatbot (lưu vào database nếu cần)"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        vehicle_id = data.get('vehicle_id')
        user_id = data.get('user_id', 'anonymous')
        
        # Lưu tin nhắn vào database (nếu có)
        # Ở đây chỉ in log
        print(f"[CHAT] User {user_id} (xe {vehicle_id}): {message}")
        
        # Tạo phản hồi tự động
        bot_response = generate_bot_response(message)
        
        return jsonify({
            'status': 'success',
            'bot_response': bot_response
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

def generate_bot_response(message):
    """Sinh phản hồi tự động cho chatbot"""
    message_lower = message.lower()
    
    if 'xin chào' in message_lower or 'hello' in message_lower:
        return 'Xin chào quý khách! Vietravel Supporter có thể giúp gì cho quý khách?'
    elif 'cảm ơn' in message_lower:
        return 'Dạ không có gì ạ! Rất vui được hỗ trợ quý khách.'
    elif 'giúp' in message_lower or 'hỗ trợ' in message_lower:
        return 'Dạ vâng, quý khách cần hỗ trợ vấn đề gì ạ?'
    elif 'xe' in message_lower and ('đâu' in message_lower or 'ở đâu' in message_lower):
        return 'Quý khách vui lòng cho biết biển số xe để em kiểm tra ạ.'
    elif 'tài xế' in message_lower or 'tài xế' in message_lower:
        return 'Thông tin tài xế sẽ được hiển thị khi quý khách chọn xe trên bản đồ ạ.'
    else:
        return 'Cảm ơn bạn. Chúng tôi đã nhận được thông tin và sẽ phản hồi sớm nhất.'





if __name__ == '__main__':
    try:
        import webbrowser
        from threading import Timer
        browser_opened = False
        
        # Cấu hình cổng - có thể thay đổi nếu cổng bị chiếm
        PORT = 5001  # Đổi sang cổng 5001 (hoặc 8080, 3000, 8000...)
        
        def open_browser():
            global browser_opened
            if not browser_opened:
                webbrowser.open(f'http://127.0.0.1:{PORT}/')
                browser_opened = True
        
        init_app()
        threading.Thread(target=reset_temporary_counts, daemon=True).start()
        
        # Đợi 1.5 giây để Flask khởi động xong rồi mới mở trình duyệt
        Timer(1.5, open_browser).start()
        
        # Chạy ứng dụng Flask với use_reloader=False để tránh mở nhiều trình duyệt
        print(f"Starting server on port {PORT}...")
        app.run(debug=False, host='0.0.0.0', port=PORT, use_reloader=False)
    except Exception as e:
        print(f"Error in main: {str(e)}")