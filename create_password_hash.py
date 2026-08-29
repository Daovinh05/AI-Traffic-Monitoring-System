#!/usr/bin/env python3
"""
Script tạo password hash đơn giản
Không cần Flask, chỉ cần bcrypt
"""

import bcrypt

# Tạo password hash
admin_password = 'admin123'
user_password = 'user123'

admin_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
user_hash = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

print("=" * 70)
print("PASSWORD HASHES MỚI")
print("=" * 70)
print(f"\nAdmin password: {admin_password}")
print(f"Admin hash: {admin_hash}\n")
print(f"User password: {user_password}")
print(f"User hash: {user_hash}\n")
print("=" * 70)

# SQL để update - CHO DATABASE TIẾNG VIỆT
print("\nSQL ĐỂ CHẠY TRONG phpMyAdmin (DATABASE TIẾNG VIỆT):")
print("=" * 70)
print(f"""
UPDATE nguoi_dung SET mat_khau = '{admin_hash}' WHERE ten_dang_nhap = 'admin';
UPDATE nguoi_dung SET mat_khau = '{user_hash}' WHERE ten_dang_nhap = 'user';
UPDATE nguoi_dung SET mat_khau = '{user_hash}' WHERE ten_dang_nhap = 'user1';
UPDATE nguoi_dung SET mat_khau = '{user_hash}' WHERE ten_dang_nhap = 'user2';
UPDATE nguoi_dung SET mat_khau = '{user_hash}' WHERE ten_dang_nhap = 'user3';
UPDATE nguoi_dung SET mat_khau = '{user_hash}' WHERE ten_dang_nhap = 'user4';
UPDATE nguoi_dung SET mat_khau = '{user_hash}' WHERE ten_dang_nhap = 'user5';
UPDATE nguoi_dung SET mat_khau = '{user_hash}' WHERE ten_dang_nhap = 'user6';
UPDATE nguoi_dung SET mat_khau = '{user_hash}' WHERE ten_dang_nhap = 'user7';
UPDATE nguoi_dung SET mat_khau = '{user_hash}' WHERE ten_dang_nhap = 'user8';
""")
print("=" * 70)

# SQL để update - CHO DATABASE TIẾNG ANH (cũ)
print("\nSQL ĐỂ CHẠY TRONG phpMyAdmin (DATABASE TIẾNG ANH - CŨ):")
print("=" * 70)
print(f"""
UPDATE users SET password = '{admin_hash}' WHERE username = 'admin';
UPDATE users SET password = '{user_hash}' WHERE username = 'user';
""")
print("=" * 70)
