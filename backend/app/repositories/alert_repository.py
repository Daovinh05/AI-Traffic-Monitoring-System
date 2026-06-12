"""Alert and admin warning persistence."""

from __future__ import annotations

from backend.app.db.database import get_db_connection


def create_ai_alert(alert_type: str, message: str, level: str, vehicle_id=None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            driver_id = None
            plate = "N/A"
            driver_name = "N/A"

            if vehicle_id:
                cur.execute(
                    """
                    SELECT p.bien_so, t.id AS id_tai_xe, t.ho_ten
                    FROM phuong_tien p
                    LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
                    WHERE p.id = %s
                    """,
                    (vehicle_id,),
                )
                vehicle = cur.fetchone()
                if vehicle:
                    plate = vehicle["bien_so"]
                    driver_id = vehicle["id_tai_xe"]
                    driver_name = vehicle["ho_ten"]

            cur.execute(
                """
                INSERT INTO canh_bao_vi_pham
                (loai_vi_pham, noi_dung_vi_pham, muc_do, thoi_gian_vi_pham,
                 id_phuong_tien, id_tai_xe)
                VALUES (%s, %s, %s, NOW(), %s, %s)
                """,
                (alert_type, message, level, vehicle_id, driver_id),
            )
            alert_id = cur.lastrowid

        conn.commit()
        return {
            "id": alert_id,
            "plate": plate,
            "driver_name": driver_name,
        }
    finally:
        conn.close()


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
                       v.loai_xe as vehicle_type,
                       d.ho_ten as driver_name,
                       COALESCE(
                           vid.duong_dan_file,
                           (
                               SELECT recorded.duong_dan_file
                               FROM video_ghi_hinh recorded
                               WHERE a.thoi_gian_vi_pham BETWEEN
                                   DATE_SUB(recorded.thoi_gian_bat_dau, INTERVAL 10 SECOND)
                                   AND COALESCE(recorded.thoi_gian_ket_thuc, NOW())
                               ORDER BY ABS(
                                   TIMESTAMPDIFF(
                                       SECOND,
                                       recorded.thoi_gian_bat_dau,
                                       a.thoi_gian_vi_pham
                                   )
                               )
                               LIMIT 1
                           )
                       ) as video_path
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


def count_all_alerts(plate: str = "") -> int:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if plate:
                cur.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM canh_bao_vi_pham a
                    LEFT JOIN phuong_tien v ON a.id_phuong_tien = v.id
                    WHERE UPPER(v.bien_so) LIKE UPPER(%s)
                    """,
                    (f"%{plate}%",),
                )
            else:
                cur.execute("SELECT COUNT(*) as total FROM canh_bao_vi_pham")
            return cur.fetchone()["total"]
    finally:
        conn.close()


def list_all_alerts(limit: int, offset: int, plate: str = ""):
    where = "WHERE UPPER(v.bien_so) LIKE UPPER(%s)" if plate else ""
    params = [f"%{plate}%"] if plate else []
    params.extend((limit, offset))

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT a.id, a.loai_vi_pham as type, a.noi_dung_vi_pham as message,
                       a.muc_do as level, a.thoi_gian_vi_pham as timestamp,
                       a.da_doc as is_read, v.bien_so as vehicle_plate,
                       v.loai_xe as vehicle_type,
                       d.ho_ten as driver_name,
                       COALESCE(
                           vid.duong_dan_file,
                           (
                               SELECT recorded.duong_dan_file
                               FROM video_ghi_hinh recorded
                               WHERE a.thoi_gian_vi_pham BETWEEN
                                   DATE_SUB(recorded.thoi_gian_bat_dau, INTERVAL 10 SECOND)
                                   AND COALESCE(recorded.thoi_gian_ket_thuc, NOW())
                               ORDER BY ABS(
                                   TIMESTAMPDIFF(
                                       SECOND,
                                       recorded.thoi_gian_bat_dau,
                                       a.thoi_gian_vi_pham
                                   )
                               )
                               LIMIT 1
                           )
                       ) as video_path
                FROM canh_bao_vi_pham a
                LEFT JOIN phuong_tien v ON a.id_phuong_tien = v.id
                LEFT JOIN tai_xe d ON a.id_tai_xe = d.id
                LEFT JOIN video_ghi_hinh vid ON a.id_video_ghi_hinh = vid.id
                {where}
                ORDER BY a.thoi_gian_vi_pham DESC
                LIMIT %s OFFSET %s
                """,
                tuple(params),
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


def acknowledge_driver_admin_warning(warning_id: int, driver_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT w.id_vi_pham AS alert_id
                FROM thong_bao_admin w
                INNER JOIN phuong_tien p ON w.bien_so_xe = p.bien_so
                WHERE w.id = %s AND p.id_tai_xe = %s
                FOR UPDATE
                """,
                (warning_id, driver_id),
            )
            warning = cur.fetchone()
            if not warning:
                conn.rollback()
                return None

            cur.execute(
                """
                UPDATE thong_bao_admin
                SET da_doc = 1, ngay_doc = COALESCE(ngay_doc, NOW())
                WHERE id = %s
                """,
                (warning_id,),
            )

            alert_id = warning["alert_id"]
            if alert_id:
                cur.execute(
                    """
                    UPDATE canh_bao_vi_pham
                    SET da_doc = 1
                    WHERE id = %s AND id_tai_xe = %s
                    """,
                    (alert_id, driver_id),
                )
        conn.commit()
        return {"warning_id": warning_id, "alert_id": alert_id}
    except Exception:
        conn.rollback()
        raise
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


def get_admin_warning(warning_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT w.id, w.bien_so_xe AS vehicle_plate,
                       p.loai_xe AS vehicle_type,
                       w.noi_dung_thong_bao AS message,
                       w.muc_do_uu_tien AS priority, w.da_doc AS is_read,
                       w.ngay_tao AS created_at, u.ho_ten AS admin_name,
                       t.id AS driver_id, t.ho_ten AS driver_name,
                       c.noi_dung_vi_pham AS violationType
                FROM thong_bao_admin w
                LEFT JOIN phuong_tien p ON w.bien_so_xe = p.bien_so
                LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
                LEFT JOIN nguoi_dung u ON w.id_admin = u.id
                LEFT JOIN canh_bao_vi_pham c ON w.id_vi_pham = c.id
                WHERE w.id = %s
                """,
                (warning_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def count_admin_warnings(driver_id=None, plate: str = ""):
    conditions = []
    params = []
    if driver_id is not None:
        conditions.append("p.id_tai_xe = %s")
        params.append(driver_id)
    if plate:
        conditions.append("UPPER(w.bien_so_xe) LIKE UPPER(%s)")
        params.append(f"%{plate}%")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM thong_bao_admin w
                LEFT JOIN phuong_tien p ON w.bien_so_xe = p.bien_so
                {where}
                """,
                tuple(params),
            )
            return cur.fetchone()["total"]
    finally:
        conn.close()


def list_admin_warnings(limit: int, offset: int, driver_id=None, plate: str = ""):
    conditions = []
    params = []
    if driver_id is not None:
        conditions.append("p.id_tai_xe = %s")
        params.append(driver_id)
    if plate:
        conditions.append("UPPER(w.bien_so_xe) LIKE UPPER(%s)")
        params.append(f"%{plate}%")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.extend((limit, offset))

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT w.id, w.bien_so_xe AS vehicle_plate,
                       p.loai_xe AS vehicle_type,
                       w.noi_dung_thong_bao AS message,
                       w.muc_do_uu_tien AS priority, w.da_doc AS is_read,
                       w.ngay_tao AS created_at, u.ho_ten AS admin_name,
                       t.ho_ten AS driver_name,
                       c.noi_dung_vi_pham AS violationType
                FROM thong_bao_admin w
                LEFT JOIN phuong_tien p ON w.bien_so_xe = p.bien_so
                LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
                LEFT JOIN nguoi_dung u ON w.id_admin = u.id
                LEFT JOIN canh_bao_vi_pham c ON w.id_vi_pham = c.id
                {where}
                ORDER BY w.ngay_tao DESC
                LIMIT %s OFFSET %s
                """,
                tuple(params),
            )
            return cur.fetchall()
    finally:
        conn.close()
