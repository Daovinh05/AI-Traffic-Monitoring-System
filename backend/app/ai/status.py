"""AI runtime readiness and asset validation."""

from __future__ import annotations

import threading
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
ASSET_DIR = ROOT_DIR / "backend" / "assets"

REQUIRED_ASSETS = (
    "shape_predictor_68_face_landmarks.dat",
    "weights/yolov8n.pt",
    "weights/day_an_toan.pt",
    "weights/bien_bao.pt",
    "weights/lech_lan.pt",
    "weights/vat_can.pt",
    "sounds/nham_mat.wav",
    "sounds/ngap_ngu.wav",
    "sounds/not_phone.wav",
    "sounds/seatbelt_alert.wav",
    "sounds/chuylaixe.wav",
    "sounds/chu_y_bien_bao.wav",
    "sounds/tay_lai_xe.wav",
    "sounds/lech_lan.wav",
    "sounds/va_cham.wav",
    "sounds/di_cham_lai.wav",
    "videos/ha_noi.mp4",
    "videos/ha_dong.mp4",
    "videos/thanh_xuan.mp4",
    "videos/ngatuso.mp4",
    "videos/bien_bao.mp4",
    "videos/lech_lan.mp4",
    "videos/ca_bin.mp4",
)

_lock = threading.Lock()
_state = {
    "enabled": False,
    "ready": False,
    "loading": False,
    "message": "AI runtime is disabled",
    "missing_assets": [],
}


def missing_assets() -> list[str]:
    return [
        relative_path
        for relative_path in REQUIRED_ASSETS
        if not (ASSET_DIR / relative_path).is_file()
    ]


def update(**values) -> None:
    with _lock:
        _state.update(values)


def snapshot() -> dict:
    with _lock:
        return {
            **_state,
            "missing_assets": list(_state["missing_assets"]),
        }
