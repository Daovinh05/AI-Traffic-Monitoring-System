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

# ======================= Biến ghi hình ===========================
video_writer = None
is_recording = False
recording_start_time = None
fps = 20.0
frame_width = 640
frame_height = 480

# Tạo thư mục recordings nếu chưa tồn tại
if not os.path.exists('recordings'):
    os.makedirs('recordings')

# Dlib & YOLO models
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("py/shape_predictor_68_face_landmarks.dat")
phone_mau = YOLO("yolov8n.pt")
seatbelt_mau = YOLO("py/weights/lasttx.pt")
bienbao_model = YOLO("py/weights/best2.pt")

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
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                
                
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
    "hand": ""
}

# ======================= Video giám sát tài xế ===========================
def driver_monitor():
    global latest_warning, warnings, video_writer, is_recording
    # Mặc định cam lap
    cap = cv2.VideoCapture(0)
    eye_closed_time = None
    counter_yawn = 0
    alarm_yawn_on = False
    seatbelt_alert_playing = False

    while True:
        success, frame = cap.read()
        if not success:
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

            # Ngủ gật
            left_eye = [points[i] for i in left_eye_indexes]
            right_eye = [points[i] for i in right_eye_indexes]
            ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0
            if ear < EAR_THRESHOLD:
                if eye_closed_time is None:
                    eye_closed_time = time.time()
                elif time.time() - eye_closed_time > EAR_MIN_DURATION:
                    chopmat_sound.play()
                    warnings["eye"] = "NHẮM MẮT QUÁ LÂU!"
            else:
                eye_closed_time = None

            # Ngáp
            yawn_ratio = detect_yawn(points)
            if yawn_ratio > YAWN_THRESHOLD:
                counter_yawn += 1
                if counter_yawn >= YAWN_CONSEC_FRAMES:
                    if not alarm_yawn_on:
                        alarm_yawn_on = True
                        ngap_sound.play()
                    warnings["yawn"] = "NGÁP NGỦ!"
            else:
                counter_yawn = 0
                alarm_yawn_on = False

            # Đầu quay
            pitch, yaw, roll = get_head_pose(points, frame.shape)
            if abs(yaw) > 35 or pitch > 25:
                warnings["head"] = "ĐẦU XOAY NHIỀU!"

        # Phát hiện dùng điện thoại
        results = phone_mau(frame)
        for result in results:
            for box in result.boxes.data:
                x1, y1, x2, y2, conf, cls = box
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                label = phone_mau.names[int(cls)]
                if "phone" in label.lower() and conf > 0.5:
                    phone_baodong.play()
                    warnings["phone"] = "DÙNG ĐIỆN THOẠI!"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Phát hiện dây an toàn
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
            if not seatbelt_alert_playing:
                seatbelt_baodong.play()
                seatbelt_alert_playing = True
            warnings["seatbelt"] = "KHÔNG ĐEO DÂY AN TOÀN!"
        else:
            seatbelt_alert_playing = False

        # Giám sát tay lái
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
    cap.release()

# ======================= Video cảnh báo biển báo ===========================
def traffic_sign_monitor():
    global warnings, video_writer, is_recording
    last_sign_time = None  # Thêm biến để theo dõi thời gian phát âm thanh cuối cùng

    #đàu vào dữ liệu biển cảnh báo
    cap = cv2.VideoCapture("bien_bao.mp4")

    while True:
        ret, frame = cap.read()
        if not ret:
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
                cv2.putText(annotated, f'{label}: {conf:.2f}', (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Reset warnings
        warnings["speed"] = ""
        warnings["sign"] = ""

        # Cập nhật cảnh báo
        current_time = time.time()
        if boxes is not None:
            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i])
                label = bienbao_model.names[cls_id]
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
    cap.release()

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
    def __init__(self, model_path="yolov8n.pt", regions=None, classes=None):
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
        
        if total_vehicles < 5:
            self.stats['traffic_status'] = {
                'level': 'normal',
                'message': 'Giao thông thông thoáng, di chuyển bình thường',
                'color': 'green'
            }
        elif total_vehicles >= 5 and total_vehicles < 10:
            self.stats['traffic_status'] = {
                'level': 'warning',
                'message': 'Giao thông hơi đông, tốc độ chậm hơn bình thường một chút',
                'color': 'yellow'
            }
        elif total_vehicles >= 10 and total_vehicles < 15:
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

    def get_stats(self):
        return self.stats

