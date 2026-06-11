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
               p.hinh_anh_xe as image, p.id_tai_xe AS driver_id,
               p.id_tuyen_duong AS route_id, t.ho_ten as driver_name,
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


def create_vehicle(
    plate: str,
    vehicle_type: str,
    image: str | None,
    driver_id: int | None,
    route_id: str | None,
    location: str,
    status: str,
    latitude: float,
    longitude: float,
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO phuong_tien
                    (bien_so, loai_xe, hinh_anh_xe, id_tai_xe,
                     id_tuyen_duong, vi_tri, trang_thai_hoat_dong,
                     toc_do_hien_tai, lat, lng)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, %s)
                """,
                (
                    plate,
                    vehicle_type,
                    image,
                    driver_id,
                    route_id,
                    location,
                    status,
                    latitude,
                    longitude,
                ),
            )
            vehicle_id = cur.lastrowid
        conn.commit()
        return vehicle_id
    finally:
        conn.close()


def get_vehicle(vehicle_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.id, p.bien_so AS plate, p.loai_xe AS type,
                       p.hinh_anh_xe AS image, p.id_tai_xe AS driver_id,
                       p.id_tuyen_duong AS route_id, p.vi_tri AS location,
                       p.trang_thai_hoat_dong AS status,
                       p.toc_do_hien_tai AS speed, p.lat, p.lng,
                       t.ho_ten AS driver_name, t.so_dien_thoai AS driver_phone,
                       td.ten_tuyen AS route_name
                FROM phuong_tien p
                LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
                LEFT JOIN tuyen_duong td ON p.id_tuyen_duong = td.id
                WHERE p.id = %s
                """,
                (vehicle_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def update_vehicle(
    vehicle_id: int,
    plate: str,
    vehicle_type: str,
    image: str | None,
    driver_id: int | None,
    route_id: str | None,
    location: str,
    status: str,
    latitude: float,
    longitude: float,
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE phuong_tien
                SET bien_so = %s, loai_xe = %s, hinh_anh_xe = %s,
                    id_tai_xe = %s, id_tuyen_duong = %s, vi_tri = %s,
                    trang_thai_hoat_dong = %s, lat = %s, lng = %s
                WHERE id = %s
                """,
                (
                    plate,
                    vehicle_type,
                    image,
                    driver_id,
                    route_id,
                    location,
                    status,
                    latitude,
                    longitude,
                    vehicle_id,
                ),
            )
            updated = cur.rowcount > 0
        conn.commit()
        return updated
    finally:
        conn.close()


def delete_vehicle(vehicle_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM phuong_tien WHERE id = %s", (vehicle_id,))
            deleted = cur.rowcount > 0
        conn.commit()
        return deleted
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
                       t.so_nam_kinh_nghiem AS experience,
                       t.tong_so_chuyen AS total_trips,
                       t.diem_danh_gia AS rating,
                       t.anh_dai_dien AS avatar,
                       IF(t.trang_thai_hoat_dong = 1,
                          'Đang làm việc', 'Đang nghỉ') AS status,
                       (SELECT COUNT(*) FROM canh_bao_vi_pham
                        WHERE id_tai_xe = t.id) AS violations,
                       (SELECT COUNT(*) FROM canh_bao_vi_pham
                        WHERE id_tai_xe = t.id
                          AND YEAR(thoi_gian_vi_pham) = YEAR(CURRENT_DATE)
                          AND MONTH(thoi_gian_vi_pham) = MONTH(CURRENT_DATE)
                       ) AS monthly_violations
                FROM tai_xe t
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_driver(driver_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.id, t.ma_tai_xe AS code, t.ho_ten AS name,
                       t.so_dien_thoai AS phone,
                       t.so_giay_phep_lai_xe AS license_type,
                       t.so_nam_kinh_nghiem AS experience,
                       t.tong_so_chuyen AS total_trips,
                       t.diem_danh_gia AS rating,
                       t.anh_dai_dien AS avatar,
                       IF(t.trang_thai_hoat_dong = 1,
                          'Đang làm việc', 'Đang nghỉ') AS status,
                       (SELECT COUNT(*) FROM canh_bao_vi_pham
                        WHERE id_tai_xe = t.id) AS violations,
                       (SELECT COUNT(*) FROM canh_bao_vi_pham
                        WHERE id_tai_xe = t.id
                          AND YEAR(thoi_gian_vi_pham) = YEAR(CURRENT_DATE)
                          AND MONTH(thoi_gian_vi_pham) = MONTH(CURRENT_DATE)
                       ) AS monthly_violations
                FROM tai_xe t
                WHERE t.id = %s
                """,
                (driver_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def create_driver(
    code,
    name,
    phone,
    license_number,
    experience,
    total_trips,
    avatar,
    rating,
    active,
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tai_xe
                    (ma_tai_xe, ho_ten, so_dien_thoai,
                     so_giay_phep_lai_xe, anh_dai_dien,
                     so_nam_kinh_nghiem, tong_so_chuyen,
                     diem_danh_gia, trang_thai_hoat_dong)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    code,
                    name,
                    phone,
                    license_number,
                    avatar,
                    experience,
                    total_trips,
                    rating,
                    active,
                ),
            )
            driver_id = cur.lastrowid
        conn.commit()
        return driver_id
    finally:
        conn.close()


def update_driver(
    driver_id,
    code,
    name,
    phone,
    license_number,
    experience,
    total_trips,
    avatar,
    rating,
    active,
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE tai_xe
                SET ma_tai_xe = %s, ho_ten = %s, so_dien_thoai = %s,
                    so_giay_phep_lai_xe = %s, anh_dai_dien = %s,
                    so_nam_kinh_nghiem = %s, tong_so_chuyen = %s,
                    diem_danh_gia = %s, trang_thai_hoat_dong = %s
                WHERE id = %s
                """,
                (
                    code,
                    name,
                    phone,
                    license_number,
                    avatar,
                    experience,
                    total_trips,
                    rating,
                    active,
                    driver_id,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def delete_driver(driver_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tai_xe WHERE id = %s", (driver_id,))
            deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    finally:
        conn.close()


def list_routes():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id AS code, ten_tuyen AS name, mo_ta AS description,
                       start_address, end_address,
                       COALESCE(start_lat, toa_do_lat) AS start_lat,
                       COALESCE(start_lng, toa_do_lng) AS start_lng,
                       COALESCE(end_lat, toa_do_lat) AS end_lat,
                       COALESCE(end_lng, toa_do_lng) AS end_lng,
                       distance, duration, vehicles, route_color AS color,
                       COALESCE(start_address, 'Chưa cập nhật địa chỉ') AS start,
                       COALESCE(end_address, 'Chưa cập nhật địa chỉ') AS end,
                       0 AS distance_old, 0 AS duration_old,
                       CASE trang_thai
                           WHEN 'active' THEN 'Hoạt động'
                           WHEN 'waiting' THEN 'Chờ triển khai'
                           ELSE 'Ngừng hoạt động'
                       END AS status
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
