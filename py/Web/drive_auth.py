from flask import Flask, render_template, Response, jsonify, request, send_file, make_response, session, redirect, url_for, flash
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_session import Session
from functools import wraps
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
import os
from shapely.geometry import Point, Polygon
import mediapipe as mp

# ========================================
# AUTHENTICATION CONFIG
# ========================================
app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Session config
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# MySQL config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'ai_traffic_monitoring'

# Extensions
bcrypt = Bcrypt(app)
Session(app)

# ========================================
# DECORATORS
# ========================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Vui lòng đăng nhập'}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        if session.get('role') != 'admin':
            flash('Bạn không có quyền truy cập', 'error')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# ========================================
# DATABASE
# ========================================
def get_db_connection():
    try:
        return pymysql.connect(
            host=app.config['MYSQL_HOST'],
            port=app.config['MYSQL_PORT'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            cursorclass=pymysql.cursors.DictCursor,
            charset='utf8mb4'
        )
    except Exception as e:
        print(f"DB Error: {e}")
        return None

# ========================================
# AUTH ROUTES
# ========================================
@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('index_page'))
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Vui lòng nhập đầy đủ'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
            
        cur = conn.cursor()
        cur.execute('SELECT id, username, password, role, full_name, is_active FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user:
            return jsonify({'success': False, 'message': 'Tên đăng nhập không tồn tại'}), 401
        
        if not user['is_active']:
            return jsonify({'success': False, 'message': 'Tài khoản đã bị khóa'}), 403
        
        if not bcrypt.check_password_hash(user['password'], password):
            return jsonify({'success': False, 'message': 'Mật khẩu không đúng'}), 401
        
        # Create session
        session.permanent = True
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['full_name'] = user['full_name']
        
        redirect_url = '/dashboard' if user['role'] == 'admin' else '/trang_chu'
        
        return jsonify({
            'success': True,
            'message': 'Đăng nhập thành công',
            'redirect': redirect_url,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'role': user['role']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Đăng xuất thành công', 'redirect': '/login'}), 200

@app.route('/api/check-auth')
def check_auth():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session.get('user_id'),
                'username': session.get('username'),
                'role': session.get('role')
            },
            'redirect': '/dashboard' if session.get('role') == 'admin' else '/trang_chu'
        }), 200
    return jsonify({'authenticated': False, 'user': None, 'redirect': None}), 200

@app.route('/')
def index_page():
    """Trang chủ - luôn redirect về login nếu chưa đăng nhập"""
    if 'user_id' in session:
        # Đã đăng nhập thì redirect theo role
        if session.get('role') == 'admin':
            return redirect(url_for('dashboard_page'))
        else:
            return redirect(url_for('trang_chu_page'))
    else:
        # Chưa đăng nhập thì về login
        return redirect(url_for('login_page'))

@app.route('/dashboard')
@login_required
@admin_required
def dashboard_page():
    return render_template('Dashboard.html', user=session.get('user'))

@app.route('/trang_chu')
@login_required
def trang_chu_page():
    return render_template('trang_chu.html', user=session.get('user'))

@app.route('/tu_van')
@login_required
def tu_van_page():
    return render_template('tu_van.html', user=session.get('user'))

@app.route('/lai_xe')
@login_required
def lai_xe_page():
    return render_template('lai_xe.html', user=session.get('user'))

@app.route('/lich_su')
@login_required
def lich_su_page():
    return render_template('lich_su.html', user=session.get('user'))

