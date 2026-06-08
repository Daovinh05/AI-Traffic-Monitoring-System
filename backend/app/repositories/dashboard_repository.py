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


def list_drivers():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.id, t.ma_tai_xe AS code, t.ho_ten AS name,
                       t.so_dien_thoai AS phone,
                       t.so_giay_phep_lai_xe AS license_type,
                       5 AS experience, t.diem_danh_gia AS rating,
                       t.anh_dai_dien AS avatar,
                       IF(t.trang_thai_hoat_dong = 1,
                          'Đang làm việc', 'Đang nghỉ') AS status,
                       (SELECT COUNT(*) FROM canh_bao_vi_pham
                        WHERE id_tai_xe = t.id) AS violations,
                       156 AS total_trips
                FROM tai_xe t
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def list_routes():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id AS code, ten_tuyen AS name, mo_ta AS description,
                       COALESCE(start_lat, toa_do_lat) AS start_lat,
                       COALESCE(start_lng, toa_do_lng) AS start_lng,
                       COALESCE(end_lat, toa_do_lat) AS end_lat,
                       COALESCE(end_lng, toa_do_lng) AS end_lng,
                       distance, duration, vehicles, route_color AS color,
                       'Khu vực trung tâm' AS start, 'Tuyến cố định' AS end,
                       0 AS distance_old, 0 AS duration_old,
                       IF(trang_thai = 'active',
                          'Hoạt động', 'Ngừng hoạt động') AS status
                FROM tuyen_duong
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def list_route_path(route_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT latitude, longitude
                FROM tuyen_duong_path
                WHERE id_tuyen_duong = %s
                ORDER BY point_order ASC
                """,
                (route_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def list_recent_warnings(limit: int = 50):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.bien_so AS plate, t.ho_ten AS driver,
                       td.ten_tuyen AS location, c.loai_vi_pham AS type,
                       c.noi_dung_vi_pham AS typeLabel,
                       DATE_FORMAT(c.thoi_gian_vi_pham,
                                   '%%H:%%i %%d/%%m/%%Y') AS time,
                       IF(c.da_doc = 1, 'processed', 'pending') AS status,
                       v.duong_dan_file AS video
                FROM canh_bao_vi_pham c
                LEFT JOIN phuong_tien p ON c.id_phuong_tien = p.id
                LEFT JOIN tai_xe t ON c.id_tai_xe = t.id
                LEFT JOIN video_ghi_hinh v ON c.id_video_ghi_hinh = v.id
                LEFT JOIN tuyen_duong td ON p.id_tuyen_duong = td.id
                ORDER BY c.thoi_gian_vi_pham DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def list_recent_admin_alerts(limit: int = 50):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT tb.bien_so_xe AS plate, t.ho_ten AS driver,
                       t.so_dien_thoai AS phone,
                       tb.noi_dung_thong_bao AS content,
                       tb.muc_do_uu_tien AS priority,
                       IF(tb.muc_do_uu_tien = 'high', 'Cao',
                          IF(tb.muc_do_uu_tien = 'medium',
                             'Trung bình', 'Thấp')) AS priorityLabel,
                       DATE_FORMAT(tb.ngay_tao, '%%d/%%m/%%Y') AS date,
                       DATE_FORMAT(tb.ngay_tao, '%%H:%%i') AS time,
                       nd.ho_ten AS admin, 'Không xác định' AS location,
                       COALESCE(c.noi_dung_vi_pham,
                                'Vi phạm hệ thống') AS violationType,
                       IF(tb.da_doc = 1, 'processed', 'pending') AS status
                FROM thong_bao_admin tb
                LEFT JOIN phuong_tien p ON tb.bien_so_xe = p.bien_so
                LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
                LEFT JOIN nguoi_dung nd ON tb.id_admin = nd.id
                LEFT JOIN canh_bao_vi_pham c ON tb.id_vi_pham = c.id
                ORDER BY tb.ngay_tao DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
    finally:
        conn.close()
