"""Application factory and executable entrypoint for the backend."""

from __future__ import annotations

import os
import threading
from pathlib import Path

from flask import Flask

from backend.app.api import register_app_routes, validate_routes
from backend.app.core.config import Settings, apply_to_flask, settings
from backend.app.extensions import init_extensions


ROOT_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = Path(os.environ.get("AI_TRAFFIC_CACHE_DIR", "/private/tmp/ai-traffic-cache"))

_workers_lock = threading.Lock()
_workers_started = False


def _configure_runtime_paths() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))
    os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR / "xdg"))
    os.environ.setdefault("YOLO_CONFIG_DIR", str(CACHE_DIR / "ultralytics"))
    os.environ.setdefault("ULTRALYTICS_CONFIG_DIR", str(CACHE_DIR / "ultralytics"))


def create_app(app_settings: Settings = settings) -> Flask:
    """Create the modular Flask API application."""
    _configure_runtime_paths()

    app = Flask(__name__, static_folder=None)
    apply_to_flask(app, app_settings)
    init_extensions(app)

    register_app_routes(app)

    missing = validate_routes(app)
    if missing:
        names = ", ".join(f"{group}:{route.endpoint}" for group, route in missing)
        raise RuntimeError(f"Backend route registration is incomplete: {names}")

    return app


app = create_app()


def _run_ai_workers() -> None:
    try:
        from backend.app.ai import runtime

        runtime.init_app()
        threading.Thread(
            target=runtime.reset_temporary_counts,
            daemon=True,
            name="reset-temporary-counts",
        ).start()
        print("[AI] Runtime initialized successfully")
    except Exception as exc:
        print(f"[AI] Runtime initialization failed; API remains available: {exc}")


def start_background_workers(flask_app: Flask = app) -> None:
    """Start AI/video workers once without blocking the HTTP API."""
    del flask_app
    global _workers_started

    with _workers_lock:
        if _workers_started:
            return
        _workers_started = True
        threading.Thread(
            target=_run_ai_workers,
            daemon=True,
            name="ai-runtime-init",
        ).start()


def main() -> None:
    start_background_workers(app)
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


if __name__ == "__main__":
    main()
