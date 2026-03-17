"""
AI Traffic Monitoring System - Controller
Flask routes and application logic
MVC Architecture - Controller Layer
"""

from flask import Flask, render_template, Response, jsonify, request, send_file, make_response, session, redirect, url_for, flash
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_session import Session
from functools import wraps
import pymysql
import os
from datetime import datetime, timedelta
import cv2
import pygame
import threading
import time
import numpy as np

# Import from models
from models import (
    # AI Alert System
    ai_alerts_queue, ai_alerts_lock, current_monitoring_vehicle_id, add_ai_alert,
    
    # Sound & Warning
    latest_warning, lock, warnings, warning_states, previous_warnings, active_video_stream,
    chopmat_sound, ngap_sound, phone_baodong, seatbelt_baodong, dau_quay_sound,
    bienbao_sound, tay_lai_sound, lech_lan_sounds, va_cham_sound, di_cham_lai_sound,
    can_play_warning,
    
    # Video Recording
    video_writer, is_recording, recording_start_time, fps, frame_width, frame_height, video_codec,
    current_video_filename, current_video_path, current_video_cam_id,
    
    # AI Models
    detector, predictor, phone_mau, seatbelt_mau, bienbao_model, model_vehicle, model_lane, model_hole,
    
    # Face Landmark
    EAR_THRESHOLD, EAR_MIN_DURATION, YAWN_THRESHOLD, YAWN_CONSEC_FRAMES,
    left_eye_indexes, right_eye_indexes, mouth_indexes,
    
    # Helper Functions
    eye_aspect_ratio, detect_yawn, get_head_pose,
    
    # Hand Tracking
    hand_detector, HandAndArmTracking,
    
    # Traffic Sign
    PICTURES_DIR, latest_sign_image_path, latest_sign_label,
    
    # Collision Detection
    last_collision_warning, warning_interval, collision_alert_sent, lane_alert_sent,
    process_lane_warning,
    
    # Traffic Monitoring
    region_colors, vehicle_colors, MultipleObjectCounter, counter, video_capture,
    current_region_type, current_location_id, location_video_map,
    get_region_points, init_app,
    
    # Chatbot
    generate_bot_response, call_llm_api, process_ai_chat_message, call_groq_law_advisor, generate_law_response_fallback,
    
    # Lane detection helpers
    estimate_distance, is_in_center_lane, draw_lane_points, draw_lane_classic,
    detect_lane_deviation_combined, collision_monitor, traffic_monitor,
    driver_monitor, traffic_sign_monitor, reset_temporary_counts,
)

