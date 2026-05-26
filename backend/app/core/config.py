"""Configuration helpers for the Flask backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class Settings:
    secret_key: str
    session_type: str
    session_permanent: bool
    session_lifetime_hours: int
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_db: str
    port: int
    debug: bool

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            secret_key=os.environ.get("SECRET_KEY", "ai-traffic-dev-secret"),
            session_type=os.environ.get("SESSION_TYPE", "filesystem"),
            session_permanent=os.environ.get("SESSION_PERMANENT", "true").lower() == "true",
            session_lifetime_hours=int(os.environ.get("SESSION_LIFETIME_HOURS", "24")),
            mysql_host=os.environ.get("MYSQL_HOST", "localhost"),
            mysql_port=int(os.environ.get("MYSQL_PORT", "3306")),
            mysql_user=os.environ.get("MYSQL_USER", "root"),
            mysql_password=os.environ.get("MYSQL_PASSWORD", ""),
            mysql_db=os.environ.get("MYSQL_DB", "giam_sat"),
            port=int(os.environ.get("PORT", "5001")),
            debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
        )


settings = Settings.from_env()


def apply_to_flask(app, app_settings: Settings = settings):
    app.secret_key = app_settings.secret_key
    app.config["SESSION_TYPE"] = app_settings.session_type
    app.config["SESSION_PERMANENT"] = app_settings.session_permanent
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
        hours=app_settings.session_lifetime_hours
    )
    app.config["MYSQL_HOST"] = app_settings.mysql_host
    app.config["MYSQL_PORT"] = app_settings.mysql_port
    app.config["MYSQL_USER"] = app_settings.mysql_user
    app.config["MYSQL_PASSWORD"] = app_settings.mysql_password
    app.config["MYSQL_DB"] = app_settings.mysql_db
    return app
