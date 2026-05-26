"""Camera and video metadata persistence."""

from __future__ import annotations

from backend.app.db.database import get_db_connection


def list_active_vehicle_cameras(vehicle_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT cx.vi_tri, cx.ten_camera, cx.video_file, p.bien_so,
                       t.ho_ten as driver_name
                FROM camera_xe cx
                JOIN phuong_tien p ON cx.id_phuong_tien = p.id
                LEFT JOIN tai_xe t ON p.id_tai_xe = t.id
                WHERE cx.id_phuong_tien = %s AND cx.trang_thai = 1
                ORDER BY FIELD(cx.vi_tri, 'tai_xe', 'truoc', 'hanh_khach', 'lui')
                """,
                (vehicle_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()
