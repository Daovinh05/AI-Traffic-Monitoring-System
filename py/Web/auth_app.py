"""
Flask Authentication Backend for AI Traffic Monitoring System
Author: AI Traffic Team
"""

from flask import Flask, render_template, redirect, url_for, request, jsonify, session, flash
from flask_bcrypt import Bcrypt
from flask_session import Session
from functools import wraps
import pymysql
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# ========================================
# CẤU HÌNH ỨNG DỤNG
# ========================================
app.secret_key = os.urandom(24)  # Key cho session

# Cấu hình MySQL (dùng PyMySQL)
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', 3306))
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'ai_traffic_monitoring')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Khởi tạo extensions
bcrypt = Bcrypt(app)
Session(app)

# ========================================
# HELPER: GET DB CONNECTION
# ========================================
def get_db_connection():
    """Tạo connection đến MySQL"""
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        port=app.config['MYSQL_PORT'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )

# ========================================
# ÁNH XẠ TÊN TIẾNG VIỆT VÀ TIẾNG ANH
# ========================================
# Bảng: users -> nguoi_dung
#   - username -> ten_dang_nhap
#   - password -> mat_khau
#   - email -> email
#   - full_name -> ho_va_ten
#   - role -> vai_tro
#   - avatar -> anh_dai_dien
#   - phone -> so_dien_thoai
#   - is_active -> hoat_dong
#   - last_login -> lan_cuoi_dang_nhap
#   - created_at -> ngay_tao
#   - updated_at -> ngay_cap_nhat
#
# Bảng: login_history -> lich_su_dang_nhap
#   - user_id -> nguoi_dung_id
#   - ip_address -> dia_chi_ip
#   - user_agent -> trinh_duyet
#   - status -> trang_thai
#   - created_at -> ngay_tao

# ========================================
# DECORATORS
# ========================================
def login_required(f):
    """Yêu cầu đăng nhập"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Yêu cầu quyền admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập'}), 401
        if session.get('vai_tro') != 'admin':
            return jsonify({'success': False, 'message': 'Bạn không có quyền truy cập'}), 403
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """Yêu cầu role cụ thể"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': 'Vui lòng đăng nhập'}), 401
            if session.get('vai_tro') not in allowed_roles:
                return jsonify({'success': False, 'message': 'Bạn không có quyền truy cập'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ========================================
# ROUTES TRANG CHỦ
# ========================================
@app.route('/')
def index():
    """Trang chủ - Chuyển hướng dựa trên quyền"""
    if 'user_id' in session:
        if session.get('vai_tro') == 'admin':
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('trang_chu'))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    """Trang đăng nhập"""
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
@role_required(['admin'])
def dashboard():
    """Dashboard dành cho Admin"""
    return render_template('Dashboard.html', user=session.get('user'))

@app.route('/trang_chu')
@login_required
@role_required(['user', 'admin'])
def trang_chu():
    """Trang chủ dành cho User"""
    return render_template('trang_chu.html', user=session.get('user'))

@app.route('/lai_xe')
@login_required
@role_required(['user', 'admin'])
def lai_xe():
    """Trang Lái Xe"""
    return render_template('lai_xe.html', user=session.get('user'))

@app.route('/tu_van')
@login_required
@role_required(['user', 'admin'])
def tu_van():
    """Trang Tư Vấn"""
    return render_template('tu_van.html', user=session.get('user'))

@app.route('/tu_van.html')
@login_required
@role_required(['user', 'admin'])
def tu_van_html():
    """Trang Tư Vấn (HTML)"""
    return render_template('tu_van.html', user=session.get('user'))

@app.route('/lai_xe_v2')
@login_required
@role_required(['user', 'admin'])
def lai_xe_v2():
    """Trang Lái Xe V2"""
    return render_template('lai_xe.html', user=session.get('user'))

# ========================================
# API AUTHENTICATION
# ========================================
@app.route('/api/login', methods=['POST'])
def api_login():
    """
    API Đăng nhập
    Request: JSON { username: string, password: string }
    Response: JSON { success: bool, message: string, redirect: string, user: object }
    """
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu'
            }), 400
        
        # Get connection
        conn = get_db_connection()
        cur = conn.cursor()

        # Tìm user trong database
        cur.execute('''
            SELECT id, ten_dang_nhap, mat_khau, email, ho_va_ten, vai_tro, anh_dai_dien, so_dien_thoai, hoat_dong
            FROM nguoi_dung
            WHERE ten_dang_nhap = %s
        ''', (username,))

        user = cur.fetchone()
        cur.close()
        conn.close()
        
        # Kiểm tra user tồn tại
        if not user:
            return jsonify({
                'success': False,
                'message': 'Tên đăng nhập không tồn tại'
            }), 401
        
        # Kiểm tra tài khoản có active không
        if not user['hoat_dong']:
            return jsonify({
                'success': False,
                'message': 'Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên'
            }), 403

        # Kiểm tra mật khẩu
        if not bcrypt.check_password_hash(user['mat_khau'], password):
            # Ghi nhận đăng nhập thất bại
            log_login_attempt(user['id'], 'failed')

            return jsonify({
                'success': False,
                'message': 'Mật khẩu không đúng'
            }), 401

        # Đăng nhập thành công
        # Cập nhật last_login
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('UPDATE nguoi_dung SET lan_cuoi_dang_nhap = NOW() WHERE id = %s', (user['id'],))
        conn.commit()
        cur.close()
        conn.close()

        # Ghi nhận đăng nhập thành công
        log_login_attempt(user['id'], 'success')

        # Tạo session
        session.permanent = True
        session['user_id'] = user['id']
        session['ten_dang_nhap'] = user['ten_dang_nhap']
        session['vai_tro'] = user['vai_tro']
        session['ho_va_ten'] = user['ho_va_ten']
        session['anh_dai_dien'] = user['anh_dai_dien']

        # Xác định redirect dựa trên role
        if user['vai_tro'] == 'admin':
            redirect_url = '/dashboard'
        else:
            redirect_url = '/trang_chu'

        return jsonify({
            'success': True,
            'message': 'Đăng nhập thành công',
            'redirect': redirect_url,
            'user': {
                'id': user['id'],
                'ten_dang_nhap': user['ten_dang_nhap'],
                'ho_va_ten': user['ho_va_ten'],
                'vai_tro': user['vai_tro'],
                'anh_dai_dien': user['anh_dai_dien']
            }
        }), 200
        
    except pymysql.Error as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi database: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi hệ thống: {str(e)}'
        }), 500