# ========================================
# FLASK APP CONFIG
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
app.config['MYSQL_DB'] = 'giam_sat'

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
# DATABASE CONNECTION
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
# AUTHENTICATION ROUTES
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
        cur.execute('SELECT id, ten_dang_nhap as username, mat_khau as password, vai_tro as role, ho_ten as full_name, trang_thai_hoat_dong as is_active FROM nguoi_dung WHERE ten_dang_nhap = %s', (username,))
        user = cur.fetchone()
        cur.close()
        cur.close() # Close the initial cursor

        if not user:
            conn.close()
            return jsonify({'success': False, 'message': 'Tên đăng nhập không tồn tại'}), 401

        if not user['is_active']:
            conn.close()
            return jsonify({'success': False, 'message': 'Tài khoản đã bị khóa'}), 403

        if not bcrypt.check_password_hash(user['password'], password):
            conn.close()
            return jsonify({'success': False, 'message': 'Mật khẩu không đúng'}), 401

        session.permanent = True
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['full_name'] = user['full_name']

        # Nếu là tài xế, tìm tai_xe_id và vehicle_id tương ứng
        if user['role'] == 'user':
            cur = conn.cursor()
            # Tìm ID tài xế từ ID người dùng
            cur.execute('SELECT id FROM tai_xe WHERE id_nguoi_dung = %s', (user['id'],))
            driver = cur.fetchone()
            if driver:
                session['tai_xe_id'] = driver['id']
                # Tìm ID xe mà tài xế này đang lái
                cur.execute('SELECT id FROM phuong_tien WHERE id_tai_xe = %s', (driver['id'],))
                vehicle = cur.fetchone()
                if vehicle:
                    session['vehicle_id'] = vehicle['id']
            cur.close()

        conn.close()

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
        if session.get('role') == 'admin':
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('trang_chu_page'))
    else:
        return redirect(url_for('login_page'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        conn = get_db_connection()
        if not conn:
            return "Lỗi kết nối CSDL", 500
        
        cur = conn.cursor()
        
        # Tính toán thông số KPI tổng
        cur.execute('''
            SELECT trang_thai_hoat_dong as status
            FROM phuong_tien 
        ''')
        all_vehicles = cur.fetchall()
        
        stats = {
            'total_vehicles': len(all_vehicles),
            'running': sum(1 for v in all_vehicles if v['status'] == 'Đang chạy'),
            'stopped': sum(1 for v in all_vehicles if v['status'] == 'Đang dừng'),
            'offline': sum(1 for v in all_vehicles if v['status'] == 'Mất tín hiệu'),
            'alerts': 0,
            'violations': 0,
            'quality': 86.0
        }

        # Phân trang
        page = request.args.get('page', 1, type=int)
        per_page = 5
        offset = (page - 1) * per_page
        total_pages = (stats['total_vehicles'] + per_page - 1) // per_page
        
        # Lấy danh sách xe và tài xế (theo trang)
        cur.execute(f'''
            SELECT p.id, p.bien_so as plate_number, p.loai_xe as type, p.hinh_anh_xe as image,
                   t.ho_ten as driver_name, t.so_dien_thoai as phone, t.diem_danh_gia as score,
                   t.anh_dai_dien as driver_image,
                   td.ten_tuyen as location, p.vi_tri as vi_tri,
                   p.trang_thai_hoat_dong as status, p.toc_do_hien_tai as speed,
                   p.lat, p.lng,
                   (SELECT COUNT(*) FROM canh_bao_vi_pham WHERE id_phuong_tien = p.id AND da_doc = 0) as violations_count
            FROM phuong_tien p
            LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
            LEFT JOIN tuyen_duong td ON p.id_tuyen_duong = td.id
            ORDER BY p.id ASC
            LIMIT {per_page} OFFSET {offset}
        ''')
        vehicles = cur.fetchall()

        # Lấy toàn bộ xe không phân trang cho Javascript
        cur.execute('''
            SELECT p.id, p.bien_so as plate_number, p.loai_xe as type, p.hinh_anh_xe as image,
                   t.ho_ten as driver_name, t.so_dien_thoai as phone, t.diem_danh_gia as score,
                   t.anh_dai_dien as driver_image,
                   td.ten_tuyen as location, p.vi_tri as vi_tri,
                   p.trang_thai_hoat_dong as status, p.toc_do_hien_tai as speed,
                   p.lat, p.lng,
                   (SELECT COUNT(*) FROM canh_bao_vi_pham WHERE id_phuong_tien = p.id AND da_doc = 0) as violations_count
            FROM phuong_tien p
            LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
            LEFT JOIN tuyen_duong td ON p.id_tuyen_duong = td.id
            ORDER BY p.id ASC
        ''')
        all_vehicles = cur.fetchall()
        
        # Lấy danh sách toàn bộ tài xế
        cur.execute('''
            SELECT t.id, t.ma_tai_xe as code, t.ho_ten as name, t.so_dien_thoai as phone, 
                   t.so_giay_phep_lai_xe as license_type, 5 as experience, t.diem_danh_gia as rating,
                   t.anh_dai_dien as avatar, IF(t.trang_thai_hoat_dong = 1, 'Đang làm việc', 'Đang nghỉ') as status, 
                   (SELECT COUNT(*) FROM canh_bao_vi_pham WHERE id_tai_xe = t.id) as violations,
                   156 as total_trips
            FROM tai_xe t
        ''')
        drivers = cur.fetchall()

        # Lấy danh sách toàn bộ tuyến đường (bao gồm tọa độ起点 và终点)
        cur.execute('''
            SELECT 
                id as code, 
                ten_tuyen as name,
                mo_ta as description,
                COALESCE(start_lat, toa_do_lat) as start_lat, 
                COALESCE(start_lng, toa_do_lng) as start_lng,
                COALESCE(end_lat, toa_do_lat) as end_lat, 
                COALESCE(end_lng, toa_do_lng) as end_lng,
                distance,
                duration,
                vehicles,
                route_color as color,
                'Khu vực trung tâm' as start, 
                'Tuyến cố định' as end,
                0 as distance_old, 
                0 as duration_old,
                IF(trang_thai = 'active', 'Hoạt động', 'Ngừng hoạt động') as status
            FROM tuyen_duong
        ''')
        routes = cur.fetchall()
        
        # Lấy danh sách path cho tất cả các tuyến
        for route in routes:
            cur.execute('''
                SELECT latitude, longitude 
                FROM tuyen_duong_path 
                WHERE id_tuyen_duong = %s 
                ORDER BY point_order ASC
            ''', (route['code'],))
            path_points = cur.fetchall()
            # Chuyển thành mảng [[lat, lng], [lat, lng], ...]
            route['path'] = [[float(p['latitude']), float(p['longitude'])] for p in path_points]
        
        cur.execute('''
            SELECT 
                p.bien_so as plate, 
                t.ho_ten as driver, 
                td.ten_tuyen as location,
                c.loai_vi_pham as type, 
                c.noi_dung_vi_pham as typeLabel, 
                DATE_FORMAT(c.thoi_gian_vi_pham, '%H:%i %d/%m/%Y') as time, 
                IF(c.da_doc = 1, 'processed', 'pending') as status, 
                v.duong_dan_file as video
            FROM canh_bao_vi_pham c
            LEFT JOIN phuong_tien p ON c.id_phuong_tien = p.id
            LEFT JOIN tai_xe t ON c.id_tai_xe = t.id
            LEFT JOIN video_ghi_hinh v ON c.id_video_ghi_hinh = v.id
            LEFT JOIN tuyen_duong td ON p.id_tuyen_duong = td.id
            ORDER BY c.thoi_gian_vi_pham DESC
            LIMIT 50
        ''')
        warnings = cur.fetchall()
        
        cur.execute('''
            SELECT 
                tb.bien_so_xe as plate, 
                t.ho_ten as driver, 
                t.so_dien_thoai as phone,
                tb.noi_dung_thong_bao as content, 
                tb.muc_do_uu_tien as priority, 
                IF(tb.muc_do_uu_tien = 'high', 'Cao', IF(tb.muc_do_uu_tien = 'medium', 'Trung bình', 'Thấp')) as priorityLabel,
                DATE_FORMAT(tb.ngay_tao, '%d/%m/%Y') as date,
                DATE_FORMAT(tb.ngay_tao, '%H:%i') as time,
                nd.ho_ten as admin,
                'Không xác định' as location,
                COALESCE(c.noi_dung_vi_pham, 'Vi phạm hệ thống') as violationType,
                IF(tb.da_doc = 1, 'processed', 'pending') as status
            FROM thong_bao_admin tb
            LEFT JOIN phuong_tien p ON tb.bien_so_xe = p.bien_so
            LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
            LEFT JOIN nguoi_dung nd ON tb.id_admin = nd.id
            LEFT JOIN canh_bao_vi_pham c ON tb.id_vi_pham = c.id
            ORDER BY tb.ngay_tao DESC
            LIMIT 50
        ''')
        admin_alerts = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return render_template('Dashboard.html', 
                               vehicles=vehicles, 
                               all_vehicles=all_vehicles, 
                               stats=stats, 
                               drivers=drivers, 
                               routes=routes, 
                               warnings=warnings, 
                               admin_alerts=admin_alerts, 
                               user=session.get('user'),
                               user_role=session.get('role'),
                               page=page, 
                               total_pages=total_pages, 
                               now=datetime.now().strftime('%H:%M %d/%m/%Y'))
    except Exception as e:
        import traceback
        return Response(traceback.format_exc(), mimetype="text/plain")

@app.route('/trang_chu')
@login_required
def trang_chu_page():
    return render_template('trang_chu.html', 
                           user=session.get('user'),
                           tai_xe_id=session.get('tai_xe_id'),
                           vehicle_id=session.get('vehicle_id'))

@app.route('/tu_van')
@login_required
def tu_van_page():
    return render_template('tu_van.html', 
                           user=session.get('user'),
                           tai_xe_id=session.get('tai_xe_id'),
                           vehicle_id=session.get('vehicle_id'))

@app.route('/lai_xe')
@login_required
def lai_xe_page():
    return render_template('lai_xe.html', 
                           user=session.get('user'),
                           tai_xe_id=session.get('tai_xe_id'),
                           vehicle_id=session.get('vehicle_id'))

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
    """Lấy danh sách cảnh báo AI (vi phạm) của tài xế đăng nhập"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        tai_xe_id = session.get('tai_xe_id')
        if not tai_xe_id:
            return jsonify({'success': False, 'message': 'Không tìm thấy thông tin tài xế'}), 400

        # Phân trang: 10 vi phạm/trang cho tài xế
        page = request.args.get('page', 1, type=int)
        per_page = 10
        offset = (page - 1) * per_page

        cur = conn.cursor()
        
        # Đếm tổng số vi phạm
        cur.execute('SELECT COUNT(*) as total FROM canh_bao_vi_pham WHERE id_tai_xe = %s', (tai_xe_id,))
        total = cur.fetchone()['total']
        total_pages = (total + per_page - 1) // per_page
        
        # Lấy vi phạm theo trang
        cur.execute('''
            SELECT a.id, a.loai_vi_pham as type, a.noi_dung_vi_pham as message, a.muc_do as level,
                   a.thoi_gian_vi_pham as timestamp, a.da_doc as is_read,
                   v.bien_so as vehicle_plate, d.ho_ten as driver_name,
                   vid.duong_dan_file as video_path
            FROM canh_bao_vi_pham a
            LEFT JOIN phuong_tien v ON a.id_phuong_tien = v.id
            LEFT JOIN tai_xe d ON a.id_tai_xe = d.id
            LEFT JOIN video_ghi_hinh vid ON a.id_video_ghi_hinh = vid.id
            WHERE a.id_tai_xe = %s
            ORDER BY a.thoi_gian_vi_pham DESC
            LIMIT %s OFFSET %s
        ''', (tai_xe_id, per_page, offset))
        alerts = cur.fetchall()
        cur.close()
        conn.close()

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

        return jsonify({
            'success': True, 
            'alerts': formatted_alerts,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        })
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
        cur.execute('UPDATE canh_bao_vi_pham SET da_doc = 1 WHERE id = %s', (alert_id,))
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
        video_dir = 'recordings'
        videos = []

        if os.path.exists(video_dir):
            for filename in os.listdir(video_dir):
                if filename.endswith('.mp4'):
                    filepath = os.path.join(video_dir, filename)
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

        videos.sort(key=lambda x: x['timestamp'], reverse=True)

        return jsonify({'success': True, 'videos': videos[:50]})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/admin-warnings')
@login_required
def get_admin_warnings():
    """Lấy danh sách cảnh báo từ admin - Chỉ lấy của tài xế đăng nhập"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        # Lấy tai_xe_id và vehicle_id từ session
        tai_xe_id = session.get('tai_xe_id')
        user_role = session.get('role')
        
        # Nếu là admin, lấy tất cả; nếu là user, chỉ lấy của user đó
        if user_role == 'admin':
            # Admin xem tất cả cảnh báo - 15 cảnh báo/trang
            page = request.args.get('page', 1, type=int)
            per_page = 15
            offset = (page - 1) * per_page

            cur = conn.cursor()

            # Đếm tổng số cảnh báo
            cur.execute('SELECT COUNT(*) as total FROM thong_bao_admin')
            total = cur.fetchone()['total']
            total_pages = (total + per_page - 1) // per_page

            # Lấy tất cả cảnh báo
            cur.execute('''
                SELECT w.id, w.bien_so_xe as vehicle_plate, w.noi_dung_thong_bao as message,
                       w.muc_do_uu_tien as priority, w.da_doc as is_read, w.ngay_tao as created_at,
                       u.ho_ten as admin_name,
                       t.ho_ten as driver_name,
                       c.noi_dung_vi_pham as violationType
                FROM thong_bao_admin w
                LEFT JOIN phuong_tien p ON w.bien_so_xe = p.bien_so
                LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
                LEFT JOIN nguoi_dung u ON w.id_admin = u.id
                LEFT JOIN canh_bao_vi_pham c ON w.id_vi_pham = c.id
                ORDER BY w.ngay_tao DESC
                LIMIT %s OFFSET %s
            ''', (per_page, offset))
        else:
            # User chỉ xem cảnh báo của mình - 10 cảnh báo/trang
            if not tai_xe_id:
                return jsonify({'success': False, 'message': 'Không tìm thấy thông tin tài xế'}), 400

            page = request.args.get('page', 1, type=int)
            per_page = 10
            offset = (page - 1) * per_page

            cur = conn.cursor()

            # Đếm tổng số cảnh báo của tài xế này
            cur.execute('''
                SELECT COUNT(*) as total 
                FROM thong_bao_admin w
                LEFT JOIN phuong_tien p ON w.bien_so_xe = p.bien_so
                WHERE p.id_tai_xe = %s
            ''', (tai_xe_id,))
            total = cur.fetchone()['total']
            total_pages = (total + per_page - 1) // per_page

            # Lấy cảnh báo theo trang, chỉ lấy của tài xế đăng nhập
            cur.execute('''
                SELECT w.id, w.bien_so_xe as vehicle_plate, w.noi_dung_thong_bao as message,
                       w.muc_do_uu_tien as priority, w.da_doc as is_read, w.ngay_tao as created_at,
                       u.ho_ten as admin_name,
                       t.ho_ten as driver_name,
                       c.noi_dung_vi_pham as violationType
                FROM thong_bao_admin w
                LEFT JOIN phuong_tien p ON w.bien_so_xe = p.bien_so
                LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
                LEFT JOIN nguoi_dung u ON w.id_admin = u.id
                LEFT JOIN canh_bao_vi_pham c ON w.id_vi_pham = c.id
                WHERE p.id_tai_xe = %s
                ORDER BY w.ngay_tao DESC
                LIMIT %s OFFSET %s
            ''', (tai_xe_id, per_page, offset))
        
        warnings = cur.fetchall()
        cur.close()
        conn.close()

        formatted_warnings = []
        for warning in warnings:
            formatted_warnings.append({
                'id': warning['id'],
                'vehicle_plate': warning['vehicle_plate'],
                'message': warning['message'],
                'priority': warning['priority'],
                'is_read': bool(warning['is_read']),
                'created_at': warning['created_at'].isoformat() if warning['created_at'] else None,
                'admin_name': warning['admin_name'],
                'driver_name': warning['driver_name'],
                'violationType': warning['violationType'] if warning['violationType'] else 'Không rõ'
            })

        return jsonify({
            'success': True,
            'warnings': formatted_warnings,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/all-alerts')
@login_required
def get_all_alerts():
    """Lấy danh sách tất cả cảnh báo AI (vi phạm) - Dành cho admin"""
    try:
        # Chỉ admin mới được truy cập
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'message': 'Không có quyền truy cập'}), 403

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        # Phân trang: 15 vi phạm/trang cho admin
        page = request.args.get('page', 1, type=int)
        per_page = 15
        offset = (page - 1) * per_page

        cur = conn.cursor()
        
        # Đếm tổng số vi phạm
        cur.execute('SELECT COUNT(*) as total FROM canh_bao_vi_pham')
        total = cur.fetchone()['total']
        total_pages = (total + per_page - 1) // per_page
        
        # Lấy vi phạm theo trang
        cur.execute('''
            SELECT a.id, a.loai_vi_pham as type, a.noi_dung_vi_pham as message, a.muc_do as level,
                   a.thoi_gian_vi_pham as timestamp, a.da_doc as is_read,
                   v.bien_so as vehicle_plate, d.ho_ten as driver_name,
                   vid.duong_dan_file as video_path
            FROM canh_bao_vi_pham a
            LEFT JOIN phuong_tien v ON a.id_phuong_tien = v.id
            LEFT JOIN tai_xe d ON a.id_tai_xe = d.id
            LEFT JOIN video_ghi_hinh vid ON a.id_video_ghi_hinh = vid.id
            ORDER BY a.thoi_gian_vi_pham DESC
            LIMIT %s OFFSET %s
        ''', (per_page, offset))
        alerts = cur.fetchall()
        cur.close()
        conn.close()

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

        return jsonify({
            'success': True, 
            'alerts': formatted_alerts,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        })
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
        cur.execute('UPDATE thong_bao_admin SET da_doc = 1, ngay_doc = NOW() WHERE id = %s', (warning_id,))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Đã đánh dấu đã đọc'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/vehicle-cameras/<int:vehicle_id>')
@login_required
def get_vehicle_cameras(vehicle_id):
    """Lấy danh sách camera video của xe theo ID"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500
        cur = conn.cursor()
        cur.execute('''
            SELECT cx.vi_tri, cx.ten_camera, cx.video_file, p.bien_so, t.ho_ten as driver_name
            FROM camera_xe cx
            JOIN phuong_tien p ON cx.id_phuong_tien = p.id
            LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
            WHERE cx.id_phuong_tien = %s AND cx.trang_thai = 1
            ORDER BY FIELD(cx.vi_tri, 'tai_xe', 'truoc', 'hanh_khach', 'lui')
        ''', (vehicle_id,))
        cameras = cur.fetchall()
        cur.close()
        conn.close()

        if not cameras:
            return jsonify({
                'success': True, 'vehicle_id': vehicle_id, 'plate': '', 'driver': '',
                'cameras': {
                    'tai_xe': {'ten': 'Camera Tài Xế', 'video': 'ca_bin.mp4'},
                    'truoc': {'ten': 'Camera Trước', 'video': 'lech_lan.mp4'},
                    'hanh_khach': {'ten': 'Camera Hành Khách', 'video': 'passenger.mp4'},
                    'lui': {'ten': 'Camera Lùi', 'video': 'car1.mp4'}
                }
            })

        cam_dict = {}
        plate = ''
        driver = ''
        for cam in cameras:
            plate = cam['bien_so']
            driver = cam['driver_name'] or ''
            cam_dict[cam['vi_tri']] = {'ten': cam['ten_camera'], 'video': cam['video_file']}

        return jsonify({'success': True, 'vehicle_id': vehicle_id, 'plate': plate, 'driver': driver, 'cameras': cam_dict})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/send-warning', methods=['POST'])
@login_required
def send_warning_to_vehicle():
    """Gửi cảnh báo từ admin đến xe"""
    try:
        # Chỉ admin mới được gửi cảnh báo
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'message': 'Không có quyền truy cập'}), 403

        data = request.get_json()
        bien_so = data.get('plate', '').strip()
        noi_dung = data.get('content', '').strip()
        muc_do = data.get('priority', 'medium')  # low, medium, high
        alert_id = data.get('alert_id') # Lấy id_vi_pham

        if not bien_so or not noi_dung:
            return jsonify({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cur = conn.cursor()
        
        # Lấy id_admin từ session
        admin_id = session.get('user_id')
        
        # Insert cảnh báo mới vào database
        cur.execute('''
            INSERT INTO thong_bao_admin 
            (id_admin, id_vi_pham, bien_so_xe, noi_dung_thong_bao, muc_do_uu_tien, da_doc, ngay_tao)
            VALUES (%s, %s, %s, %s, %s, 0, NOW())
        ''', (admin_id, alert_id, bien_so, noi_dung, muc_do))
        
        warning_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'success': True, 
            'message': 'Đã gửi cảnh báo thành công',
            'warning_id': warning_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/mark-alert-processed', methods=['POST'])
@login_required
def mark_alert_as_processed():
    """Đánh dấu cảnh báo AI đã được xử lý (đã gửi cảnh cáo)"""
    try:
        # Chỉ admin mới được đánh dấu
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'message': 'Không có quyền truy cập'}), 403

        data = request.get_json()
        alert_id = data.get('alert_id')

        if not alert_id:
            return jsonify({'success': False, 'message': 'Thiếu alert_id'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cur = conn.cursor()
        # Đánh dấu đã đọc (da_doc = 1)
        cur.execute('UPDATE canh_bao_vi_pham SET da_doc = 1 WHERE id = %s', (alert_id,))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Đã đánh dấu đã xử lý'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

# ========================================
# MONITORING VEHICLE CONTROL
# ========================================
@app.route('/api/set_monitoring_vehicle', methods=['POST'])
@login_required
def set_monitoring_vehicle():
    """Set vehicle_id for monitoring - dùng khi admin/driver bắt đầu giám sát xe cụ thể"""
    from models import current_monitoring_vehicle_id
    import models
    data = request.get_json()
    v_id = data.get('vehicle_id') if data else None
    if v_id:
        models.current_monitoring_vehicle_id = int(v_id)
    else:
        models.current_monitoring_vehicle_id = None
    return jsonify({'success': True, 'vehicle_id': models.current_monitoring_vehicle_id})

# ========================================
# VIDEO STREAMING ROUTES
# ========================================
@app.route('/video_driver')
def video_driver():
    import models
    vehicle_id = session.get('vehicle_id') or models.current_monitoring_vehicle_id
    return Response(driver_monitor(vehicle_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_traffic')
def video_traffic():
    import models
    vehicle_id = session.get('vehicle_id') or models.current_monitoring_vehicle_id
    return Response(traffic_sign_monitor(vehicle_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_sign')
def video_sign():
    global current_location_id
    location_id = request.args.get('location', None)

    if location_id and location_id in location_video_map:
        current_location_id = location_id
        region_type = location_video_map[location_id]

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
    vehicle_id = session.get('vehicle_id')
    return Response(collision_monitor(vehicle_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/recordings/<path:filename>')
def serve_video(filename):
    """Serve video files from recordings or video_input directory"""
    # 1. Check in root recordings directory (absolute path)
    recordings_path = os.path.join(os.getcwd(), 'recordings', filename)
    if os.path.exists(recordings_path):
        return send_file(recordings_path)
    
    # 2. Fallback to py/video_input directory (absolute path)
    video_input_path = os.path.join(os.getcwd(), 'py', 'video_input', filename)
    if os.path.exists(video_input_path):
        return send_file(video_input_path)
        
    return "Video not found", 404

# ========================================
# CONTROL API ROUTES
# ========================================
@app.route('/change_region_points', methods=['POST'])
@login_required
def change_region_points():
    global counter, current_region_type, video_capture, active_video_stream, current_location_id
    try:
        data = request.get_json()
        region_type = data.get('type')
        location_id = data.get('location')

        if location_id and location_id in location_video_map:
            region_type = location_video_map[location_id]
            current_location_id = location_id
        elif region_type in ['single', 'multiple', 'thanhxuan', 'ngatuso']:
            current_location_id = [k for k, v in location_video_map.items() if v == region_type][0]

        if region_type in ['single', 'multiple', 'thanhxuan', 'ngatuso']:
            print(f"Changing to region type: {region_type} (location: {current_location_id})")

            active_video_stream = None
            time.sleep(1)

            if video_capture is not None:
                video_capture.release()
                video_capture = None

            current_region_type = region_type
            region_data = get_region_points(region_type)
            region_points = region_data['regions']
            video_source = region_data['video_source']

            print(f"Using video source: {video_source}")

            if not os.path.exists(video_source):
                print(f"Video file not found: {video_source}")
                return jsonify({"status": "error", "message": f"Không tìm thấy file video: {video_source}"})

            video_capture = cv2.VideoCapture(video_source)
            if not video_capture.isOpened():
                print(f"Failed to open video: {video_source}")
                return jsonify({"status": "error", "message": f"Không thể mở video: {video_source}"})

            video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 720)
            video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 560)
            video_capture.set(cv2.CAP_PROP_FPS, 20)

            print(f"Video capture initialized with properties: {video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)}x{video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)}")

            object_classes = [2, 3, 5, 7]
            counter = MultipleObjectCounter(model_path="py/weights/yolov8n.pt", regions=region_points, classes=object_classes)

            active_video_stream = 'traffic'

            print("Region change completed successfully")
            return jsonify({"status": "success"})

        return jsonify({"status": "error", "message": "Invalid region type"})
    except Exception as e:
        print(f"Error in change_region_points: {str(e)}")
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

@app.route('/get_warnings')
@login_required
def get_warnings():
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

        active_video_stream = None
        time.sleep(0.5)

        current_mode = new_mode
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error in set_mode: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/start_recording')
@login_required
def start_recording():
    import models
    from models import (
        video_writer, is_recording, recording_start_time,
        current_video_filename, current_video_path, current_video_cam_id,
        video_codec, fps, frame_width, frame_height
    )

    if not models.is_recording:
        section_id = request.args.get('section_id', 'driver')
        
        # Map section_id to camera_id from camera_giam_sat table
        # 1: Driver, 2: Road/Collision, 3: Sign, 4: Hanoi, 5: Thanh Xuan
        cam_mapping = {
            'driver': 1,
            'vacham': 2,
            'traffic': 3,
            'sign': 4 # For traffic flow, using Hanoi trạm as default or based on location
        }
        
        models.current_video_cam_id = cam_mapping.get(section_id, 1)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        models.current_video_filename = f'output_{timestamp}.mp4'
        models.current_video_path = f'recordings/{models.current_video_filename}'

        # Ensure directory exists
        if not os.path.exists('recordings'):
            os.makedirs('recordings')

        models.video_writer = cv2.VideoWriter(
            models.current_video_path,
            video_codec,
            fps,
            (frame_width, frame_height)
        )

        models.is_recording = True
        models.recording_start_time = datetime.now()
        return f"Recording started for {section_id}"
    return "Already recording"

@app.route('/stop_recording')
@login_required
def stop_recording():
    import models
    from models import (
        is_recording, video_writer, recording_start_time,
        current_video_filename, current_video_path, current_video_cam_id
    )

    if models.is_recording and models.video_writer is not None:
        models.video_writer.release()
        models.video_writer = None
        models.is_recording = False
        
        end_time = datetime.now()
        start_time = models.recording_start_time
        file_path = models.current_video_path
        file_name = models.current_video_filename
        cam_id = models.current_video_cam_id
        
        # Calculate file size
        file_size = 0
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            
        # Save to database and link to violation
        try:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor()
                
                # 1. Insert into video_ghi_hinh
                # Format path to be accessible via /recordings/ route
                web_path = f"/recordings/{file_name}"
                cur.execute("""
                    INSERT INTO video_ghi_hinh (id_camera, ten_file_video, duong_dan_file, thoi_gian_bat_dau, thoi_gian_ket_thuc, kich_thuoc_file)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (cam_id, file_name, web_path, start_time, end_time, file_size))
                
                video_id = cur.lastrowid
                
                # 2. Link all violations for the current vehicle/driver within the recording time range
                vehicle_id = session.get('vehicle_id') or models.current_monitoring_vehicle_id
                
                if vehicle_id:
                    # Link violations from 10 seconds before start until now
                    link_start_time = start_time - timedelta(seconds=10)
                    cur.execute("""
                        UPDATE canh_bao_vi_pham 
                        SET id_video_ghi_hinh = %s 
                        WHERE id_phuong_tien = %s 
                        AND thoi_gian_vi_pham BETWEEN %s AND %s
                    """, (video_id, vehicle_id, link_start_time, end_time))
                
                conn.commit()
                cur.close()
                conn.close()
                return f"Recording stopped and saved (ID: {video_id})"
        except Exception as e:
            print(f"Error saving recording to DB: {e}")
            return f"Recording stopped but error saving to DB: {str(e)}"

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

