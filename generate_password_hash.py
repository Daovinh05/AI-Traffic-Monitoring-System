#!/usr/bin/env python3
"""
Script tạo password hash cho admin và user
Chạy script này để lấy hash mới nhất
"""

from flask_bcrypt import Bcrypt
from flask import Flask

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Tạo password hash
admin_password = 'admin123'
user_password = 'user123'

admin_hash = bcrypt.generate_password_hash(admin_password).decode('utf-8')
user_hash = bcrypt.generate_password_hash(user_password).decode('utf-8')

print("=" * 60)
print("PASSWORD HASHES (copy vào database)")
print("=" * 60)
print(f"\nAdmin password: {admin_password}")
print(f"Admin hash: {admin_hash}\n")
print(f"User password: {user_password}")
print(f"User hash: {user_hash}\n")
print("=" * 60)

# SQL để update
print("\nSQL ĐỂ CHẠY TRONG phpMyAdmin:")
print("=" * 60)
print(f"""
UPDATE users SET password = '{admin_hash}' WHERE username = 'admin';
UPDATE users SET password = '{user_hash}' WHERE username = 'user';
""")
print("=" * 60)