# ========================================
# API ENDPOINTS FOR HISTORY PAGE
# ========================================
@app.route('/api/alerts')
@login_required
def get_alerts():
    """Lấy danh sách cảnh báo AI (vi phạm)"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cur = conn.cursor()
        cur.execute('''
            SELECT a.*, v.plate_number as vehicle_plate, d.full_name as driver_name
            FROM alerts a
            LEFT JOIN vehicles v ON a.vehicle_id = v.id
            LEFT JOIN drivers d ON a.driver_id = d.id
            ORDER BY a.timestamp DESC
            LIMIT 100
        ''')
        alerts = cur.fetchall()
        cur.close()
        conn.close()
        
        # Format alerts
        formatted_alerts = []
        for alert in alerts:
            formatted_alerts.append({
                'id': alert['id'],
                'type': alert['type'],
                'message': alert['message'],
                'level': alert['level'],
                'timestamp': alert['timestamp'].isoformat() if alert['timestamp'] else None,
                'vehicle_plate': alert['vehicle_plate'],
                'driver_name': alert['driver_name'],
                'is_read': bool(alert['is_read']),
                'video_path': alert['video_path']
            })
        
        return jsonify({'success': True, 'alerts': formatted_alerts})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/alerts/<int:alert_id>/read', methods=['POST'])
@login_required
def mark_alert_as_read(alert_id):
    """Đánh dấu cảnh báo đã đọc"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cur = conn.cursor()
        cur.execute('UPDATE alerts SET is_read = 1 WHERE id = %s', (alert_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Đã đánh dấu đã đọc'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/videos')
@login_required
def get_videos():
    """Lấy danh sách video vi phạm"""
    try:
        # Lấy danh sách file video từ thư mục recordings
        import os
        video_dir = 'recordings'
        videos = []
        
        if os.path.exists(video_dir):
            for filename in os.listdir(video_dir):
                if filename.endswith('.mp4'):
                    filepath = os.path.join(video_dir, filename)
                    # Lấy thông tin file
                    stat = os.stat(filepath)
                    videos.append({
                        'id': filename,
                        'title': filename.replace('.mp4', '').replace('_', ' ').title(),
                        'path': f'/{filepath}',
                        'thumbnail': f'/static/video-thumbnail.png',
                        'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'duration': 'N/A',
                        'size': stat.st_size
                    })
        
        # Sort by timestamp descending
        videos.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({'success': True, 'videos': videos[:50]})  # Giới hạn 50 video
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/admin-warnings')
@login_required
def get_admin_warnings():
    """Lấy danh sách cảnh báo từ admin"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cur = conn.cursor()
        cur.execute('''
            SELECT w.*, u.full_name as admin_name
            FROM warnings w
            LEFT JOIN users u ON w.admin_id = u.id
            ORDER BY w.created_at DESC
            LIMIT 100
        ''')
        warnings = cur.fetchall()
        cur.close()
        conn.close()
        
        # Format warnings
        formatted_warnings = []
        for warning in warnings:
            formatted_warnings.append({
                'id': warning['id'],
                'vehicle_plate': warning['vehicle_plate'],
                'message': warning['message'],
                'priority': warning['priority'],
                'is_read': bool(warning['is_read']),
                'created_at': warning['created_at'].isoformat() if warning['created_at'] else None,
                'admin_name': warning['admin_name']
            })
        
        return jsonify({'success': True, 'warnings': formatted_warnings})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/admin-warnings/<int:warning_id>/read', methods=['POST'])
@login_required
def mark_warning_as_read(warning_id):
    """Đánh dấu cảnh báo admin đã đọc"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        
        cur = conn.cursor()
        cur.execute('UPDATE warnings SET is_read = 1, read_at = NOW() WHERE id = %s', (warning_id,))
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Đã đánh dấu đã đọc'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

# ========================================
# END AUTHENTICATION CODE
# BEGIN ORIGINAL DRIVE.PY CODE
# ========================================

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
ngap_sound = pygame.mixer.Sound("py/Sound/ngap_ngu.wav")
phone_baodong = pygame.mixer.Sound("py/Sound/not_phone.wav")
seatbelt_baodong = pygame.mixer.Sound("py/Sound/seatbelt_alert.wav")
dau_quay_sound = pygame.mixer.Sound("py/Sound/chuylaixe.wav")
bienbao_sound = pygame.mixer.Sound("py/Sound/chu_y_bien_bao.wav")
tay_lai_sound = pygame.mixer.Sound("py/Sound/tay_lai_xe.wav")
lech_lan_sounds = pygame.mixer.Sound("py/Sound/lech_lan.wav")
va_cham_sound = pygame.mixer.Sound("py/Sound/va_cham.wav")
di_cham_lai_sound = pygame.mixer.Sound("py/Sound/di_cham_lai.wav")

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
seatbelt_mau = YOLO("py/weights/day_an_toan.pt")
bienbao_model = YOLO("py/weights/bien_bao.pt")
model_vehicle = YOLO("py/weights/yolov8n.pt")   # Phát hiện phương tiện
model_lane = YOLO("py/weights/lech_lan.pt")
       # Mô hình YOLO đã huấn luyện lại vạch kẻ đường
model_hole = YOLO("py/weights/vat_can.pt")  # Mô hình phát hiện ổ gà/vật cản

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
    
    # Chuẩn hóa góc về khoảng -90 đến 90 độ
    pitch = eulerAngles[0]
    yaw = eulerAngles[1]
    roll = eulerAngles[2]
    
    # Chuyển đổi góc từ độ Euler sang khoảng -90 đến 90
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
                # cv2.putText(img, "WARNING: Khong cam vo lang xe !", (10, 30),
                #             cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,0), 2)
                
                
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

                
                # Vẽ toàn bộ 68 điểm landmark trên khuôn mặt (màu trắng)
                # 1. Đường viền hàm (0-16)
                for i in range(0, 17):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(0, 16):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)

                # 2. Lông mày trái (17-21)
                for i in range(17, 22):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(17, 21):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)

                # 3. Lông mày phải (22-26)
                for i in range(22, 27):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(22, 26):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)

                # 4. Sống mũi (27-35)
                for i in range(27, 36):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(27, 35):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)

                # 5. Mắt trái (36-41)
                for i in range(36, 42):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(36, 41):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)
                cv2.line(frame, points[41], points[36], (255, 255, 255), 1)

                # 6. Mắt phải (42-47)
                for i in range(42, 48):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(42, 47):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)
                cv2.line(frame, points[47], points[42], (255, 255, 255), 1)

                # 7. Miệngoài (48-59)
                for i in range(48, 60):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(48, 59):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)
                cv2.line(frame, points[59], points[48], (255, 255, 255), 1)

                # 8. Miệng trong (60-67)
                for i in range(60, 68):
                    x, y = points[i]
                    cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)
                for i in range(60, 67):
                    cv2.line(frame, points[i], points[i + 1], (255, 255, 255), 1)
                cv2.line(frame, points[67], points[60], (255, 255, 255), 1)

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

                # Đầu quay - chỉ kiểm tra nếu cảnh báo đầu được bật
                if warning_states["head"]:
                    pitch, yaw, roll = get_head_pose(points, frame.shape)
                    # Cảnh báo nếu quay trái/phải (yaw) lớn hơn 35 độ hoặc cúi xuống (pitch) lớn hơn 25 độ
                    if abs(yaw) > 40 or pitch > 35:
                        if can_play_warning("head"):
                            dau_quay_sound.play()
                        warnings["head"] = "MẤT TẬP TRUNG !"
                        if previous_warnings["head"] != "MẤT TẬP TRUNG !":
                            add_ai_alert("head", "Tài xế mất tập trung (quay đầu/ngửa đầu)!", current_monitoring_vehicle_id)
                    
                    # Hiển thị thông số pitch, yaw và roll ở góc camera (màu vàng)
                    cv2.rectangle(frame, (10, 10), (200, 75), (0, 0, 0), cv2.FILLED)
                    cv2.putText(frame, f"Pitch: {pitch:.1f}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    cv2.putText(frame, f"Yaw: {yaw:.1f}", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    cv2.putText(frame, f"Roll: {roll:.1f}", (10, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            

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

def process_collision_warning(frame, distance, current_time, object_type='vehicle'):
    """
    Xử lý cảnh báo va chạm (deprecated - dùng logic mới trực tiếp trong loop)
    object_type: 'person' hoặc 'vehicle'
    """
    global last_collision_warning, warnings, collision_alert_sent

    # Xác định ngưỡng dựa trên loại đối tượng
    if object_type == 'person':
        critical_distance = 12
        warning_distance = 20
        alert_message = "🚨 PHÁT HIỆN NGƯỜI TRƯỚC ĐẦU XE!"
    else:
        critical_distance = 8
        warning_distance = 15
        alert_message = "🚨 CẢNH BÁO VA CHẠM SẮP XẢY RA!"

    if distance < critical_distance:
        warnings["collision"] = "CẢNH BÁO VA CHẠM!"
        if current_time - last_collision_warning >= warning_interval:
            va_cham_sound.play()
            last_collision_warning = current_time
    elif distance < warning_distance:
        warnings["collision"] = "GIỮ KHOẢNG CÁCH!"
    else:
        warnings["collision"] = ""
        collision_alert_sent = False  # Reset khi không còn nguy hiểm

def process_lane_warning(frame, left_found, right_found):
    global warnings, lane_alert_sent

    # Kiểm tra nếu cảnh báo lệch làn bị tắt
    if not warning_states.get("lane", True):
        warnings["lane"] = ""
        return

    if not (left_found and right_found):
        warnings["lane"] = "CẢNH BÁO LỆCH LÀN!"
        if not pygame.mixer.get_busy():
            lech_lan_sounds.play()
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
        # Sử dụng video hole.mp4 để phát hiện vật cản/ổ gà
        cap = cv2.VideoCapture("py/video_input/lech_lan.mp4")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 20)

        last_obstacle_warning = 0
        obstacle_warning_interval = 2.0  # Khoảng thời gian giữa các cảnh báo vật cản

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
            warnings["obstacle"] = ""

            # Kiểm tra xem có cần nhận diện không (chỉ nhận diện khi ít nhất 1 cảnh báo được bật)
            need_collision_detection = warning_states.get("collision", True)
            need_lane_detection = warning_states.get("lane", True)
            need_obstacle_detection = warning_states.get("obstacle", True)
            
            # Nếu tất cả cảnh báo đều tắt, bỏ qua nhận diện để tiết kiệm tài nguyên
            if not (need_collision_detection or need_lane_detection or need_obstacle_detection):
                # Vẫn vẽ frame bình thường nhưng không nhận diện gì
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                continue

            # Phát hiện vật cản/ổ gà bằng model_hole (best_hole.pt) - Chỉ khi được bật
            if need_obstacle_detection:
                results_hole = model_hole(frame, verbose=False)
                obstacle_detected = False
                obstacle_count = 0
                max_conf = 0.0

                for result in results_hole:
                    # Xử lý masks (segmentation)
                    if result.masks is not None:
                        # Lấy thông tin boxes và confidence
                        if result.boxes is not None:
                            for i, box in enumerate(result.boxes):
                                conf = float(box.conf[0])
                                if conf > 0.3:  # Chỉ xét khi confidence > 30%
                                    obstacle_detected = True
                                    obstacle_count += 1
                                    if conf > max_conf:
                                        max_conf = conf

                                    # Vẽ bounding box và mask với label tùy chỉnh
                                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                                    # Vẽ mask
                                    frame = result.plot(labels=False, conf=False, line_width=2)
                                    # Vẽ bounding box màu đỏ
                                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                                    label = f"Chuong ngai vat {conf:.2f}"
                                    cv2.putText(frame, label, (x1, y1 - 10),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        else:
                            # Nếu chỉ có masks mà không có boxes
                            obstacle_detected = True
                            obstacle_count += len(result.masks)
                            frame = result.plot(labels=False, conf=False, line_width=2)

                    # Xử lý boxes riêng (nếu không có masks)
                    elif result.boxes is not None:
                        for box in result.boxes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            conf = float(box.conf[0])
                            cls = int(box.cls[0])

                            if conf > 0.3:  # Chỉ xét khi confidence > 30%
                                obstacle_detected = True
                                obstacle_count += 1
                                if conf > max_conf:
                                    max_conf = conf

                                # Vẽ bounding box màu đỏ nổi bật
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                                label = f"Chuong ngai vat {conf:.2f}"
                                cv2.putText(frame, label, (x1, y1 - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

                # Nếu phát hiện vật cản/ổ gà với confidence cao, cảnh báo
                if obstacle_detected and max_conf > 0.3:
                    warnings["obstacle"] = f"VẬT CẢN PHÍA TRƯỚC! ({obstacle_count})"
                    if current_time - last_obstacle_warning >= obstacle_warning_interval:
                        di_cham_lai_sound.play()
                        last_obstacle_warning = current_time
                else:
                    warnings["obstacle"] = ""
            else:
                # Không nhận diện vật cản
                obstacle_detected = False

            # Phát hiện phương tiện - Chỉ khi cảnh báo va chạm được bật
            if need_collision_detection:
                results_v = model_vehicle(frame)[0]
                for box in results_v.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = model_vehicle.names[cls]

                if label in ['car', 'truck', 'bus', 'motorbike', 'person']:
                    distance = estimate_distance(y1, y2)
                    
                    # Xác định ngưỡng khoảng cách dựa trên đối tượng
                    if label == 'person':
                        # Người: ngưỡng an toàn cao hơn (nguy hiểm hơn)
                        critical_distance = 12  # Dưới 12m là nguy hiểm
                        warning_distance = 20   # Dưới 20m là cảnh báo
                        alert_message = "🚨 PHÁT HIỆN NGƯỜI TRƯỚC ĐẦU XE!"
                    else:
                        # Phương tiện/chướng ngại vật
                        critical_distance = 8
                        warning_distance = 15
                        alert_message = "🚨 CẢNH BÁO VA CHẠM SẮP XẢY RA!"
                    
                    # Xử lý cảnh báo va chạm
                    if distance < critical_distance:
                        warnings["collision"] = "CẢNH BÁO VA CHẠM!"
                        if current_time - last_collision_warning >= warning_interval:
                            va_cham_sound.play()
                            last_collision_warning = current_time
                        color = (0, 0, 255)  # Đỏ
                    elif distance < warning_distance:
                        warnings["collision"] = "GIỮ KHOẢNG CÁCH!"
                        color = (0, 255, 255)  # Vàng
                        collision_alert_sent = False
                    else:
                        warnings["collision"] = ""
                        color = (0, 255, 0)  # Xanh lá
                        collision_alert_sent = False

                    # Vẽ bounding box, nhãn và khoảng cách
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    
                    # Thêm nhãn đối tượng và khoảng cách
                    label_text = f'{label} {conf:.2f} | {distance:.1f}m'
                    if label == 'person':
                        label_text = f'NGUOI {conf:.2f} | {distance:.1f}m'
                    
                    cv2.putText(frame, label_text, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    
                    # Vẽ thêm indicator đặc biệt cho người
                    if label == 'person' and distance < warning_distance:
                        # Vẽ vòng tròn đỏ quanh người
                        cv2.circle(frame, ((x1 + x2) // 2, (y1 + y2) // 2), 10, (0, 0, 255), -1)

            # Nhận diện làn bằng YOLO - Chỉ khi cảnh báo lệch làn được bật
            if need_lane_detection:
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

# Lưu vị trí hiện tại để hỗ trợ frontend
current_location_id = "hanoi"
location_video_map = {
    "hanoi": "single",
    "hadong": "multiple",
    "thanhxuan": "thanhxuan",
    "ngatuso": "ngatuso"
}

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
@login_required
def change_region_points():
    global counter, current_region_type, video_capture, active_video_stream, current_location_id
    try:
        data = request.get_json()
        region_type = data.get('type')
        location_id = data.get('location')  # Thêm location_id từ frontend

        # Hỗ trợ cả region_type cũ và location_id mới
        if location_id and location_id in location_video_map:
            region_type = location_video_map[location_id]
            current_location_id = location_id
        elif region_type in ['single', 'multiple', 'thanhxuan', 'ngatuso']:
            current_location_id = [k for k, v in location_video_map.items() if v == region_type][0]

        if region_type in ['single', 'multiple', 'thanhxuan', 'ngatuso']:
            print(f"Changing to region type: {region_type} (location: {current_location_id})")

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
@login_required
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

@app.route('/traffic_bus')
def traffic_bus():
    """Serve Dashboard.html với đầy đủ dữ liệu từ drive.py"""
    return render_template('Dashboard.html')

@app.route('/tu_van.html')
@login_required
def tu_van_html():
    """Serve tu_van.html - Trang tư vấn luật giao thông"""
    return render_template('tu_van.html', user=session.get('user'))

@app.route('/lai_xe_v2')
@login_required
def lai_xe_v2_page():
    response = make_response(render_template('lai_xe.html', user=session.get('user')))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

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
    global current_location_id
    # Lấy tham số location từ frontend
    location_id = request.args.get('location', None)
    
    # Nếu có location_id và khác với hiện tại, cập nhật
    if location_id and location_id in location_video_map:
        current_location_id = location_id
        region_type = location_video_map[location_id]
        
        # Cập nhật region type và video source
        global current_region_type, video_capture, active_video_stream
        if region_type != current_region_type:
            active_video_stream = None
            time.sleep(0.5)
            
            if video_capture is not None:
                video_capture.release()
            
            current_region_type = region_type
            region_data = get_region_points(region_type)
            video_source = region_data['video_source']
            
            video_capture = cv2.VideoCapture(video_source)
            if not video_capture.isOpened():
                print(f"Failed to open video for location {location_id}")
            
            # Reinitialize counter
            object_classes = [2, 3, 5, 7]
            counter = MultipleObjectCounter(model_path="py/weights/yolov8n.pt", 
                                           regions=region_data['regions'], 
                                           classes=object_classes)
            
            active_video_stream = 'traffic'
            print(f"Switched to location: {location_id} ({region_type})")
    
    return Response(traffic_monitor(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_vacham')
def video_vacham():
    return Response(collision_monitor(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/py/video_input/<path:filename>')
def serve_video(filename):
    """Serve video files cho cam hành trình"""
    # Video nam o thu muc py/video_input/, khong phai py/Web/video_input/
    video_path = os.path.join(os.path.dirname(__file__), '..', 'video_input', filename)
    if os.path.exists(video_path):
        return send_file(video_path)
    return "Video not found", 404

@app.route('/get_warnings')
@login_required
def get_warnings():
    # Thêm thông tin hình ảnh biển báo vào warnings
    warnings_with_image = warnings.copy()
    warnings_with_image['sign_image'] = latest_sign_image_path
    warnings_with_image['sign_label'] = latest_sign_label
    return jsonify(warnings_with_image)

@app.route('/get_latest_sign_image')
@login_required
def get_latest_sign_image():
    """Trả về hình ảnh biển báo mới nhất"""
    global latest_sign_image_path
    if latest_sign_image_path and os.path.exists(latest_sign_image_path):
        return send_file(latest_sign_image_path, mimetype='image/jpeg')
    # Trả về ảnh placeholder nếu không có ảnh
    return "", 404

@app.route('/get_stats')
@login_required
def get_stats():
    global counter
    return jsonify(counter.get_stats())

@app.route('/set_mode', methods=['POST'])
@login_required
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
@login_required
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
@login_required
def stop_recording():
    global is_recording, video_writer
    
    if is_recording and video_writer is not None:
        video_writer.release()
        video_writer = None
        is_recording = False
        return "Recording stopped"
    return "Not recording"

@app.route('/get_video_source/<region_type>')
@login_required
def get_video_source(region_type):
    try:
        region_data = get_region_points(region_type)
        return jsonify({"video_source": region_data['video_source']})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


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
    """API gửi tin nhắn vào chatbot với AI xử lý"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        vehicle_id = data.get('vehicle_id')
        user_id = data.get('user_id', 'anonymous')

        # Lưu tin nhắn vào database (nếu có)
        print(f"[CHAT] User {user_id} (xe {vehicle_id}): {message}")

        # AI xử lý và tạo phản hồi
        bot_response = process_ai_chat_message(message, vehicle_id)

        return jsonify({
            'status': 'success',
            'bot_response': bot_response
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/groq_law_chat', methods=['POST'])
def api_groq_law_chat():
    """API tư vấn luật giao thông bằng Groq AI"""
    try:
        data = request.get_json()
        message = data.get('message', '')

        print(f"[LAW CHAT] User hỏi: {message}")

        # Gọi Groq API để tư vấn luật
        response = call_groq_law_advisor(message)

        return jsonify({
            'status': 'success',
            'response': response
        })

    except Exception as e:
        print(f"Lỗi api_groq_law_chat: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

def call_groq_law_advisor(question):
    """
    Gọi Groq API để tư vấn luật giao thông
    """
    try:
        from groq import Groq
        import os
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()
        GROQ_API_KEY = os.getenv('GROQ_API_KEY')

        if not GROQ_API_KEY:
            print("⚠️ Không tìm thấy GROQ_API_KEY")
            return generate_law_response_fallback(question)

        client = Groq(api_key=GROQ_API_KEY)

        # === DỮ LIỆU LUẬT GIAO THÔNG VIỆT NAM (CẬP NHẬT 2026) ===
        law_database = """
**NGUỒN LUẬT:**
- Luật Giao thông đường bộ 2008
- Nghị định 100/2019/NĐ-CP (xử phạt vi phạm giao thông)
- Nghị định 123/2021/NĐ-CP (sửa đổi, bổ sung)
- Các văn bản hướng dẫn thi hành

**MỨC PHẠT CHÍNH XÁC 2026:**

### 1. PHẠT QUÁ TỐC ĐỘ:
**Ô tô:**
- Quá 5-10 km/h: 800.000đ (Điểm 100/2019/NĐ-CP)
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
- Mức 1 (chưa vượt quá 50mg/100ml máu hoặc 0.25mg/1lít khí thở): 6-8 triệu đồng + tước GPLX 10-12 tháng
- Mức 2 (vượt quá 50-80mg/100ml máu hoặc 0.25-0.4mg/1lít khí thở): 16-18 triệu đồng + tước GPLX 16-18 tháng
- Mức 3 (vượt quá 80mg/100ml máu hoặc 0.4mg/1lít khí thở): 30-40 triệu đồng + tước GPLX 22-24 tháng

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
- Tạm giữ phương tiện: 7-10 ngày (với một số vi phạm)
- Tước quyền sử dụng GPLX: 1-24 tháng tùy mức độ
- Trục xuất người nước ngoài vi phạm

**LƯU Ý QUAN TRỌNG:**
- Đèn vàng: Phải dừng trước vạch dừng, trừ khi đã đi quá vạch thì được đi tiếp
- Đèn xanh: Được phép đi, không bị phạt
- Người điều khiển xe phải tuân thủ tín hiệu đèn giao thông
- Nồng độ cồn: KHÔNG được lái xe nếu đã uống rượu bia (mức 0 với ô tô từ 2026)
"""

        # System prompt cho AI tư vấn luật
        system_prompt = f"""
Bạn là **Luật Sư Giao Thông AI** với 20 năm kinh nghiệm, chuyên tư vấn luật giao thông Việt Nam.

**DỮ LIỆU LUẬT CẬP NHẬT 2026:**
{law_database}

**NHIỆM VỤ CỦA BẠN:**
1. Trả lời chính xác dựa trên dữ liệu luật được cung cấp ở trên
2. Trích dẫn điều luật, nghị định cụ thể khi có thể
3. Phân biệt rõ các loại phương tiện (ôtô, xe máy, xe đạp, xe tải)
4. Đề cập đến hình phạt chính và hình phạt bổ sung
5. Sử dụng emoji phù hợp để làm rõ nghĩa
6. Trình bày có cấu trúc, dễ đọc
7. Luôn cập nhật theo quy định mới nhất 2026

**PHONG CÁCH TRẢ LỜI:**
- Thân thiện, nhiệt tình, chu đáo
- Giải thích rõ ràng, dễ hiểu
- Đưa ra ví dụ minh họa khi cần
- Cảnh báo nguy hiểm khi vi phạm nghiêm trọng

**CÁC CÂU HỎI THƯỜNG GẶP:**
- "Vượt đèn đỏ phạt bao nhiêu?" → Dựa vào mục 4
- "Nồng độ cồn phạt thế nào?" → Dựa vào mục 2
- "Không đội mũ bảo hiểm?" → Dựa vào mục 3
- "Quá tốc độ phạt sao?" → Dựa vào mục 1
- "Không có bằng lái?" → Dựa vào mục 5
- "Đèn xanh có bị phạt không?" → Trả lời KHÔNG, đèn xanh được đi
- "Đèn vàng được đi không?" → Dựa vào lưu ý quan trọng

**LUÔN NHẮC NGƯỜI DÙNG:**
- Đội mũ bảo hiểm
- Không uống rượu bia khi lái xe
- Tuân thủ tốc độ quy định
- Giữ khoảng cách an toàn
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
    """
    Fallback khi không có Groq API
    """
    q = question.lower()

    # Kiểm tra câu hỏi có hợp lệ không
    if 'đèn xanh' in q:
        return """**✅ ĐÈN XANH KHÔNG BỊ PHẠT!**

🚦 **Đèn xanh** là tín hiệu được phép đi, không vi phạm.

⚠️ **Lưu ý:**
• Vẫn phải giảm tốc độ khi qua giao lộ
• Quan sát và nhường đường cho người đi bộ
• Không được vượt xe khác trong giao lộ

❌ **Chỉ bị phạt khi:**
• Vượt đèn **ĐỎ** hoặc đèn **VÀNG** (khi chưa qua vạch dừng)
• Gây tai nạn hoặc ùn tắc giao thông"""

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
• Quá trên 35 km/h: 6-8 triệu đồng

⚠️ Có thể bị tạm giữ phương tiện 7-10 ngày"""

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

💡 **Lưu ý:** Đèn đỏ phải dừng trước vạch sơn. 
Vượt đèn đỏ rất nguy hiểm, có thể gây tai nạn chết người!"""

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
• Hướng dẫn thủ tục hành chính

**Ví dụ:**
• "Phạt quá tốc độ bao nhiêu?"
• "Phạt nồng độ cồn 2026?"
• "Thủ tục đăng ký xe máy?"
• "Đèn vàng được đi không?"

💡 Hãy hỏi cụ thể để được tư vấn chính xác!"""


# ==================== AI CHATBOT XỬ LÝ TIN NHẮN ====================

def generate_bot_response(message, vehicle_id=None):
    """
    AI Rule-based response (fallback khi không có LLM API)
    """
    message_lower = message.lower().strip()
    
    # === AI RULE-BASED RESPONSE ===
    
    # 1. Chào hỏi
    if any(x in message_lower for x in ['xin chào', 'hello', 'hi', 'chào']):
        return 'Xin chào quý khách! 🚗 Tôi là Vietravel Supporter. Tôi có thể giúp gì cho bạn?'
    
    # 2. Cảm ơn
    if any(x in message_lower for x in ['cảm ơn', 'cam on', 'thanks']):
        return 'Dạ không có gì ạ! Rất vui được hỗ trợ quý khách. 😊'
    
    # 3. Hỏi về xe
    if any(x in message_lower for x in ['xe ở đâu', 'vị trí xe', 'xe nào', 'tìm xe']):
        import re
        plate_match = re.search(r'(\d{1,2}[A-Z]-\d{3}\.\d{2})', message, re.IGNORECASE)
        if plate_match:
            plate = plate_match.group(0).upper()
            vehicles = [
                {'plate': '29A-111.11', 'driver': 'Nguyễn Văn Đức', 'location': 'Võ Chí Công'},
                {'plate': '29B-222.22', 'driver': 'Trần Văn Hoan', 'location': 'Bến xe Mỹ Đình'},
                {'plate': '30E-333.33', 'driver': 'Lê Thị Đào', 'location': 'Minh Khai'},
            ]
            for v in vehicles:
                if v['plate'] == plate:
                    return f"🚗 Xe {plate} do tài xế {v['driver']} lái, đang ở vị trí: {v['location']}"
            return f"❌ Không tìm thấy xe biển số {plate}"
        return 'Bạn vui lòng cho biết biển số xe, ví dụ: "Xe 29B-222.22 ở đâu?"'
    
    # 4. Hỏi về vi phạm / cảnh báo
    if any(x in message_lower for x in ['vi phạm', 'cảnh báo', 'lỗi', 'bị phạt']):
        return f'''📊 Thống kê vi phạm hôm nay:
- 📱 Dùng điện thoại: {warnings.get('phone', '') and 1 or 0} lần
- 😴 Ngáp ngủ: {warnings.get('yawn', '') and 1 or 0} lần
- ⚠️ Không dây an toàn: {warnings.get('seatbelt', '') and 1 or 0} lần
- 🚨 Va chạm: {warnings.get('collision', '') and 1 or 0} lần

Bạn muốn xem chi tiết xe nào?'''
    
    # 5. Hỏi về tài xế
    if any(x in message_lower for x in ['tài xế', 'tài xế nào', 'ai lái']):
        return '''👨‍✈️ Danh sách tài xế đang hoạt động:
1. Nguyễn Văn Đức - 29A-111.11
2. Trần Văn Hoan - 29B-222.22
3. Lê Thị Đào - 30E-333.33

Bạn cần thông tin tài xế nào?'''
    
    # 6. Yêu cầu hỗ trợ
    if any(x in message_lower for x in ['hỗ trợ', 'giúp', 'help', 'cần giúp']):
        return '''🆘 Tôi có thể giúp bạn:
- 📍 Theo dõi vị trí xe
- ⚠️ Xem cảnh báo vi phạm
- 👤 Thông tin tài xế
- 📊 Thống kê hành trình

Bạn cần gì?'''
    
    # 7. Hỏi về thời tiết / giao thông
    if any(x in message_lower for x in ['thời tiết', 'giao thông', 'đường xá']):
        return '''🌤️ Thời tiết Hà Nội:
- Nhiệt độ: 25°C
- Trời nắng đẹp
- Giao thông thuận lợi

Chúc bạn lái xe an toàn! 🚗'''
    
    # 8. Tạm biệt
    if any(x in message_lower for x in ['tạm biệt', 'bye', 'goodbye', 'kết thúc']):
        return 'Cảm ơn bạn đã sử dụng dịch vụ! Chúc bạn một ngày tốt lành! 🌟'
    
    # === DEFAULT RESPONSE ===
    return '''Cảm ơn bạn đã nhắn tin! 
Tôi đã nhận được yêu cầu và sẽ phản hồi sớm nhất.

Hoặc bạn có thể:
- 🎤 Nói: "Xem cảnh báo"
- 📍 Hỏi: "Xe 29B-222.22 ở đâu?"
- 📊 Hỏi: "Thống kê hôm nay"'''


def call_llm_api(message, vehicle_id=None):
    """
    Gọi API từ mô hình AI thực thụ (LLM)
    Hỗ trợ: OpenAI, Google Gemini, Groq (miễn phí)
    """

    # === OPTION 1: GROQ (MIỄN PHÍ, NHANH) ===
    # API Key đã được tích hợp
    try:
        from groq import Groq
        import os
        from dotenv import load_dotenv  # type: ignore

        # Load API key từ file .env
        load_dotenv()
        GROQ_API_KEY = os.getenv('GROQ_API_KEY')
        
        if not GROQ_API_KEY:
            print("⚠️ Không tìm thấy GROQ_API_KEY trong .env file")
            return None

        client = Groq(api_key=GROQ_API_KEY)
        
        # === DATA THỰC TẾ TỪ HỆ THỐNG ===
        # Lấy thông tin xe từ data
        vehicles_data = [
            {'plate': '29A-111.11', 'driver': 'Nguyễn Văn Đức', 'location': 'Võ Chí Công', 'status': 'Đang chạy', 'speed': 45},
            {'plate': '29B-222.22', 'driver': 'Trần Văn Hoan', 'location': 'Bến xe Mỹ Đình', 'status': 'Đang dừng', 'speed': 0},
            {'plate': '30E-333.33', 'driver': 'Lê Thị Đào', 'location': 'Minh Khai', 'status': 'Đang chạy', 'speed': 30},
            {'plate': '29H-444.44', 'driver': 'Phạm Văn Dũng', 'location': 'Ngã tư Sở', 'status': 'Đang chạy', 'speed': 50},
            {'plate': '15B-555.55', 'driver': 'Hoàng Văn Việt', 'location': 'Cao tốc 5B', 'status': 'Đang chạy', 'speed': 40},
            {'plate': '30G-666.66', 'driver': 'Vũ Thị Hồng', 'location': 'Phủ Tây Hồ', 'status': 'Đang chạy', 'speed': 40},
            {'plate': '29LD-777.77', 'driver': 'Công ty Travel', 'location': 'Cầu Chương Dương', 'status': 'Đang chạy', 'speed': 60},
        ]
        
        # Chuyển thành string để đưa vào context
        vehicles_info = "\n".join([
            f"- {v['plate']}: Tài xế {v['driver']}, vị trí {v['location']}, trạng thái {v['status']}, tốc độ {v['speed']} km/h"
            for v in vehicles_data
        ])
        
        # Context cho AI với DATA THỰC TẾ
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

=== HƯỚNG DẪN TRẢ LỜI ===
- Khi được hỏi về xe (ví dụ: "xe 29A-111.11 ở đâu"), TRA CỨU trong danh sách xe trên
- Trả lời bằng tiếng Việt, thân thiện, ngắn gọn
- Sử dụng emoji phù hợp
- Ưu tiên an toàn giao thông
- Nếu không tìm thấy biển số, nói "Không tìm thấy xe trong hệ thống"

=== USER MESSAGE ===
{message}

=== TRẢ LỜI ===
"""
        
        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Model mới nhất, nhanh và thông minh
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
    
    # === OPTION 2: OPENAI CHATGPT (TRẢ PHÍ) ===
    # Uncomment để dùng
    """
    try:
        from openai import OpenAI

        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-YOUR_API_KEY')
        client = OpenAI(api_key=OPENAI_API_KEY)

        context = "Bạn là trợ lý giao thông Vietravel. Cảnh báo: " + str(warnings) + ". User: " + message + ". Trả lời bằng tiếng Việt:"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý giao thông Vietravel"},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=300
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"❌ Lỗi OpenAI API: {e}")
        return None
    """
    
    # === OPTION 3: GOOGLE GEMINI (MIỄN PHÍ GIỚI HẠN) ===
    # Uncomment để dùng
    """
    try:
        import google.generativeai as genai

        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'YOUR_API_KEY')
        genai.configure(api_key=GEMINI_API_KEY)

        model = genai.GenerativeModel('gemini-pro')

        context = "Bạn là trợ lý giao thông Vietravel. Cảnh báo: " + str(warnings) + ". User: " + message + ". Trả lời bằng tiếng Việt:"

        response = model.generate_content(context)
        return response.text

    except Exception as e:
        print(f"❌ Lỗi Gemini API: {e}")
        return None
    """


def process_ai_chat_message(message, vehicle_id=None):
    """
    Xử lý tin nhắn chatbot với AI thực thụ
    Fallback về rule-based nếu API thất bại
    """
    # 1. Thử gọi LLM API
    llm_response = call_llm_api(message, vehicle_id)
    
    if llm_response:
        # Thành công với AI
        return llm_response
    
    # 2. Fallback về rule-based
    print("⚠️ Fallback về rule-based AI")
    return generate_bot_response(message, vehicle_id)


if __name__ == '__main__':
    try:
        import webbrowser
        from threading import Timer
        import os

        # Cấu hình cổng
        PORT = 5001

        browser_opened = False

        def open_browser():
            global browser_opened
            if not browser_opened:
                url = f'http://localhost:{PORT}/login'
                print(f"\n🌐 Mở browser: {url}")
                webbrowser.open(url)
                browser_opened = True

        init_app()
        threading.Thread(target=reset_temporary_counts, daemon=True).start()

        # Mở browser sau 2 giây khi server start
        Timer(2, open_browser).start()

        print("=" * 70)
        print("AI TRAFFIC MONITORING SYSTEM - WITH AUTHENTICATION")
        print("=" * 70)
        print("📋 TÀI KHOẢN:")
        print("  👮 Admin: username=admin, password=admin123")
        print("  👤 User:  username=user, password=user123")
        print("=" * 70)
        print(f"🌐 URL: http://localhost:{PORT}/login")
        print("=" * 70)
        print("💡 Nhấn Ctrl+C để dừng server")
        print("=" * 70)

        # Tắt debug mode để ổn định hơn
        app.run(debug=False, host='0.0.0.0', port=PORT, use_reloader=False)
    except Exception as e:
        print(f"Error in main: {str(e)}")


