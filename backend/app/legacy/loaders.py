"""Lazy loaders for legacy modules.

The original AI modules load heavy dependencies at import time. Keep imports
lazy so the new architecture can be imported without immediately loading
YOLO/dlib/pygame models.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
LEGACY_WEB_DIR = ROOT_DIR / "py" / "Web"


def ensure_legacy_path() -> None:
    if str(LEGACY_WEB_DIR) not in sys.path:
        sys.path.insert(0, str(LEGACY_WEB_DIR))


def load_models_module():
    ensure_legacy_path()
    return importlib.import_module("models")


def load_mqtt_client_module():
    ensure_legacy_path()
    return importlib.import_module("mqtt_client")
