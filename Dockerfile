# 🍎 Build cho arm64 (M1/M2/M3 Mac) + amd64 (Intel/Linux)
FROM python:3.10-slim-bullseye

# System packages required for OpenCV, audio, building some Python extensions
# Tối ưu cho M1 Mac: sử dụng native arm64 build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    pkg-config \
    ffmpeg \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgl1 \
    libsndfile1 \
    libasound2-dev \
    libpulse-dev \
    pulseaudio \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency list first to leverage Docker cache
COPY requirements.txt /app/requirements.txt

# Install Python packages
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy application code
COPY . /app

# Default FLASK app (override with -e FLASK_APP=...) and port
ENV FLASK_APP=py/Web/all_tong.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# Default command: run Flask development server. For production, replace with gunicorn or uvicorn as needed.
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
