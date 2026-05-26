"""Dashboard persistence queries."""

from __future__ import annotations

from backend.app.db.database import get_db_connection


def list_vehicle_statuses():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT trang_thai_hoat_dong as status FROM phuong_tien")
            return cur.fetchall()
    finally:
        conn.close()


def list_dashboard_vehicles(limit: int | None = None, offset: int = 0):
    sql = """
        SELECT p.id, p.bien_so as plate_number, p.loai_xe as type,
               p.hinh_anh_xe as image, t.ho_ten as driver_name,
               t.so_dien_thoai as phone, t.diem_danh_gia as score,
               t.anh_dai_dien as driver_image, td.ten_tuyen as location,
               p.vi_tri as vi_tri, p.trang_thai_hoat_dong as status,
               p.toc_do_hien_tai as speed, p.lat, p.lng,
               (SELECT COUNT(*) FROM canh_bao_vi_pham
                WHERE id_phuong_tien = p.id AND da_doc = 0) as violations_count
        FROM phuong_tien p
        LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
        LEFT JOIN tuyen_duong td ON p.id_tuyen_duong = td.id
        ORDER BY p.id ASC
    """
    params = ()
    if limit is not None:
        sql += " LIMIT %s OFFSET %s"
        params = (limit, offset)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()
