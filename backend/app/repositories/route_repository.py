"""Route management persistence."""

from __future__ import annotations

from backend.app.db.database import get_db_connection


def list_routes():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, ten_tuyen, mo_ta, start_address, end_address,
                       start_lat, start_lng, end_lat, end_lng,
                       distance, duration, vehicles, route_color, toa_do_lat,
                       toa_do_lng, trang_thai
                FROM tuyen_duong
                ORDER BY ten_tuyen ASC
                """
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_route(route_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, ten_tuyen, mo_ta, start_address, end_address,
                       start_lat, start_lng, end_lat, end_lng,
                       toa_do_lat, toa_do_lng, trang_thai
                FROM tuyen_duong
                WHERE id = %s
                """,
                (route_id,),
            )
            return cur.fetchone()
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


def route_exists(route_id) -> bool:
    return get_route(route_id) is not None


def create_route(
    route_id,
    name,
    description,
    start_address,
    end_address,
    distance,
    duration,
    vehicles,
    color,
    status,
    path,
):
    conn = get_db_connection()
    try:
        start_lat, start_lng = path[0]
        end_lat, end_lng = path[-1]
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tuyen_duong
                (id, ten_tuyen, mo_ta, start_address, end_address,
                 start_lat, start_lng, end_lat, end_lng, distance,
                 duration, vehicles, route_color, trang_thai)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    route_id,
                    name,
                    description,
                    start_address,
                    end_address,
                    start_lat,
                    start_lng,
                    end_lat,
                    end_lng,
                    distance,
                    duration,
                    vehicles,
                    color,
                    status,
                ),
            )
            _insert_path(cur, route_id, path)
        conn.commit()
    finally:
        conn.close()


def update_route(
    route_id,
    name,
    description,
    start_address,
    end_address,
    distance,
    duration,
    vehicles,
    color,
    status,
    path,
):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if path:
                start_lat, start_lng = path[0]
                end_lat, end_lng = path[-1]
                cur.execute(
                    """
                    UPDATE tuyen_duong
                    SET ten_tuyen = %s, mo_ta = %s, start_address = %s,
                        end_address = %s, start_lat = %s, start_lng = %s,
                        end_lat = %s, end_lng = %s, distance = %s,
                        duration = %s, vehicles = %s, route_color = %s,
                        trang_thai = %s
                    WHERE id = %s
                    """,
                    (
                        name,
                        description,
                        start_address,
                        end_address,
                        start_lat,
                        start_lng,
                        end_lat,
                        end_lng,
                        distance,
                        duration,
                        vehicles,
                        color,
                        status,
                        route_id,
                    ),
                )
                cur.execute("DELETE FROM tuyen_duong_path WHERE id_tuyen_duong = %s", (route_id,))
                _insert_path(cur, route_id, path)
            else:
                cur.execute(
                    """
                    UPDATE tuyen_duong
                    SET ten_tuyen = %s, mo_ta = %s, start_address = %s,
                        end_address = %s, distance = %s, duration = %s,
                        vehicles = %s, route_color = %s, trang_thai = %s
                    WHERE id = %s
                    """,
                    (
                        name,
                        description,
                        start_address,
                        end_address,
                        distance,
                        duration,
                        vehicles,
                        color,
                        status,
                        route_id,
                    ),
                )
        conn.commit()
    finally:
        conn.close()


def delete_route(route_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tuyen_duong WHERE id = %s", (route_id,))
        conn.commit()
    finally:
        conn.close()


def _insert_path(cur, route_id, path):
    for index, (lat, lng) in enumerate(path, start=1):
        cur.execute(
            """
            INSERT INTO tuyen_duong_path (id_tuyen_duong, point_order, latitude, longitude)
            VALUES (%s, %s, %s, %s)
            """,
            (route_id, index, lat, lng),
        )
