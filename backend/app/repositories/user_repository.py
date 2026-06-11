"""User, driver, and vehicle lookups."""

from __future__ import annotations

from backend.app.db.database import get_db_connection


def find_user_by_username(username: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, ten_dang_nhap as username, mat_khau as password,
                       vai_tro as role, ho_ten as full_name,
                       trang_thai_hoat_dong as is_active
                FROM nguoi_dung
                WHERE ten_dang_nhap = %s
                """,
                (username,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def find_user_by_id(user_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, ten_dang_nhap AS username, mat_khau AS password,
                       vai_tro AS role, ho_ten AS full_name,
                       trang_thai_hoat_dong AS is_active
                FROM nguoi_dung
                WHERE id = %s
                """,
                (user_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def find_driver_by_user_id(user_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM tai_xe WHERE id_nguoi_dung = %s", (user_id,))
            return cur.fetchone()
    finally:
        conn.close()


def find_driver_profile_by_user_id(user_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, ma_tai_xe AS code, ho_ten AS name,
                       so_dien_thoai AS phone,
                       so_giay_phep_lai_xe AS license_number,
                       anh_dai_dien AS avatar,
                       IF(trang_thai_hoat_dong = 1,
                          'Đang làm việc', 'Đang nghỉ') AS status
                FROM tai_xe
                WHERE id_nguoi_dung = %s
                """,
                (user_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def find_vehicle_by_driver_id(driver_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM phuong_tien WHERE id_tai_xe = %s", (driver_id,))
            return cur.fetchone()
    finally:
        conn.close()


def update_user_profile(
    user_id: int,
    full_name: str,
    phone: str,
    license_number: str,
    avatar: str | None,
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE nguoi_dung SET ho_ten = %s WHERE id = %s",
                (full_name, user_id),
            )
            cur.execute(
                """
                UPDATE tai_xe
                SET ho_ten = %s, so_dien_thoai = %s,
                    so_giay_phep_lai_xe = %s, anh_dai_dien = %s
                WHERE id_nguoi_dung = %s
                """,
                (full_name, phone, license_number, avatar, user_id),
            )
        conn.commit()
    finally:
        conn.close()


def update_user_password(user_id: int, password_hash: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE nguoi_dung SET mat_khau = %s WHERE id = %s",
                (password_hash, user_id),
            )
        conn.commit()
    finally:
        conn.close()
