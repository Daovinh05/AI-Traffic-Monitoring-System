"""Main backend entrypoint.

This module is the new architectural entrypoint. It intentionally mounts the
existing Flask application from ``py/Web/drive_auth.py`` so all current pages,
static assets, APIs, and video streams keep the same behavior and appearance.
Feature code can now be moved from the legacy module into ``api/``,
``services/``, ``repositories/``, and ``ai/`` one slice at a time.
"""

from __future__ import annotations

import sys
import threading
import os
from pathlib import Path

from .core.config import apply_to_flask, settings


ROOT_DIR = Path(__file__).resolve().parents[2]
LEGACY_WEB_DIR = ROOT_DIR / "py" / "Web"
CACHE_DIR = Path(os.environ.get("AI_TRAFFIC_CACHE_DIR", "/private/tmp/ai-traffic-cache"))

CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR / "xdg"))
os.environ.setdefault("YOLO_CONFIG_DIR", str(CACHE_DIR / "ultralytics"))
os.environ.setdefault("ULTRALYTICS_CONFIG_DIR", str(CACHE_DIR / "ultralytics"))

if str(LEGACY_WEB_DIR) not in sys.path:
    sys.path.insert(0, str(LEGACY_WEB_DIR))

import drive_auth as legacy_app_module  # noqa: E402


def create_app():
    app = legacy_app_module.app
    apply_to_flask(app)
    return app


app = create_app()


def start_background_workers() -> None:
    """Start legacy background workers used by AI/video monitoring."""
    legacy_app_module.init_app()
    threading.Thread(
        target=legacy_app_module.reset_temporary_counts,
        daemon=True,
        name="reset-temporary-counts",
    ).start()


if __name__ == "__main__":
    start_background_workers()
    print("=" * 70)
    print("AI TRAFFIC MONITORING SYSTEM - MODULAR BACKEND")
    print("=" * 70)
    print(f"URL: http://localhost:{settings.port}/login")
    print("=" * 70)
    app.run(
        debug=settings.debug,
        host="0.0.0.0",
        port=settings.port,
        use_reloader=False,
    )
