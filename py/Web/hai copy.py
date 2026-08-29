from flask import Flask, render_template, Response, jsonify, request
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
import pyttsx3  # Thêm thư viện text-to-speech

app = Flask(__name__)

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
                    else:
                        counter_yawn = 0
                        alarm_yawn_on = False

                # Đầu quay - chỉ kiểm tra nếu cảnh báo đầu được bật
                if warning_states["head"]:
                    pitch, yaw, roll = get_head_pose(points, frame.shape)
                    if abs(yaw) > 35 or pitch > 25:
                        if can_play_warning("head"):
                            dau_quay_sound.play()
                        warnings["head"] = "ĐẦU XOAY NHIỀU!"

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

            # Giám sát tay lái - chỉ kiểm tra nếu cảnh báo tay lái được bật
            if warning_states["hand"]:
                frame = hand_detector.findArmsAndHands(frame)

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

# ======================= Video cảnh báo biển báo ===========================
def traffic_sign_monitor():
    global warnings, video_writer, is_recording, active_video_stream
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

            if boxes is not None:
                for i in range(len(boxes)):
                    cls_id = int(boxes.cls[i])
                    conf = float(boxes.conf[i])
                    label = bienbao_model.names[cls_id]
                    x1, y1, _, _ = map(int, boxes.xyxy[i])
                    

            # Reset warnings
            warnings["speed"] = ""
            warnings["sign"] = ""

            # Cập nhật cảnh báo
            current_time = time.time()
            if boxes is not None:
                for i in range(len(boxes)):
                    cls_id = int(boxes.cls[i])
                    label = bienbao_model.names[cls_id]
                    
                    # Xử lý biển báo tốc độ
                    if "speed" in label.lower():
                        warnings["speed"] = f"BIỂN BÁO TỐC ĐỘ: {label}"
                        # Phát âm thanh nếu chưa phát trong 3 giây qua
                        if last_sign_time is None or current_time - last_sign_time > 3:
                            bienbao_sound.play()
                            last_sign_time = current_time
                    else:
                        warnings["sign"] = f"{label}"
                        # Phát âm thanh nếu chưa phát trong 3 giây qua
                        if last_sign_time is None or current_time - last_sign_time > 3:
                            bienbao_sound.play()
                            last_sign_time = current_time

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

def process_collision_warning(frame, distance, current_time):
    global last_collision_warning, warnings
    
    if distance < 8:
        warnings["collision"] = "CẢNH BÁO VA CHẠM!"
        if current_time - last_collision_warning >= warning_interval:
            va_cham_sound.play()
            last_collision_warning = current_time
    elif distance < 15:
        warnings["collision"] = "GIỮ KHOẢNG CÁCH!"
    else:
        warnings["collision"] = ""

def process_lane_warning(frame, left_found, right_found):
    global warnings
    
    if not (left_found and right_found):
        warnings["lane"] = "CẢNH BÁO LỆCH LÀN!"
        if not pygame.mixer.get_busy():
            lech_lan_sounds.play()
    else:
        warnings["lane"] = ""

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


# phần điểu chirng bằng tay

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

@app.route('/lai_xe')
def settings():
    return render_template('lai_xe.html')


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
    return jsonify(warnings)

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




if __name__ == '__main__':
    try:
        import webbrowser
        from threading import Timer
        
        # Cấu hình cổng - có thể thay đổi nếu cổng bị chiếm
        PORT = 5001  # Đổi sang cổng 5001 (hoặc 8080, 3000, 8000...)
        
        browser_opened = False
        
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