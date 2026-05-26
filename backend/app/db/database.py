"""Database connection adapter for repositories."""

from __future__ import annotations

import pymysql

from backend.app.core.config import settings


def get_db_connection():
    return pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_db,
        cursorclass=pymysql.cursors.DictCursor,
        charset="utf8mb4",
    )
