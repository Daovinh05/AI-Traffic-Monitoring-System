"""
AI Traffic Monitoring System - Models
Contains database models, data structures, and business logic
"""

import pymysql
import os
from datetime import datetime, timedelta
import cv2
import dlib
import numpy as np
import pygame
import threading
import time
from ultralytics import YOLO
from shapely.geometry import Point, Polygon
import mediapipe as mp
from flask import session

# ========================================
# GLOBAL VARIABLES FOR AI ALERTS & CHATBOT
# ========================================
ai_alerts_queue = []
ai_alerts_lock = threading.Lock()
ai_alert_counter = 0 # Thêm counter cho ID
MAX_ALERTS_HISTORY = 50
current_monitoring_vehicle_id = None

def add_ai_alert(alert_type, message, vehicle_id=None):
    """Thêm cảnh báo AI vào hàng đợi"""
    global ai_alerts_queue, ai_alert_counter
    with ai_alerts_lock:
        ai_alert_counter += 1
        alert = {
            'id': ai_alert_counter, # Gán ID duy nhất
            'type': alert_type,
            'message': message,
            'vehicle_id': vehicle_id,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'level': 'critical' if alert_type in ['eye', 'phone', 'seatbelt', 'collision'] else 'warning'
        }
        ai_alerts_queue.append(alert)
        if len(ai_alerts_queue) > MAX_ALERTS_HISTORY:
            ai_alerts_queue = ai_alerts_queue[-MAX_ALERTS_HISTORY:]
        print(f"[AI ALERT] {alert_type}: {message}")
        
        # Ghi vào database (Cần import db context nếu được, tạm thời dùng pymysql độc lập)
        try:
            conn = pymysql.connect(
                host='localhost',
                port=3306,
                user='root',
                password='',
                database='giam_sat',
                cursorclass=pymysql.cursors.DictCursor,
                charset='utf8mb4'
            )
            cur = conn.cursor()
            
            # Lấy thông tin phương tiện và tài xế
            plate = 'N/A'
            driver_name = 'N/A'
            driver_id = None
            
            if vehicle_id:
                cur.execute("""
                    SELECT p.bien_so, t.id as id_tai_xe, t.ho_ten 
                    FROM phuong_tien p
                    LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
                    WHERE p.id = %s
                """, (vehicle_id,))
                res = cur.fetchone()
                if res:
                    plate = res['bien_so']
                    driver_id = res['id_tai_xe']
                    driver_name = res['ho_ten']
            
            # Cập nhật thông tin vào object alert trong queue
            alert['plate'] = plate
            alert['driver_name'] = driver_name
            # Ghi đè tin nhắn để có thêm thông tin nếu cần
            # alert['message'] = f"[{plate} - {driver_name}] {message}"
            
            cur.execute("""
                INSERT INTO canh_bao_vi_pham (loai_vi_pham, noi_dung_vi_pham, muc_do, thoi_gian_vi_pham, id_phuong_tien, id_tai_xe) 
                VALUES (%s, %s, %s, NOW(), %s, %s)
            """, (alert_type, message, alert['level'], vehicle_id, driver_id))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error saving AI alert to DB: {e}")

# ========================================
# SOUND & WARNING SYSTEM
# ========================================
latest_warning = ""
lock = threading.Lock()
pygame.init()

# Sound files
SOUND_DIR = "py/Sound"
chopmat_sound = pygame.mixer.Sound(os.path.join(SOUND_DIR, "nham_mat.wav"))
ngap_sound = pygame.mixer.Sound(os.path.join(SOUND_DIR, "ngap_ngu.wav"))
phone_baodong = pygame.mixer.Sound(os.path.join(SOUND_DIR, "not_phone.wav"))
seatbelt_baodong = pygame.mixer.Sound(os.path.join(SOUND_DIR, "seatbelt_alert.wav"))
dau_quay_sound = pygame.mixer.Sound(os.path.join(SOUND_DIR, "chuylaixe.wav"))
bienbao_sound = pygame.mixer.Sound(os.path.join(SOUND_DIR, "chu_y_bien_bao.wav"))
tay_lai_sound = pygame.mixer.Sound(os.path.join(SOUND_DIR, "tay_lai_xe.wav"))
lech_lan_sounds = pygame.mixer.Sound(os.path.join(SOUND_DIR, "lech_lan.wav"))
va_cham_sound = pygame.mixer.Sound(os.path.join(SOUND_DIR, "va_cham.wav"))
di_cham_lai_sound = pygame.mixer.Sound(os.path.join(SOUND_DIR, "di_cham_lai.wav"))

WARNING_INTERVALS = {
    "eye": 2,
    "yawn": 3,
    "head": 3,
    "phone": 3,
    "seatbelt": 4,
    "hand": 4
}

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

# ========================================
# VIDEO RECORDING CONFIG
# ========================================
video_writer = None
is_recording = False
recording_start_time = None
current_video_filename = None
current_video_path = None
current_video_cam_id = None
fps = 30.0
frame_width = 1280
frame_height = 720
video_codec = cv2.VideoWriter_fourcc(*'avc1')

if not os.path.exists('recordings'):
    os.makedirs('recordings')

# ========================================
# AI MODELS
# ========================================
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("py/shape_predictor_68_face_landmarks.dat")
phone_mau = YOLO("py/weights/yolov8n.pt")
seatbelt_mau = YOLO("py/weights/day_an_toan.pt")
bienbao_model = YOLO("py/weights/bien_bao.pt")
model_vehicle = YOLO("py/weights/yolov8n.pt")
model_lane = YOLO("py/weights/lech_lan.pt")
model_hole = YOLO("py/weights/vat_can.pt")

