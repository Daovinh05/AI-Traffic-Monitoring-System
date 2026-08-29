# 🐳 Hướng Dẫn Chạy AI Traffic Monitoring System Với Docker

## 🚀 Chạy Nhanh (Quick Start)

```bash
# Bước 1: Chuyển đến thư mục project
cd /Users/vinhdv/Documents/Clone/AI-Traffic-Monitoring-System

# Bước 2: Build và chạy (lần đầu mất 10-30 phút)
docker compose up --build

# Bước 3: Mở browser và truy cập
# 👉 http://localhost:5001
```

---

## 📋 Mục Lục

- [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
- [Cài Đặt](#cài-đặt)
- [Các Lệnh Cơ Bản](#các-lệnh-cơ-bản)
- [Cấu Hình](#cấu-hình)
- [Xử Lý Lỗi](#xử-lý-lỗi)
- [Lưu Ý Quan Trọng](#lưu-ý-quan-trọng)

---

## 🖥️ Yêu Cầu Hệ Thống

| Thành phần | Yêu cầu |
|------------|---------|
| **Docker** | Docker Desktop 4.0+ |
| **RAM** | Tối thiểu 4GB (khuyến nghị 8GB+) |
| **CPU** | Intel hoặc Apple Silicon (M1/M2/M3) |
| **Dung lượng** | ~5GB cho image và container |

### Kiểm tra Docker đã cài chưa:

```bash
docker --version
docker compose version
```

### Cài Docker Desktop:

- **Mac M1/M2/M3**: https://desktop.docker.com/mac/main/arm64/Docker.dmg
- **Mac Intel**: https://desktop.docker.com/mac/main/amd64/Docker.dmg
- **Windows**: https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe

---

## 📦 Cài Đặt

### Bước 1: Chuẩn bị

Đảm bảo các file model đã có trong `py/weights/`:

```bash
ls py/weights/
# Phải có ít nhất 1 file .pt (best.pt, yolov8n.pt, ...)
```

### Bước 2: Build Image

```bash
docker compose build
```

**Thời gian dự kiến:**
- Lần đầu: 15-30 phút (tùy tốc độ mạng)
- Lần sau: 1-2 phút (do cache)

### Bước 3: Chạy Container

```bash
# Chạy và xem logs
docker compose up

# HOẶC chạy nền (không thấy logs)
docker compose up -d
```

### Bước 4: Truy Cập Ứng Dụng

Mở browser và vào: **http://localhost:5001**

---

## ⌨️ Các Lệnh Cơ Bản

| Lệnh | Mô tả |
|------|-------|
| `docker compose up --build` | Build và chạy |
| `docker compose up -d` | Chạy nền (detached) |
| `docker compose down` | Dừng và xóa container |
| `docker compose logs -f` | Xem logs |
| `docker compose ps` | Xem container đang chạy |
| `docker compose exec ai-traffic-monitor bash` | Truy cập shell trong container |
| `docker compose build --no-cache` | Build lại từ đầu |
| `docker compose down --rmi all` | Xóa cả container và image |

---

## ⚙️ Cấu Hình

### Đổi Port

Sửa file `docker-compose.yml`:

```yaml
ports:
  - "8080:5000"  # Đổi thành port bạn muốn
```

Sau đó chạy lại:
```bash
docker compose up -d
```

### Chạy File Flask Khác

Sửa `FLASK_APP` trong `docker-compose.yml`:

```yaml
environment:
  - FLASK_APP=py/Web/drive.py  # Thay đổi file chạy
```

Build lại:
```bash
docker compose up --build
```

### Tăng RAM Cho Container

Sửa `docker-compose.yml`, thêm:

```yaml
services:
  ai-traffic-monitor:
    deploy:
      resources:
        limits:
          memory: 4G
```

---

## 🔧 Xử Lý Lỗi

### ❌ Lỗi: "Cannot connect to the Docker daemon"

**Nguyên nhân:** Docker Desktop chưa chạy.

**Giải pháp:**
1. Mở Docker Desktop từ Applications
2. Đợi đến khi biểu tượng Docker ngừng nhấp nháy
3. Chạy lại lệnh

---

### ❌ Lỗi: "Bind for 0.0.0.0:5000 failed: port is already allocated"

**Nguyên nhân:** Port 5000 hoặc 5001 đã được dùng.

**Giải pháp:**
```bash
# Kiểm tra port đang dùng
lsof -i :5001

# Đổi port trong docker-compose.yml
ports:
  - "5002:5000"
```

---

### ❌ Lỗi: "No such file or directory: 'py/weights/*.pt'"

**Nguyên nhân:** Thiếu file model YOLO.

**Giải pháp:**
```bash
# Kiểm tra thư mục weights
ls -la py/weights/

# Nếu trống, cần tải model về
# (Liên hệ admin hoặc tải từ Hugging Face)
```

---

### ❌ Lỗi: "ModuleNotFoundError: No module named 'xxx'"

**Nguyên nhân:** Thiếu package trong requirements.txt.

**Giải pháp:**
```bash
# Thêm package vào requirements.txt
echo "tên-package==version" >> requirements.txt

# Build lại
docker compose build --no-cache
docker compose up
```

---

### ❌ Container crash liên tục

**Kiểm tra logs:**
```bash
docker compose logs ai-traffic-monitor | tail -50
```

**Truy cập container để debug:**
```bash
docker compose run --rm ai-traffic-monitor bash
# Trong container:
python -c "import torch; print(torch.__version__)"
```

---

### ❌ Build bị treo hoặc lỗi giữa chừng

**Giải pháp:**
```bash
# Tăng resource trong Docker Desktop:
# 1. Mở Docker Desktop Settings
# 2. Vào Resources
# 3. Tăng RAM lên 4GB+, CPU lên 4 cores

# Build lại với no-cache
docker compose build --no-cache
```

---

## ⚠️ Lưu Ý Quan Trọng

### 1. Webcam Không Hoạt Động Trên Mac

**Lý do:** Docker Desktop trên macOS không thể truy cập webcam do hạn chế bảo mật.

**Giải pháp:**
- ✅ Dùng video file có sẵn trong `py/video_input/`
- ✅ Hoặc chạy native (không dùng Docker):
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  flask --app=py/Web/all_tong.py run
  ```

---

### 2. Âm Thanh Hạn Chế

**Lý do:** Container Linux không có access đến audio driver của macOS.

**Giải pháp:** Chạy native nếu cần âm thanh đầy đủ.

---

### 3. Performance Chậm Hơn Native

| Nền tảng | Hiệu năng |
|----------|-----------|
| Native (pip install) | 100% |
| Docker trên M1 Mac | ~70-80% |
| Docker trên Intel Mac | ~60-70% |

**Mẹo:** Lần chạy đầu chậm do load model, các lần sau sẽ nhanh hơn.

---

### 4. Dung Lượng Image Lớn

Image có thể chiếm **3-5GB** dung lượng.

**Giải phóng dung lượng:**
```bash
# Xóa image khi không dùng
docker compose down --rmi all

# Xóa container dừng
docker container prune

# Xóa tất cả unused images
docker image prune -a
```

---

## 📊 So Sánh: Docker vs Native

| Tính năng | Docker | Native |
|-----------|--------|--------|
| Cài đặt | ✅ 1 lệnh | ⚠️ Nhiều bước |
| Webcam | ❌ Không (Mac) | ✅ Có |
| Audio | ⚠️ Hạn chế | ✅ Đầy đủ |
| Performance | ⚠️ 70-80% | ✅ 100% |
| Portability | ✅ Mọi máy | ⚠️ Phụ thuộc máy |
| Cô lập | ✅ An toàn | ⚠️ Ảnh hưởng system |

---

## 💡 Khuyến Nghị

### 🎯 Cho Development (Mac)

```bash
# Chạy native để có webcam + audio đầy đủ
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask --app=py/Web/all_tong.py run
```

### 🎯 Cho Deployment (Linux Server)

```bash
# Dùng Docker để đồng bộ môi trường
docker compose up -d
```

### 🎯 Cho Testing Nhanh

```bash
# Dùng Docker, không cần cài đặt phức tạp
docker compose up --build
```

---

## 📚 Tài Liệu Tham Khảo

- [Docker Documentation](https://docs.docker.com)
- [Docker Compose](https://docs.docker.com/compose)
- [Flask Documentation](https://flask.palletsprojects.com)
- [Ultralytics YOLOv8](https://docs.ultralytics.com)

---

## 🆘 Cần Trợ Giúp?

```bash
# 1. Kiểm tra container có chạy không
docker ps

# 2. Xem logs chi tiết
docker compose logs -f ai-traffic-monitor

# 3. Truy cập container debug
docker compose exec ai-traffic-monitor bash

# 4. Kiểm tra port
lsof -i :5001
```

---

**Chúc bạn thành công! 🚀**

Nếu gặp lỗi, hãy chụp màn hình lỗi và gửi cho đội phát triển.
