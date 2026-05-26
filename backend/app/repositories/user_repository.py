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


def find_driver_by_user_id(user_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM tai_xe WHERE id_nguoi_dung = %s", (user_id,))
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
