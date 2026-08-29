"""Recorded-video metadata persistence."""

from __future__ import annotations

from datetime import timedelta

from backend.app.db.database import get_db_connection


def save_recording(
    camera_id,
    filename,
    web_path,
    started_at,
    ended_at,
    file_size,
    vehicle_id=None,
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO video_ghi_hinh
                (id_camera, ten_file_video, duong_dan_file, thoi_gian_bat_dau,
                 thoi_gian_ket_thuc, kich_thuoc_file)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    camera_id,
                    filename,
                    web_path,
                    started_at,
                    ended_at,
                    file_size,
                ),
            )
            video_id = cur.lastrowid
            if vehicle_id:
                cur.execute(
                    """
                    UPDATE canh_bao_vi_pham
                    SET id_video_ghi_hinh = %s
                    WHERE id_phuong_tien = %s
                      AND thoi_gian_vi_pham BETWEEN %s AND %s
                    """,
                    (
                        video_id,
                        vehicle_id,
                        started_at - timedelta(seconds=10),
                        ended_at,
                    ),
                )
        conn.commit()
        return video_id
    finally:
        conn.close()