@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    """
    API Đăng xuất
    Response: JSON { success: bool, message: string }
    """
    user_id = session.get('user_id')
    
    # Clear session
    session.clear()
    
    return jsonify({
        'success': True,
        'message': 'Đăng xuất thành công',
        'redirect': '/login'
    }), 200

@app.route('/api/check-auth')
def check_auth():
    """
    API Kiểm tra trạng thái đăng nhập
    Response: JSON { authenticated: bool, user: object|null, redirect: string|null }
    """
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session.get('user_id'),
                'ten_dang_nhap': session.get('ten_dang_nhap'),
                'vai_tro': session.get('vai_tro'),
                'ho_va_ten': session.get('ho_va_ten'),
                'anh_dai_dien': session.get('anh_dai_dien')
            },
            'redirect': '/dashboard' if session.get('vai_tro') == 'admin' else '/trang_chu'
        }), 200

    return jsonify({
        'authenticated': False,
        'user': None,
        'redirect': None
    }), 200

@app.route('/api/user/profile')
@login_required
def get_profile():
    """
    API Lấy thông tin user hiện tại
    Response: JSON { success: bool, user: object }
    """
    return jsonify({
        'success': True,
        'user': {
            'id': session.get('user_id'),
            'ten_dang_nhap': session.get('ten_dang_nhap'),
            'ho_va_ten': session.get('ho_va_ten'),
            'email': session.get('email'),
            'vai_tro': session.get('vai_tro'),
            'anh_dai_dien': session.get('anh_dai_dien'),
            'so_dien_thoai': session.get('so_dien_thoai')
        }
    }), 200

# ========================================
# HELPER FUNCTIONS
# ========================================
def log_login_attempt(user_id, status):
    """Ghi nhận lịch sử đăng nhập"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO lich_su_dang_nhap (nguoi_dung_id, dia_chi_ip, trinh_duyet, trang_thai)
            VALUES (%s, %s, %s, %s)
        ''', (user_id, request.remote_addr, request.user_agent.string, status))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error logging login attempt: {e}")

# ========================================
# ERROR HANDLERS
# ========================================
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    if request.is_json:
        return jsonify({'success': False, 'message': 'Bạn không có quyền truy cập'}), 403
    return render_template('403.html'), 403

@app.errorhandler(500)
def internal_error(e):
    if request.is_json:
        return jsonify({'success': False, 'message': 'Lỗi máy chủ nội bộ'}), 500
    return render_template('500.html'), 500

# ========================================
# MAIN
# ========================================
if __name__ == '__main__':
    import socket
    import subprocess
    import webbrowser
    import time
    import threading
    
    print("=" * 50)
    print("AI TRAFFIC MONITORING SYSTEM - AUTHENTICATION")
    print("=" * 50)
    print(f"Database: {app.config['MYSQL_DB']}")
    print(f"Host: {app.config['MYSQL_HOST']}:{app.config['MYSQL_PORT']}")
    print("=" * 50)
    print("Default accounts:")
    print("  Admin: username=admin, password=admin123")
    print("  User:  username=user, password=user123")
    print("=" * 50)
    
    # Kiểm tra và kill process cũ trên port 5001
    def kill_process_on_port(port):
        try:
            result = subprocess.run(
                f'lsof -ti:{port} | xargs kill -9 2>/dev/null',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✓ Đã giải phóng port {port}")
            else:
                print(f"✓ Port {port} đã sẵn sàng")
        except Exception as e:
            print(f"Lưu ý: {e}")
    
    # Tự động mở trình duyệt
    def open_browser():
        time.sleep(2)  # Đợi app khởi động
        webbrowser.open('http://localhost:5001/login')
    
    # Kill process cũ và mở browser
    kill_process_on_port(5001)
    
    # Chỉ mở browser nếu không phải restart mode
    import os
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(debug=False, host='0.0.0.0', port=5001)
