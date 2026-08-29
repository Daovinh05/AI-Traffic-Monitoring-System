"""Database queries used to build chatbot context."""

from __future__ import annotations

from backend.app.db.database import get_db_connection


def find_vehicle_by_plate(plate: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.bien_so, t.ho_ten, td.ten_tuyen
                FROM phuong_tien p
                LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
                LEFT JOIN tuyen_duong td ON p.id_tuyen_duong = td.id
                WHERE p.bien_so = %s
                """,
                (plate,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def list_vehicle_context(limit: int = 10):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.bien_so AS plate, t.ho_ten AS driver,
                       td.ten_tuyen AS location,
                       p.trang_thai_hoat_dong AS status,
                       p.toc_do_hien_tai AS speed
                FROM phuong_tien p
                LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
                LEFT JOIN tuyen_duong td ON p.id_tuyen_duong = td.id
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
    finally:
        conn.close()