# ========================================
# FACE LANDMARK CONFIG
# ========================================
EAR_THRESHOLD = 0.30
EAR_MIN_DURATION = 2
YAWN_THRESHOLD = 25
YAWN_CONSEC_FRAMES = 15

left_eye_indexes = [36, 37, 38, 39, 40, 41]
right_eye_indexes = [42, 43, 44, 45, 46, 47]
mouth_indexes = [48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59]

# ========================================
# HELPER FUNCTIONS
# ========================================
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

    pitch = eulerAngles[0]
    yaw = eulerAngles[1]
    roll = eulerAngles[2]

    if pitch > 90:
        pitch = pitch - 180
    elif pitch < -90:
        pitch = pitch + 180

    if yaw > 90:
        yaw = yaw - 180
    elif yaw < -90:
        yaw = yaw + 180

    if roll > 90:
        roll = roll - 180
    elif roll < -90:
        roll = roll + 180

    return [float(pitch), float(yaw), float(roll)]

# ========================================
# LANE DETECTION HELPERS
# ========================================
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
    roi_array = np.array(roi_vertices, np.int32)
    cv2.fillPoly(mask, [roi_array], 255)
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

def process_lane_warning(frame, left_found, right_found):
    global warnings, lane_alert_sent

    if not warning_states.get("lane", True):
        warnings["lane"] = ""
        return

    if not (left_found and right_found):
        warnings["lane"] = "CẢNH BÁO LỆCH LÀN!"
        if not pygame.mixer.get_busy():
            lech_lan_sounds.play()
    else:
        warnings["lane"] = ""
        lane_alert_sent = False

def detect_lane_deviation_combined(results_l, frame, width, classic_lines):
    center_x = width // 2
    left_found, right_found = False, False

    for box in results_l.boxes:
        x1, _, x2, _ = map(int, box.xyxy[0])
        cx = (x1 + x2) // 2
        if cx < center_x - 50:
            left_found = True
        elif cx > center_x + 50:
            right_found = True

    for line in classic_lines:
        x1, _, x2, _ = line
        cx = (x1 + x2) // 2
        if cx < center_x - 50:
            left_found = True
        elif cx > center_x + 50:
            right_found = True

    process_lane_warning(frame, left_found, right_found)
    return frame

# ========================================
# HAND AND ARM TRACKING
# ========================================
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
                if self.last_warning_time is None or current_time - self.last_warning_time >= self.warning_interval:
                    tay_lai_sound.play()
                    self.last_warning_time = current_time
                    # Update warnings directly (they are in the same module)
                    warnings["hand"] = "CẢNH BÁO: KHÔNG CẦM VÔ LĂNG!"
        else:
            self.no_fist_start_time = None
            self.last_warning_time = None
            warnings["hand"] = ""

        return img

hand_detector = HandAndArmTracking()

# ========================================
# GLOBAL WARNING STATES
# ========================================
current_mode = "driver"
warning_states = {
    "eye": True,
    "yawn": True,
    "head": True,
    "phone": True,
    "seatbelt": True,
    "hand": True,
    "collision": True,
    "lane": True,
    "obstacle": True
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
    "lane": "",
    "obstacle": ""
}

active_video_stream = None

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

# ========================================
# TRAFFIC SIGN MONITORING
# ========================================
PICTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'pictures')
latest_sign_image_path = None
latest_sign_label = ""

if not os.path.exists(PICTURES_DIR):
    os.makedirs(PICTURES_DIR)

# ========================================
# COLLISION DETECTION VARIABLES
# ========================================
last_collision_warning = 0
warning_interval = 1.0
collision_alert_sent = False
lane_alert_sent = False

# ========================================
# TRAFFIC MONITORING
# ========================================
region_colors = [
    (255, 0, 255),
    (0, 255, 255),
    (86, 0, 254),
    (0, 128, 255),
    (235, 183, 0),
    (255, 34, 134)
]

vehicle_colors = {
    2: (255, 0, 0),
    3: (255,255,0),
    5: (0, 255, 0),
    7: (0, 0, 128)
}

