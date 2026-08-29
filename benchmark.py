#!/usr/bin/env python3
"""Benchmark AI pipeline: run N frames, capture timing output."""
import os, sys, io, contextlib, traceback

os.environ["DRIVER_VIDEO_SOURCE"] = "backend/assets/videos/ca_bin.mp4"
_cache = "/tmp/ai-cache"
os.environ.setdefault("MPLCONFIGDIR", f"{_cache}/matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", f"{_cache}/xdg")
os.environ.setdefault("YOLO_CONFIG_DIR", f"{_cache}/ultralytics")
os.environ.setdefault("ULTRALYTICS_CONFIG_DIR", f"{_cache}/ultralytics")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.ai import runtime

N_FRAMES = 500

print(f"Running benchmark: {N_FRAMES} frames...", flush=True)

# Monkey-patch the error handler to show full traceback
original_monitor = runtime.driver_monitor

import numpy as np
# Fix: ensure numpy < 2 compatibility for dlib
if np.__version__.startswith("2"):
    print(f"WARNING: numpy {np.__version__} may cause issues with dlib")

stream = runtime.driver_monitor(vehicle_id=None)

import time
last_log = time.time()
for i, frame_data in enumerate(stream):
    if i % 100 == 0:
        now = time.time()
        print(f"  Processed {i} frames ({100/(now-last_log):.1f} fps avg)", flush=True)
        last_log = now
    if i >= N_FRAMES - 1:
        runtime.active_video_stream = None
        break

# Consume remaining to get final print
try:
    for _ in stream:
        pass
except:
    pass
