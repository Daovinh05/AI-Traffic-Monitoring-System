# Multi-platform Dockerfile for AI Traffic Monitoring System
# Supports both arm64 (M1/M2/M3 Mac) and amd64 (Intel/Linux)

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for OpenCV, dlib, mediapipe, and audio
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    pkg-config \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgtk-3-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libopenblas-dev \
    liblapack-dev \
    libblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Set CMake policy minimum to avoid version conflicts with dlib
ENV CMAKE_POLICY_VERSION_MINIMUM=3.5

# Set SDL audio driver to dummy (required for headless Docker)
ENV SDL_AUDIODRIVER=dummy

# Copy requirements first for better Docker caching
COPY requirements.txt /app/requirements.txt

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy application code (excluding ignored files via .dockerignore)
COPY . /app

# Set environment variables
ENV FLASK_APP=py/Web/all_tong.py
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Expose Flask port
EXPOSE 5000

# Default command to run Flask development server
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