class MultipleObjectCounter:
    def __init__(self, model_path="py/weights/yolov8n.pt", regions=None, classes=None):
        self.model = YOLO(model_path)
        self.regions = regions if regions is not None else []
        self.classes = classes if classes is not None else []

        self.in_counts = [0] * len(self.regions)
        self.out_counts = [0] * len(self.regions)
        self.counted_ids = [set() for _ in range(len(self.regions))]
        self.tracking_history = {}

        self.region_stats = [{
            'car': 0,
            'motorcycle': 0,
            'bus': 0,
            'truck': 0,
            'total': 0
        } for _ in range(len(self.regions))]

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

        self.temp_vehicle_type_counts = {'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0}
        self.lock = threading.Lock()
        self.vehicles_in_regions = [set() for _ in range(len(self.regions))]

    def update_traffic_status(self):
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
        results = self.model.track(frame, persist=True, classes=self.classes)

        if results[0].boxes.id is None:
            return frame

        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.cpu().numpy().astype(int)
        clss = results[0].boxes.cls.cpu().numpy().astype(int)

        self.stats['vehicle_types'] = {'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0}

        for region_vehicles in self.vehicles_in_regions:
            region_vehicles.clear()

        for i, region_points in enumerate(self.regions):
            color = region_colors[i % len(region_colors)]
            cv2.polylines(frame, [np.array(region_points)], True, color, 2)

            xs = [pt[0] for pt in region_points]
            ys = [pt[1] for pt in region_points]
            cx = int(sum(xs) / len(xs))
            cy = int(sum(ys) / len(ys))

            cv2.putText(frame, f"Khu : {i+1}", (cx - 50, cy - 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.putText(frame, f"Sum : {self.region_stats[i]['total']}",
                       (cx - 50, cy - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        for box, track_id, cls in zip(boxes, track_ids, clss):
            color = vehicle_colors.get(cls, (255, 255, 255))
            cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), color, 2)

            vehicle_type = "Car" if cls == 2 else "Motorcycle" if cls == 3 else "Bus" if cls == 5 else "Truck"
            label_size = cv2.getTextSize(vehicle_type, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(frame,
                        (int(box[0]), int(box[1] - label_size[1] - 10)),
                        (int(box[0] + label_size[0]), int(box[1])),
                        color, -1)
            cv2.putText(frame, vehicle_type,
                       (int(box[0]), int(box[1] - 5)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            current_centroid = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)

            if track_id not in self.tracking_history:
                self.tracking_history[track_id] = []
            self.tracking_history[track_id].append(current_centroid)

            if len(self.tracking_history[track_id]) > 30:
                self.tracking_history[track_id] = self.tracking_history[track_id][-30:]

            for r_idx, region_points in enumerate(self.regions):
                polygon = Polygon(region_points)
                if polygon.contains(Point(current_centroid)):
                    self.vehicles_in_regions[r_idx].add(track_id)

                    if track_id not in self.counted_ids[r_idx]:
                        if len(self.tracking_history[track_id]) > 1:
                            prev_centroid = self.tracking_history[track_id][-2]
                            if not polygon.contains(Point(prev_centroid)):
                                self.in_counts[r_idx] += 1
                                self.counted_ids[r_idx].add(track_id)

                                self.region_stats[r_idx][vehicle_type.lower()] += 1
                                self.region_stats[r_idx]['total'] += 1

                                self.stats['lane_counts'][r_idx] = self.in_counts[r_idx]
                                self.stats['region_details'] = self.region_stats
                                self.update_traffic_status()

        for r_idx, region_vehicles in enumerate(self.vehicles_in_regions):
            self.region_stats[r_idx] = {
                'car': 0,
                'motorcycle': 0,
                'bus': 0,
                'truck': 0,
                'total': len(region_vehicles)
            }

            for track_id in region_vehicles:
                if track_id in self.tracking_history:
                    for box, tid, cls in zip(boxes, track_ids, clss):
                        if tid == track_id:
                            vehicle_type = "car" if cls == 2 else "motorcycle" if cls == 3 else "bus" if cls == 5 else "truck"
                            self.region_stats[r_idx][vehicle_type] += 1
                            break

        self.update_traffic_status()
        return frame

    def get_stats(self):
        return self.stats

counter = None
video_capture = None
current_region_type = 'single'
current_location_id = "hanoi"

location_video_map = {
    "hanoi": "single",
    "hadong": "multiple",
    "thanhxuan": "thanhxuan",
    "ngatuso": "ngatuso"
}

def get_region_points(region_type):
    if region_type == 'single':
        return {
            'regions': [
                np.array([[443, 79], [4, 399], [4, 709], [1267, 711], [1272, 401], [877, 39], [475, 57]])
            ],
            'video_source': "py/video_input/ha_noi.mp4"
        }
    elif region_type == 'thanhxuan':
        return {
            'regions': [
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
                np.array([[500, 87], [75, 717], [2, 713], [2, 420], [440, 82]]),
                np.array([[579, 90], [409, 717], [77, 717], [499, 87]]),
                np.array([[639, 95], [746, 717], [416, 717], [579, 90]]),
                np.array([[713, 95], [1088, 717], [750, 717], [639, 97]]),
                np.array([[713, 97], [1090, 717], [1275, 717], [1282, 515], [767, 84]])
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

    region_data = get_region_points(current_region_type)
    region_points = region_data['regions']
    video_source = region_data['video_source']

    video_capture = cv2.VideoCapture(video_source)

    if not video_capture.isOpened():
        raise Exception("Không thể mở video")
    counter = MultipleObjectCounter(model_path="py/weights/yolov8n.pt", regions=region_points, classes=object_classes)


# ========================================
# VIDEO MONITORING FUNCTIONS
# ========================================
def driver_monitor(vehicle_id=None):
    """Generator function for driver monitoring video stream"""
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

            warnings["eye"] = ""
            warnings["yawn"] = ""
            warnings["head"] = ""
            warnings["phone"] = ""
            warnings["seatbelt"] = ""
            warnings["hand"] = ""

            for face in faces:
                shape = predictor(gray, face)
                points = [(shape.part(i).x, shape.part(i).y) for i in range(68)]

                for idx in left_eye_indexes + right_eye_indexes + mouth_indexes:
                    x, y = points[idx]
                    cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

                # Draw facial landmarks
                for i in range(0, 17):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(0, 16):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)

                for i in range(17, 22):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(17, 21):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)

                for i in range(22, 27):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(22, 26):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)

                for i in range(27, 36):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(27, 35):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)

                for i in range(36, 42):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(36, 41):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)
                cv2.line(frame, points[41], points[36], (255, 255, 255), 1)

                for i in range(42, 48):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(42, 47):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)
                cv2.line(frame, points[47], points[42], (255, 255, 255), 1)

                for i in range(48, 60):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(48, 59):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)
                cv2.line(frame, points[59], points[48], (255, 255, 255), 1)

                for i in range(60, 68):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(60, 67):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)
                cv2.line(frame, points[67], points[60], (255, 255, 255), 1)

                # Eye closure detection
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
                            if previous_warnings["eye"] != "NHẮM MẮT QUÁ LÂU!":
                                add_ai_alert("eye", "Tài xế đang nhắm mắt quá lâu!", vehicle_id)
                    else:
                        eye_closed_time = None

                # Yawn detection
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
                                add_ai_alert("yawn", "Tài xế đang ngáp ngủ!", vehicle_id)
                    else:
                        counter_yawn = 0
                        alarm_yawn_on = False

                # Head pose detection
                if warning_states["head"]:
                    pitch, yaw, roll = get_head_pose(points, frame.shape)
                    if abs(yaw) > 40 or pitch > 35:
                        if can_play_warning("head"):
                            dau_quay_sound.play()
                        warnings["head"] = "MẤT TẬP TRUNG !"
                        if previous_warnings["head"] != "MẤT TẬP TRUNG !":
                            add_ai_alert("head", "Tài xế mất tập trung (quay đầu/ngửa đầu)!", vehicle_id)

                    cv2.rectangle(frame, (10, 10), (200, 75), (0, 0, 0), cv2.FILLED)
                    cv2.putText(frame, f"Pitch: {pitch:.1f}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    cv2.putText(frame, f"Yaw: {yaw:.1f}", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    cv2.putText(frame, f"Roll: {roll:.1f}", (10, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            # Phone detection
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
                                add_ai_alert("phone", "Tài xế đang dùng điện thoại!", vehicle_id)
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                            cv2.putText(frame, label, (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Seatbelt detection
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
                        add_ai_alert("seatbelt", "Tài xế không đeo dây an toàn!", vehicle_id)

            # Hand detection
            if warning_states["hand"]:
                frame = hand_detector.findArmsAndHands(frame)
                if warnings["hand"] and previous_warnings["hand"] != warnings["hand"]:
                    add_ai_alert("hand", warnings["hand"], vehicle_id)

            # Update previous warnings
            for key in previous_warnings:
                previous_warnings[key] = warnings[key] if warnings[key] else ""

            # Resize frame
            frame = cv2.resize(frame, (frame_width, frame_height))

            # Record if enabled
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


def traffic_sign_monitor(vehicle_id=None):
    """Generator function for traffic sign monitoring video stream"""
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

            warnings["speed"] = ""
            warnings["sign"] = ""
            latest_sign_label = ""

            current_time = time.time()
            if boxes is not None:
                for i in range(len(boxes)):
                    cls_id = int(boxes.cls[i])
                    label = bienbao_model.names[cls_id]
                    x1, y1, x2, y2 = map(int, boxes.xyxy[i])

                    if "speed" in label.lower():
                        warnings["speed"] = f"BIỂN BÁO TỐC ĐỘ: {label}"
                        latest_sign_label = label
                        if last_sign_time is None or current_time - last_sign_time > 3:
                            bienbao_sound.play()
                            last_sign_time = current_time
                    else:
                        warnings["sign"] = f"{label}"
                        latest_sign_label = label
                        if last_sign_time is None or current_time - last_sign_time > 3:
                            bienbao_sound.play()
                            last_sign_time = current_time

                    try:
                        h, w = frame.shape[:2]
                        x1 = max(0, min(x1, w))
                        y1 = max(0, min(y1, h))
                        x2 = max(0, min(x2, w))
                        y2 = max(0, min(y2, h))

                        if x2 > x1 and y2 > y1:
                            sign_crop = frame[y1:y2, x1:x2]
                            sign_crop = cv2.resize(sign_crop, (200, 200))
                            latest_sign_image_path = os.path.join(PICTURES_DIR, 'latest_sign.jpg')
                            cv2.imwrite(latest_sign_image_path, sign_crop)
                            print(f"Saved sign image to: {latest_sign_image_path}")
                    except Exception as e:
                        print(f"Error cropping sign image: {e}")

            annotated = cv2.resize(annotated, (frame_width, frame_height))

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


def collision_monitor(vehicle_id=None):
    """Generator function for collision monitoring video stream"""
    global warnings, video_writer, is_recording, active_video_stream, last_collision_warning
    try:
        active_video_stream = 'vacham'
        cap = cv2.VideoCapture("py/video_input/lech_lan.mp4")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 20)

        last_obstacle_warning = 0
        obstacle_warning_interval = 2.0

        while active_video_stream == 'vacham':
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame from collision camera")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            frame = cv2.resize(frame, (960, 540))
            height, width = frame.shape[:2]
            current_time = time.time()

            warnings["collision"] = ""
            warnings["lane"] = ""
            warnings["obstacle"] = ""

            need_collision_detection = warning_states.get("collision", True)
            need_lane_detection = warning_states.get("lane", True)
            need_obstacle_detection = warning_states.get("obstacle", True)

            if not (need_collision_detection or need_lane_detection or need_obstacle_detection):
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                continue

            # Obstacle detection
            if need_obstacle_detection:
                results_hole = model_hole(frame, verbose=False)
                obstacle_detected = False
                obstacle_count = 0
                max_conf = 0.0

                for result in results_hole:
                    if result.masks is not None:
                        if result.boxes is not None:
                            for i, box in enumerate(result.boxes):
                                conf = float(box.conf[0])
                                if conf > 0.3:
                                    obstacle_detected = True
                                    obstacle_count += 1
                                    if conf > max_conf:
                                        max_conf = conf

                                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                                    frame = result.plot(labels=False, conf=False, line_width=2)
                                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                                    label = f"Chuong ngai vat {conf:.2f}"
                                    cv2.putText(frame, label, (x1, y1 - 10),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        else:
                            obstacle_detected = True
                            obstacle_count += len(result.masks)
                            frame = result.plot(labels=False, conf=False, line_width=2)

                    elif result.boxes is not None:
                        for box in result.boxes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            conf = float(box.conf[0])
                            cls = int(box.cls[0])

                            if conf > 0.3:
                                obstacle_detected = True
                                obstacle_count += 1
                                if conf > max_conf:
                                    max_conf = conf

                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                                label = f"Chuong ngai vat {conf:.2f}"
                                cv2.putText(frame, label, (x1, y1 - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                if obstacle_detected and max_conf > 0.3:
                    warnings["obstacle"] = f"VẬT CẢN PHÍA TRƯỚC! ({obstacle_count})"
                    if current_time - last_obstacle_warning >= obstacle_warning_interval:
                        di_cham_lai_sound.play()
                        last_obstacle_warning = current_time
                else:
                    warnings["obstacle"] = ""

            # Vehicle detection
            if need_collision_detection:
                results_v = model_vehicle(frame)[0]
                for box in results_v.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = model_vehicle.names[cls]

                if label in ['car', 'truck', 'bus', 'motorbike', 'person']:
                    distance = estimate_distance(y1, y2)

                    if label == 'person':
                        critical_distance = 12
                        warning_distance = 20
                    else:
                        critical_distance = 8
                        warning_distance = 15

                    if distance < critical_distance:
                        warnings["collision"] = "CẢNH BÁO VA CHẠM!"
                        if current_time - last_collision_warning >= warning_interval:
                            va_cham_sound.play()
                            last_collision_warning = current_time
                        color = (0, 0, 255)
                    elif distance < warning_distance:
                        warnings["collision"] = "GIỮ KHOẢNG CÁCH!"
                        color = (0, 255, 255)
                        collision_alert_sent = False
                    else:
                        warnings["collision"] = ""
                        color = (0, 255, 0)
                        collision_alert_sent = False

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                    label_text = f'{label} {conf:.2f} | {distance:.1f}m'
                    if label == 'person':
                        label_text = f'NGUOI {conf:.2f} | {distance:.1f}m'

                    cv2.putText(frame, label_text, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                    if label == 'person' and distance < warning_distance:
                        cv2.circle(frame, ((x1 + x2) // 2, (y1 + y2) // 2), 10, (0, 0, 255), -1)

            # Lane detection
            if need_lane_detection:
                results_l = model_lane(frame)[0]
                frame = draw_lane_points(frame, results_l, width)
                frame, classic_lines = draw_lane_classic(frame)
                frame = detect_lane_deviation_combined(results_l, frame, width, classic_lines)

            frame = cv2.resize(frame, (frame_width, frame_height))

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


def traffic_monitor():
    """Generator function for traffic flow monitoring video stream"""
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
    """Reset temporary vehicle counts every 10 seconds"""
    global counter
    while True:
        time.sleep(10)
        if counter:
            with counter.lock:
                print("Thống kê trong 10 giây qua:", counter.temp_vehicle_type_counts)
                counter.temp_vehicle_type_counts = {'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0}


# ========================================
# AI CHATBOT FUNCTIONS
# ========================================
def generate_bot_response(message, vehicle_id=None):
    """AI Rule-based response (fallback khi không có LLM API)"""
    message_lower = message.lower().strip()

    if any(x in message_lower for x in ['xin chào', 'hello', 'hi', 'chào']):
        return 'Xin chào quý khách! 🚗 Tôi là Vietravel Supporter. Tôi có thể giúp gì cho bạn?'

    if any(x in message_lower for x in ['cảm ơn', 'cam on', 'thanks']):
        return 'Dạ không có gì ạ! Rất vui được hỗ trợ quý khách. 😊'

    if any(x in message_lower for x in ['xe ở đâu', 'vị trí xe', 'xe nào', 'tìm xe']):
        import re
        plate_match = re.search(r'(\d{1,2}[a-zA-Z]-\d{3}\.\d{2})', message, re.IGNORECASE)
        if plate_match:
            plate = plate_match.group(0).upper()
            try:
                conn = pymysql.connect(host='localhost', port=3306, user='root', password='', database='giam_sat', cursorclass=pymysql.cursors.DictCursor, charset='utf8mb4')
                cur = conn.cursor()
                cur.execute('''
                    SELECT p.bien_so, t.ho_ten, td.ten_tuyen 
                    FROM phuong_tien p
                    LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
                    LEFT JOIN tuyen_duong td ON p.id_tuyen_duong = td.id
                    WHERE p.bien_so = %s
                ''', (plate,))
                v = cur.fetchone()
                cur.close()
                conn.close()
                if v:
                    return f"🚗 Xe {v['bien_so']} do tài xế {v['ho_ten']} lái, đang ở vị trí: {v['ten_tuyen']}"
                else:
                    return f"❌ Không tìm thấy xe biển số {plate}"
            except Exception as e:
                print(e)
                return f"❌ Lỗi truy vấn cơ sở dữ liệu"
        return 'Bạn vui lòng cho biết biển số xe, ví dụ: "Xe 29B-222.22 ở đâu?"'

    if any(x in message_lower for x in ['vi phạm', 'cảnh báo', 'lỗi', 'bị phạt']):
        return f'''📊 Thống kê vi phạm hôm nay:
- 📱 Dùng điện thoại: {warnings.get('phone', '') and 1 or 0} lần
- 😴 Ngáp ngủ: {warnings.get('yawn', '') and 1 or 0} lần
- ⚠️ Không dây an toàn: {warnings.get('seatbelt', '') and 1 or 0} lần
- 🚨 Va chạm: {warnings.get('collision', '') and 1 or 0} lần

Bạn muốn xem chi tiết xe nào?'''

    if any(x in message_lower for x in ['tài xế', 'tài xế nào', 'ai lái']):
        return '''👨‍✈️ Danh sách tài xế đang hoạt động:
1. Nguyễn Văn Đức - 29A-111.11
2. Trần Văn Hoan - 29B-222.22
3. Lê Thị Đào - 30E-333.33

Bạn cần thông tin tài xế nào?'''

    if any(x in message_lower for x in ['hỗ trợ', 'giúp', 'help', 'cần giúp']):
        return '''🆘 Tôi có thể giúp bạn:
- 📍 Theo dõi vị trí xe
- ⚠️ Xem cảnh báo vi phạm
- 👤 Thông tin tài xế
- 📊 Thống kê hành trình

Bạn cần gì?'''

    if any(x in message_lower for x in ['thời tiết', 'giao thông', 'đường xá']):
        return '''🌤️ Thời tiết Hà Nội:
- Nhiệt độ: 25°C
- Trời nắng đẹp
- Giao thông thuận lợi

Chúc bạn lái xe an toàn! 🚗'''

    if any(x in message_lower for x in ['tạm biệt', 'bye', 'goodbye', 'kết thúc']):
        return 'Cảm ơn bạn đã sử dụng dịch vụ! Chúc bạn một ngày tốt lành! 🌟'

    return '''Cảm ơn bạn đã nhắn tin!
Tôi đã nhận được yêu cầu và sẽ phản hồi sớm nhất.

Hoặc bạn có thể:
- 🎤 Nói: "Xem cảnh báo"
- 📍 Hỏi: "Xe 29B-222.22 ở đâu?"
- 📊 Hỏi: "Thống kê hôm nay"'''


def call_llm_api(message, vehicle_id=None):
    """Gọi API từ mô hình AI thực thụ (LLM)"""
    try:
        from groq import Groq
        import os
        from dotenv import load_dotenv

        load_dotenv()
        GROQ_API_KEY = os.getenv('GROQ_API_KEY')

        if not GROQ_API_KEY:
            print("⚠️ Không tìm thấy GROQ_API_KEY trong .env file")
            return None

        client = Groq(api_key=GROQ_API_KEY)

        # Lấy dữ liệu xe thật từ DB cho AI Context
        vehicles_data = []
        try:
            conn = pymysql.connect(host='localhost', port=3306, user='root', password='', database='giam_sat', cursorclass=pymysql.cursors.DictCursor, charset='utf8mb4')
            cur = conn.cursor()
            cur.execute('''
                SELECT p.bien_so as plate, t.ho_ten as driver, td.ten_tuyen as location, 
                       p.trang_thai_hoat_dong as status, p.toc_do_hien_tai as speed
                FROM phuong_tien p
                LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
                LEFT JOIN tuyen_duong td ON p.id_tuyen_duong = td.id
                LIMIT 10
            ''')
            vehicles_data = cur.fetchall()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error loading vehicles for LLM: {e}")

        vehicles_info = "\n".join([
            f"- {v['plate']}: Tài xế {v['driver']}, vị trí {v['location']}, trạng thái {v['status']}, tốc độ {v['speed']} km/h"
            for v in vehicles_data
        ])

        context = f"""
Bạn là trợ lý ảo AI của Vietravel, hỗ trợ giám sát giao thông và an toàn lái xe.

=== THÔNG TIN XE THỰC TẾ (DATA TỪ HỆ THỐNG) ===
Danh sách xe đang giám sát:
{vehicles_info}

=== CẢNH BÁO AI ĐANG HOẠT ĐỘNG ===
- Nhắm mắt: {warnings.get('eye', 'Không có') or 'Không có'}
- Ngáp ngủ: {warnings.get('yawn', 'Không có') or 'Không có'}
- Mất tập trung: {warnings.get('head', 'Không có') or 'Không có'}
- Dùng điện thoại: {warnings.get('phone', 'Không có') or 'Không có'}
- Không dây an toàn: {warnings.get('seatbelt', 'Không có') or 'Không có'}
- Không cầm vô lăng: {warnings.get('hand', 'Không có') or 'Không có'}
- Va chạm: {warnings.get('collision', 'Không có') or 'Không có'}
- Lệch làn: {warnings.get('lane', 'Không có') or 'Không có'}

=== USER MESSAGE ===
{message}

=== TRẢ LỜI ===
"""

        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là trợ lý giao thông Vietravel. Trả lời bằng tiếng Việt, thân thiện. LUÔN TRA CỨU DANH SÁCH XE KHI ĐƯỢC HỎI VỀ VỊ TRÍ."
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            temperature=0.7,
            max_tokens=500,
            top_p=1.0,
            stream=False,
            stop=None
        )

        response = chat_completion.choices[0].message.content
        print(f"🤖 [GROQ AI] Response: {response[:100]}...")
        return response

    except ImportError:
        print("⚠️ Chưa cài groq. Chạy: pip install groq")
        return None
    except Exception as e:
        print(f"❌ Lỗi Groq API: {e}")
        return None


def process_ai_chat_message(message, vehicle_id=None):
    """Xử lý tin nhắn chatbot với AI thực thụ"""
    llm_response = call_llm_api(message, vehicle_id)

    if llm_response:
        return llm_response

    print("⚠️ Fallback về rule-based AI")
    return generate_bot_response(message, vehicle_id)


def call_groq_law_advisor(question):
    """Gọi Groq API để tư vấn luật giao thông"""
    try:
        from groq import Groq
        import os
        from dotenv import load_dotenv

        load_dotenv()
        GROQ_API_KEY = os.getenv('GROQ_API_KEY')

        if not GROQ_API_KEY:
            print("⚠️ Không tìm thấy GROQ_API_KEY")
            return generate_law_response_fallback(question)

        client = Groq(api_key=GROQ_API_KEY)

        law_database = """
**NGUỒN LUẬT:**
- Luật Giao thông đường bộ 2008
- Nghị định 100/2019/NĐ-CP (xử phạt vi phạm giao thông)
- Nghị định 123/2021/NĐ-CP (sửa đổi, bổ sung)
- Các văn bản hướng dẫn thi hành

**MỨC PHẠT CHÍNH XÁC 2026:**

### 1. PHẠT QUÁ TỐC ĐỘ:
**Ô tô:**
- Quá 5-10 km/h: 800.000đ
- Quá 10-20 km/h: 3-5 triệu đồng + tước GPLX 1-3 tháng
- Quá 20-35 km/h: 6-8 triệu đồng + tước GPLX 2-4 tháng
- Quá trên 35 km/h: 10-12 triệu đồng + tước GPLX 4-6 tháng

**Xe máy:**
- Quá 5-10 km/h: 400-600 nghìn đồng
- Quá 10-20 km/h: 800 nghìn - 1 triệu đồng
- Quá 20-35 km/h: 4-5 triệu đồng + tước GPLX 1-3 tháng
- Quá trên 35 km/h: 6-8 triệu đồng + tước GPLX 2-4 tháng

### 2. PHẠT NỒNG ĐỘ CỒN (Điều 5, Nghị định 100):
**Ô tô:**
- Mức 1: 6-8 triệu đồng + tước GPLX 10-12 tháng
- Mức 2: 16-18 triệu đồng + tước GPLX 16-18 tháng
- Mức 3: 30-40 triệu đồng + tước GPLX 22-24 tháng

**Xe máy:**
- Mức 1: 2-3 triệu đồng + tước GPLX 10-12 tháng
- Mức 2: 4-5 triệu đồng + tước GPLX 16-18 tháng
- Mức 3: 6-8 triệu đồng + tước GPLX 22-24 tháng

### 3. PHẠT KHÔNG ĐỘI MŨ BẢO HIỂM (Điều 6, Nghị định 100):
- Người điều khiển: 400-600 nghìn đồng
- Người ngồi sau: 400-600 nghìn đồng
- Trẻ em dưới 6 tuổi: Được miễn trừ

### 4. PHẠT VƯỢT ĐÈN ĐỎ (Điều 5, Nghị định 100):
**Ô tô:** 4-6 triệu đồng + tước GPLX 1-3 tháng
**Xe máy:** 800 nghìn - 1 triệu đồng + tước GPLX 1-3 tháng

### 5. PHẠT KHÔNG CÓ GIẤY PHÉP LÁI (Điều 21, Nghị định 100):
**Ô tô:**
- Không mang theo: 100-200 nghìn đồng
- GPLX hết hạn dưới 3 tháng: 1-2 triệu đồng
- GPLX hết hạn trên 3 tháng: 3-5 triệu đồng
- Không có GPLX: 5-7 triệu đồng

**Xe máy:**
- Không mang theo: 100-200 nghìn đồng
- Không có GPLX: 1-2 triệu đồng

### 6. PHẠT SAI LÀN ĐƯỜNG:
**Ô tô:** 3-5 triệu đồng + tước GPLX 1-3 tháng
**Xe máy:** 400-600 nghìn đồng

### 7. PHẠT ĐỖ XE SAI QUY ĐỊNH:
**Ô tô:**
- Đỗ xe không đúng nơi quy định: 200-300 nghìn đồng
- Đỗ xe trên vỉa hè: 800 nghìn - 1 triệu đồng
- Đỗ xe chắn lối ra vào: 4-6 triệu đồng

**Xe máy:**
- Đỗ xe không đúng nơi quy định: 100-200 nghìn đồng
- Đỗ xe trên vỉa hè: 200-300 nghìn đồng

### 8. HÌNH PHẠT BỔ SUNG:
- Tạm giữ phương tiện: 7-10 ngày
- Tước quyền sử dụng GPLX: 1-24 tháng
- Trục xuất người nước ngoài vi phạm
"""

        system_prompt = f"""
Bạn là **Luật Sư Giao Thông AI** với 20 năm kinh nghiệm, chuyên tư vấn luật giao thông Việt Nam.

**DỮ LIỆU LUẬT CẬP NHẬT 2026:**
{law_database}

**NHIỆM VỤ CỦA BẠN:**
1. Trả lời chính xác dựa trên dữ liệu luật được cung cấp
2. Trích dẫn điều luật, nghị định cụ thể
3. Phân biệt rõ các loại phương tiện
4. Đề cập đến hình phạt chính và hình phạt bổ sung
5. Sử dụng emoji phù hợp
6. Trình bày có cấu trúc, dễ đọc
"""

        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=1000,
            top_p=1.0,
            stream=False
        )

        response = chat_completion.choices[0].message.content
        print(f"🤖 [GROQ LAW] Response: {response[:100]}...")
        return response

    except ImportError:
        print("⚠️ Chưa cài groq. Chạy: pip install groq")
        return generate_law_response_fallback(question)
    except Exception as e:
        print(f"❌ Lỗi Groq API: {e}")
        return generate_law_response_fallback(question)


def generate_law_response_fallback(question):
    """Fallback khi không có Groq API"""
    q = question.lower()

    if 'đèn xanh' in q:
        return """**✅ ĐÈN XANH KHÔNG BỊ PHẠT!**

🚦 **Đèn xanh** là tín hiệu được phép đi, không vi phạm.

⚠️ **Lưu ý:**
• Vẫn phải giảm tốc độ khi qua giao lộ
• Quan sát và nhường đường cho người đi bộ
• Không được vượt xe khác trong giao lộ"""

    if 'đèn vàng' in q:
        return """**🚦 QUY ĐỊNH VỀ ĐÈN VÀNG**

✅ **Được đi tiếp nếu:**
• Đã đi quá vạch dừng khi đèn chuyển vàng

❌ **Bị phạt nếu:**
• Cố tình tăng tốc để vượt khi đèn vừa chuyển vàng
• Chưa qua vạch dừng mà không dừng lại

**Mức phạt vượt đèn vàng:**
🚗 Ô tô: 4-6 triệu đồng
🏍️ Xe máy: 800 nghìn - 1 triệu đồng
⚠️ Tước GPLX 1-3 tháng"""

    if any(x in q for x in ['tốc độ', 'chạy nhanh', 'vượt tốc']):
        return """**📊 MỨC PHẠT QUÁ TỐC ĐỘ 2026**

🚗 **Ô tô:**
• Quá 5-10 km/h: 800.000đ
• Quá 10-20 km/h: 3-5 triệu đồng
• Quá 20-35 km/h: 6-8 triệu đồng
• Quá trên 35 km/h: 10-12 triệu đồng + treo bằng 2-4 tháng

🏍️ **Xe máy:**
• Quá 5-10 km/h: 400-600 nghìn đồng
• Quá 10-20 km/h: 800 nghìn - 1 triệu đồng
• Quá 20-35 km/h: 4-5 triệu đồng
• Quá trên 35 km/h: 6-8 triệu đồng"""

    if any(x in q for x in ['nồng độ cồn', 'rượu', 'bia']):
        return """**🍺 MỨC PHẠT NỒNG ĐỘ CỒN 2026**

🚗 **Ô tô:**
• Mức 1: 6-8 triệu đồng
• Mức 2: 16-18 triệu đồng
• Mức 3: 30-40 triệu đồng

🏍️ **Xe máy:**
• Mức 1: 2-3 triệu đồng
• Mức 2: 4-5 triệu đồng
• Mức 3: 6-8 triệu đồng

⚠️ Tước GPLX 10-24 tháng, tạm giữ xe 7 ngày"""

    if any(x in q for x in ['mũ bảo hiểm', 'nón bảo hiểm']):
        return """**⛑️ PHẠT KHÔNG ĐỘI MŨ BẢO HIỂM**

👤 Người điều khiển: 400-600 nghìn đồng
👥 Người ngồi sau: 400-600 nghìn đồng

✅ Miễn trừ: Trẻ em dưới 6 tuổi, người bị bệnh"""

    if 'đèn đỏ' in q or ('vượt' in q and 'đèn' in q):
        return """**🚦 PHẠT VƯỢT ĐÈN ĐỎ**

🚗 Ô tô: 4-6 triệu đồng
🏍️ Xe máy: 800 nghìn - 1 triệu đồng

⚠️ Tước GPLX 1-3 tháng

💡 **Lưu ý:** Đèn đỏ phải dừng trước vạch sơn."""

    if any(x in q for x in ['giấy phép lái xe', 'bằng lái', 'không có bằng']):
        return """**📄 PHẠT KHÔNG CÓ GIẤY PHÉP LÁI**

🚗 **Ô tô:**
• Không mang theo: 100-200 nghìn đồng
• Hết hạn: 1-5 triệu đồng
• Không có GPLX: 5-7 triệu đồng

🏍️ **Xe máy:**
• Không mang theo: 100-200 nghìn đồng
• Không có GPLX: 1-2 triệu đồng"""

    if any(x in q for x in ['đăng ký xe', 'làm biển số', 'sang tên']):
        return """**📝 THỦ TỤC ĐĂNG KÝ XE MÁY**

**Hồ sơ gồm:**
1. CCCD/CMND + photo
2. Hóa đơn mua xe (bản gốc)
3. Giấy khai đăng ký xe

**Lệ phí:**
• Hà Nội/TP.HCM: 500.000đ
• Các tỉnh: 80.000đ

⏱️ Thời gian: 2-3 ngày làm việc"""

    return """Cảm ơn bạn đã đặt câu hỏi!

🤖 Tôi là trợ lý tư vấn luật giao thông.

**Tôi có thể giúp bạn:**
• Tra cứu mức phạt vi phạm
• Giải đáp tình huống giao thông
• Hướng dẫn thủ tục hành chính"""
