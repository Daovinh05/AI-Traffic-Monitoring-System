"""Alert and admin warning persistence."""

from __future__ import annotations

from backend.app.db.database import get_db_connection


def count_driver_alerts(driver_id: int) -> int:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as total FROM canh_bao_vi_pham WHERE id_tai_xe = %s",
                (driver_id,),
            )
            return cur.fetchone()["total"]
    finally:
        conn.close()


def list_driver_alerts(driver_id: int, limit: int, offset: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.id, a.loai_vi_pham as type, a.noi_dung_vi_pham as message,
                       a.muc_do as level, a.thoi_gian_vi_pham as timestamp,
                       a.da_doc as is_read, v.bien_so as vehicle_plate,
                       d.ho_ten as driver_name, vid.duong_dan_file as video_path
                FROM canh_bao_vi_pham a
                LEFT JOIN phuong_tien v ON a.id_phuong_tien = v.id
                LEFT JOIN tai_xe d ON a.id_tai_xe = d.id
                LEFT JOIN video_ghi_hinh vid ON a.id_video_ghi_hinh = vid.id
                WHERE a.id_tai_xe = %s
                ORDER BY a.thoi_gian_vi_pham DESC
                LIMIT %s OFFSET %s
                """,
                (driver_id, limit, offset),
            )
            return cur.fetchall()
    finally:
        conn.close()


def count_all_alerts() -> int:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as total FROM canh_bao_vi_pham")
            return cur.fetchone()["total"]
    finally:
        conn.close()


def list_all_alerts(limit: int, offset: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.id, a.loai_vi_pham as type, a.noi_dung_vi_pham as message,
                       a.muc_do as level, a.thoi_gian_vi_pham as timestamp,
                       a.da_doc as is_read, v.bien_so as vehicle_plate,
                       d.ho_ten as driver_name, vid.duong_dan_file as video_path
                FROM canh_bao_vi_pham a
                LEFT JOIN phuong_tien v ON a.id_phuong_tien = v.id
                LEFT JOIN tai_xe d ON a.id_tai_xe = d.id
                LEFT JOIN video_ghi_hinh vid ON a.id_video_ghi_hinh = vid.id
                ORDER BY a.thoi_gian_vi_pham DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            return cur.fetchall()
    finally:
        conn.close()


def mark_alert_read(alert_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE canh_bao_vi_pham SET da_doc = 1 WHERE id = %s", (alert_id,))
        conn.commit()
    finally:
        conn.close()


def mark_admin_warning_read(warning_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE thong_bao_admin SET da_doc = 1, ngay_doc = NOW() WHERE id = %s",
                (warning_id,),
            )
        conn.commit()
    finally:
        conn.close()


def create_admin_warning(admin_id, alert_id, plate: str, content: str, priority: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO thong_bao_admin
                (id_admin, id_vi_pham, bien_so_xe, noi_dung_thong_bao,
                 muc_do_uu_tien, da_doc, ngay_tao)
                VALUES (%s, %s, %s, %s, %s, 0, NOW())
                """,
                (admin_id, alert_id, plate, content, priority),
            )
            warning_id = cur.lastrowid
        conn.commit()
        return warning_id
    finally:
        conn.close()