counter = None
video_capture = None
current_region_type = 'single'  # Default to single region

def traffic_monitor():
    global counter, video_capture
    while True:
        success, frame = video_capture.read()
        if not success:
            video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue
            
        if counter:
            try:
                processed_frame = counter.process(frame)
                ret, buffer = cv2.imencode('.jpg', processed_frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                print(f"Error processing frame: {e}")
                continue

def reset_temporary_counts():
    global counter
    while True:
        time.sleep(10)
        if counter:
            with counter.lock:
                print("Thống kê trong 10 giây qua:", counter.temp_vehicle_type_counts)
                counter.temp_vehicle_type_counts = {'car': 0, 'motorcycle': 0, 'bus': 0, 'truck': 0}

def get_region_points(region_type):
    if region_type == 'single':  # Hà Nội
        return {
            'regions': [
                np.array([[400, -9], [-47, 330], [-40, 648], [1136, 620], [1102, 372], [801, 19]])
            ],
            'video_source': "ha_noi.mp4"
        }
    elif region_type == 'multiple':  # Hà Đông
        return {
            'regions': [
                np.array([[767, 505], [1302, 660], [17, 661], [600, 507]]),
                np.array([[598, 589], [788, 586]])
            ],
            'video_source': "ha_dong.mp4"
        }
    elif region_type == 'multiple1':  # Thanh Xuân
        return {
            'regions': [
                np.array([[1003, 68], [1456, 592], [1444, 852], [969, 854], [833, 70]]),
                np.array([[829, 62], [967, 853], [503, 843], [707, 68], [829, 69]]),
                np.array([[492, 850], [98, 845], [584, 47], [700, 66]]),
                np.array([[584, 47], [446, 23], [-87, 466], [-87, 839], [96, 846], [579, 52]])
            ],
            'video_source': "thanh_xuan.mp4"
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
    counter = MultipleObjectCounter(model_path="yolov8n.pt", regions=region_points, classes=object_classes)

@app.route('/change_region_points', methods=['POST'])
def change_region_points():
    global counter, current_region_type, video_capture
    try:
        data = request.get_json()
        region_type = data.get('type')
        
        if region_type in ['single', 'multiple', 'multiple1']:
            current_region_type = region_type
            # Get new region points and video source
            region_data = get_region_points(region_type)
            region_points = region_data['regions']
            video_source = region_data['video_source']
            
            # Release current video capture
            if video_capture is not None:
                video_capture.release()
            
            # Initialize new video capture with optimized settings
            video_capture = cv2.VideoCapture(video_source)
            if not video_capture.isOpened():
                return jsonify({"status": "error", "message": f"Không thể mở video: {video_source}"})
            
            # Set video capture properties for better performance
            video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Reduce buffer size
            video_capture.set(cv2.CAP_PROP_FPS, 30)  # Set FPS
            
            # Reinitialize counter with new region points
            object_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck
            counter = MultipleObjectCounter(model_path="yolov8n.pt", regions=region_points, classes=object_classes)
            
            # Give the video capture a moment to initialize
            time.sleep(0.1)
            
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "message": "Invalid region type"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ======================= Flask Routes ===========================
@app.route('/')
def index():
    return render_template('app_tong.html')

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

@app.route('/get_warnings')
def get_warnings():
    return jsonify(warnings)

@app.route('/get_stats')
def get_stats():
    global counter
    return jsonify(counter.get_stats())

@app.route('/set_mode', methods=['POST'])
def set_mode():
    global current_mode
    data = request.get_json()
    current_mode = data.get('mode', 'driver')
    return jsonify({"status": "success"})

@app.route('/start_recording')
def start_recording():
    global video_writer, is_recording, recording_start_time
    
    if not is_recording:
        # Tạo tên file dựa trên thời gian
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'recordings/recording_{timestamp}.mp4'
        
        # Khởi tạo video writer
        video_writer = cv2.VideoWriter(
            filename,
            cv2.VideoWriter_fourcc(*'mp4v'),
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

if __name__ == '__main__':
    init_app()
    threading.Thread(target=reset_temporary_counts, daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=5000) 
    

    