# ========================================
# CHATBOT & VOICE COMMAND APIs
# ========================================
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
            'alerts': ai_alerts_queue[-20:]
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

        if 'hiển thị xe' in command or 'tìm xe' in command:
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

        print(f"[CHAT] User {user_id} (xe {vehicle_id}): {message}")

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

# ========================================
# ROUTE MANAGEMENT API ENDPOINTS
# ========================================
@app.route('/api/routes', methods=['GET'])
@login_required
def get_routes():
    """Lấy danh sách tất cả tuyến đường với path chi tiết"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cur = conn.cursor()
        cur.execute('''
            SELECT 
                id, ten_tuyen, mo_ta,
                start_lat, start_lng, end_lat, end_lng,
                distance, duration, vehicles, route_color,
                toa_do_lat, toa_do_lng, trang_thai
            FROM tuyen_duong
            ORDER BY ten_tuyen ASC
        ''')
        routes = cur.fetchall()
        
        # Lấy path cho từng tuyến
        formatted_routes = []
        for route in routes:
            cur.execute('''
                SELECT latitude, longitude 
                FROM tuyen_duong_path 
                WHERE id_tuyen_duong = %s 
                ORDER BY point_order ASC
            ''', (route['id'],))
            path_points = cur.fetchall()
            
            formatted_routes.append({
                'id': route['id'],
                'code': route['id'],
                'name': route['ten_tuyen'],
                'description': route['mo_ta'],
                'start_lat': float(route['start_lat']) if route['start_lat'] else None,
                'start_lng': float(route['start_lng']) if route['start_lng'] else None,
                'end_lat': float(route['end_lat']) if route['end_lat'] else None,
                'end_lng': float(route['end_lng']) if route['end_lng'] else None,
                'distance': float(route['distance']) if route['distance'] else 0,
                'duration': int(route['duration']) if route['duration'] else 0,
                'vehicles': route['vehicles'],
                'color': route['route_color'] or '#4a9eff',
                'center_lat': float(route['toa_do_lat']) if route['toa_do_lat'] else None,
                'center_lng': float(route['toa_do_lng']) if route['toa_do_lng'] else None,
                'status': 'Hoạt động' if route['trang_thai'] == 'active' else 'Ngừng hoạt động',
                'path': [[float(p['latitude']), float(p['longitude'])] for p in path_points]
            })

        cur.close()
        conn.close()

        return jsonify({'success': True, 'routes': formatted_routes})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/routes/<route_id>', methods=['GET'])
@login_required
def get_route_detail(route_id):
    """Lấy chi tiết một tuyến đường"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cur = conn.cursor()
        cur.execute('''
            SELECT 
                id, ten_tuyen, mo_ta,
                start_lat, start_lng, end_lat, end_lng,
                toa_do_lat, toa_do_lng, trang_thai
            FROM tuyen_duong
            WHERE id = %s
        ''', (route_id,))
        route = cur.fetchone()
        cur.close()
        conn.close()

        if not route:
            return jsonify({'success': False, 'message': 'Tuyến đường không tồn tại'}), 404

        return jsonify({
            'success': True,
            'route': {
                'id': route['id'],
                'name': route['ten_tuyen'],
                'description': route['mo_ta'],
                'start_lat': float(route['start_lat']) if route['start_lat'] else None,
                'start_lng': float(route['start_lng']) if route['start_lng'] else None,
                'end_lat': float(route['end_lat']) if route['end_lat'] else None,
                'end_lng': float(route['end_lng']) if route['end_lng'] else None,
                'center_lat': float(route['toa_do_lat']) if route['toa_do_lat'] else None,
                'center_lng': float(route['toa_do_lng']) if route['toa_do_lng'] else None,
                'status': route['trang_thai']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/routes', methods=['POST'])
@login_required
def create_route():
    """Tạo mới tuyến đường"""
    try:
        data = request.get_json()
        route_id = data.get('id', '').strip()
        name = data.get('name', '').strip()
        description = data.get('description', '')
        distance = data.get('distance', 0)
        duration = data.get('duration', 0)
        vehicles = data.get('vehicles', '')
        color = data.get('color', '#4a9eff')
        status = data.get('status', 'active')
        path = data.get('path', [])  # Mảng [[lat, lng], [lat, lng], ...]

        if not route_id or not name:
            return jsonify({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin'}), 400

        if not path or len(path) < 2:
            return jsonify({'success': False, 'message': 'Tuyến đường cần ít nhất 2 điểm tọa độ'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cur = conn.cursor()
        
        # Check if route exists
        cur.execute('SELECT id FROM tuyen_duong WHERE id = %s', (route_id,))
        if cur.fetchone():
            return jsonify({'success': False, 'message': 'Mã tuyến đường đã tồn tại'}), 400

        # Lấy tọa độ điểm đầu và cuối
        start_lat, start_lng = path[0]
        end_lat, end_lng = path[-1]

        cur.execute('''
            INSERT INTO tuyen_duong 
            (id, ten_tuyen, mo_ta, start_lat, start_lng, end_lat, end_lng, 
             distance, duration, vehicles, route_color, trang_thai)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (route_id, name, description, start_lat, start_lng, end_lat, end_lng, 
              distance, duration, vehicles, color, status))
        
        # Insert các điểm path
        for i, (lat, lng) in enumerate(path):
            cur.execute('''
                INSERT INTO tuyen_duong_path (id_tuyen_duong, point_order, latitude, longitude)
                VALUES (%s, %s, %s, %s)
            ''', (route_id, i + 1, lat, lng))
        
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Tạo tuyến đường thành công'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/routes/<route_id>', methods=['PUT'])
@login_required
def update_route(route_id):
    """Cập nhật tuyến đường"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '')
        distance = data.get('distance', 0)
        duration = data.get('duration', 0)
        vehicles = data.get('vehicles', '')
        color = data.get('color', '#4a9eff')
        status = data.get('status', 'active')
        path = data.get('path', [])  # Mảng [[lat, lng], [lat, lng], ...]

        if not name:
            return jsonify({'success': False, 'message': 'Vui lòng nhập đầy đủ thông tin'}), 400

        if path and len(path) < 2:
            return jsonify({'success': False, 'message': 'Tuyến đường cần ít nhất 2 điểm tọa độ'}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cur = conn.cursor()
        
        # Check if route exists
        cur.execute('SELECT id FROM tuyen_duong WHERE id = %s', (route_id,))
        if not cur.fetchone():
            return jsonify({'success': False, 'message': 'Tuyến đường không tồn tại'}), 404

        # Nếu có path mới, cập nhật tọa độ đầu cuối
        if path:
            start_lat, start_lng = path[0]
            end_lat, end_lng = path[-1]
            
            cur.execute('''
                UPDATE tuyen_duong 
                SET ten_tuyen = %s, mo_ta = %s, start_lat = %s, start_lng = %s, 
                    end_lat = %s, end_lng = %s, distance = %s, duration = %s, 
                    vehicles = %s, route_color = %s, trang_thai = %s
                WHERE id = %s
            ''', (name, description, start_lat, start_lng, end_lat, end_lng, 
                  distance, duration, vehicles, color, status, route_id))
            
            # Xóa path cũ và thêm path mới
            cur.execute('DELETE FROM tuyen_duong_path WHERE id_tuyen_duong = %s', (route_id,))
            for i, (lat, lng) in enumerate(path):
                cur.execute('''
                    INSERT INTO tuyen_duong_path (id_tuyen_duong, point_order, latitude, longitude)
                    VALUES (%s, %s, %s, %s)
                ''', (route_id, i + 1, lat, lng))
        else:
            # Chỉ cập nhật thông tin cơ bản
            cur.execute('''
                UPDATE tuyen_duong 
                SET ten_tuyen = %s, mo_ta = %s, distance = %s, duration = %s, 
                    vehicles = %s, route_color = %s, trang_thai = %s
                WHERE id = %s
            ''', (name, description, distance, duration, vehicles, color, status, route_id))
        
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Cập nhật tuyến đường thành công'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/routes/<route_id>', methods=['DELETE'])
@login_required
def delete_route(route_id):
    """Xóa tuyến đường"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database error'}), 500

        cur = conn.cursor()
        
        # Check if route exists
        cur.execute('SELECT id FROM tuyen_duong WHERE id = %s', (route_id,))
        if not cur.fetchone():
            return jsonify({'success': False, 'message': 'Tuyến đường không tồn tại'}), 404

        cur.execute('DELETE FROM tuyen_duong WHERE id = %s', (route_id,))
        
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Xóa tuyến đường thành công'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'}), 500

# ========================================
# MAIN APPLICATION
# ========================================
if __name__ == '__main__':
    try:
        import webbrowser
        from threading import Timer
        import pygame

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

        app.run(debug=False, host='0.0.0.0', port=PORT, use_reloader=False)
    except Exception as e:
        print(f"Error in main: {str(e)}")
