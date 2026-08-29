#!/usr/bin/env python3
"""
Script tạo password hash và cập nhật database
Sử dụng: python reset_password.py
"""

import pymysql
from flask_bcrypt import Bcrypt

# Cấu hình database
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',
    'database': 'giam_sat',
    'charset': 'utf8mb4'
}

# Password mặc định
DEFAULT_PASSWORD = 'admin123'

def create_password_hash(password):
    """Tạo password hash bằng bcrypt"""
    bcrypt = Bcrypt()
    return bcrypt.generate_password_hash(password).decode('utf-8')

def update_database():
    """Cập nhật password cho tất cả user trong database"""
    try:
        # Kết nối database
        conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
        cursor = conn.cursor()
        
        # Tạo password hash
        password_hash = create_password_hash(DEFAULT_PASSWORD)
        
        print(f"Password hash cho '{DEFAULT_PASSWORD}':")
        print(password_hash)
        print()
        
        # Cập nhật password cho tất cả user
        cursor.execute("""
            UPDATE nguoi_dung 
            SET mat_khau = %s
        """, (password_hash,))
        
        conn.commit()
        
        # Hiển thị danh sách user đã cập nhật
        cursor.execute("SELECT id, ten_dang_nhap, vai_tro, ho_ten FROM nguoi_dung")
        users = cursor.fetchall()
        
        print(f"✓ Đã cập nhật password cho {len(users)} user:")
        print("-" * 60)
        for user in users:
            print(f"  - {user['ten_dang_nhap']} ({user['vai_tro']}): {user['ho_ten']}")
        
        print("-" * 60)
        print(f"\n✓ Thành công! Tất cả user đều có password là: {DEFAULT_PASSWORD}")
        print("\nBây giờ bạn có thể đăng nhập với:")
        print(f"  Username: admin | Password: {DEFAULT_PASSWORD}")
        print(f"  Username: user  | Password: {DEFAULT_PASSWORD}")
        
        cursor.close()
        conn.close()
        
    except pymysql.Error as e:
        print(f"✗ Lỗi database: {e}")
        print("\nKiểm tra lại cấu hình database trong script này.")
    except Exception as e:
        print(f"✗ Lỗi: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("SCRIPT TẠO PASSWORD HASH VÀ CẬP NHẬT DATABASE")
    print("=" * 60)
    print()
    update_database()
