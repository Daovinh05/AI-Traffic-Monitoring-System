# 🚗 AI Traffic Monitoring System

Hệ thống Hỗ trợ Lái xe Thông minh với AI, tích hợp nhiều tính năng an toàn và cảnh báo giao thông.

---

## 📋 Mục lục

- [Tính năng](#-tính-năng)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Hướng dẫn cài đặt](#-hướng-dẫn-cài-đặt)
  - [Cách 1: Cài đặt trực tiếp (Recommended)](#cách-1-cài-đặt-trực-tiếp-recommended)
  - [Cách 2: Sử dụng Docker](#cách-2-sử-dụng-docker)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [Chạy ứng dụng](#-chạy-ứng-dụng)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Tính năng

### 🎯 Giám sát tài xế
- Phát hiện buồn ngủ (nhắm mắt, ngáp)
- Phát hiện sử dụng điện thoại
- Kiểm tra dây an toàn
- Giám sát tay lái

### 🚦 Cảnh báo biển báo giao thông
- Nhận diện biển báo tốc độ
- Cảnh báo cấm rẽ
- Nhận diện biển báo nguy hiểm

### 📊 Phân tích lưu lượng giao thông
- Đếm phương tiện
- Phân loại xe (xe hơi, xe tải, xe máy)
- Cảnh báo kẹt xe

### ⚠️ Cảnh báo an toàn
- Cảnh báo va chạm
- Cảnh báo lệch làn đường
- Phát hiện khoảng cách an toàn

### 👋 Điều khiển bằng cử chỉ tay
- Điều khiển âm thanh
- Điều khiển ứng dụng
- Điều khiển camera

---

## 💻 Yêu cầu hệ thống

### Tối thiểu
- **Hệ điều hành**: Windows 10 / macOS 11+ / Linux (Ubuntu 20.04+)
- **Python**: 3.8 - 3.10
- **RAM**: 8GB (khuyến nghị 16GB)
- **Dung lượng**: 10GB trống
- **Webcam**: Tùy chọn (cho tính năng giám sát tài xế)

### Khuyến nghị
- **GPU**: NVIDIA CUDA support (tăng tốc inference)
- **CPU**: 4 cores trở lên
- **RAM**: 16GB

---

## 🛠️ Hướng dẫn cài đặt

### Cách 1: Cài đặt trực tiếp (Recommended)

#### Bước 1: Clone repository

```bash
git clone <repository-url>
cd AI-Traffic-Monitoring-System
```

#### Bước 2: Tạo và kích hoạt Virtual Environment

**Trên Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Trên macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

> **Lưu ý**: Thư mục `venv/` đã được thêm vào `.gitignore`, nên khi pull dự án về, bạn **phải tự tạo** virtual environment mới.

#### Bước 3: Cài đặt dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **⚠️ Lưu ý quan trọng về dlib:**
> - **Windows**: Cần cài Visual C++ Build Tools trước khi cài dlib
>   - Tải tại: https://visualstudio.microsoft.com/visual-cpp-build-tools/
> - **macOS**: 
>   ```bash
>   brew install cmake
>   pip install dlib --no-binary dlib
>   ```
> - **Linux**:
>   ```bash
>   sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev
>   ```

#### Bước 4: Tải model files

**Tải YOLO weights:**
```bash
mkdir -p py/weights
cd py/weights
# Tải model YOLOv8
curl -L https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n.pt -o yolov8n.pt
# Hoặc tải các model khác nếu cần
cd ../..
```

**Tải shape predictor (cho facial landmarks):**
```bash
# File đã có sẵn trong dự án: py/shape_predictor_68_face_landmarks.dat
# Nếu thiếu, tải từ: https://github.com/davisking/dlib-models
```

#### Bước 5: Kiểm tra cài đặt

```bash
python -c "import cv2, dlib, flask, ultralytics; print('✅ Tất cả dependencies đã cài đặt thành công!')"
```

---

### Cách 2: Sử dụng Docker

> **Lưu ý**: Docker không hỗ trợ webcam trên macOS. Chỉ sử dụng Docker cho testing hoặc deployment server.

#### Bước 1: Cài đặt Docker Desktop

- Tải từ: https://www.docker.com/products/docker-desktop
- Chọn phiên bản phù hợp (Apple Silicon cho M1/M2/M3)

#### Bước 2: Build và chạy container

```bash
# Build image
docker compose build

# Chạy container
docker compose up

# Hoặc chạy background
docker compose up -d
```

#### Bước 3: Truy cập ứng dụng

Mở trình duyệt: http://localhost:5000

#### Các lệnh Docker hữu ích

```bash
# Xem logs
docker compose logs -f

# Dừng container
docker compose down

# Dừng và xóa containers, networks
docker compose down --rmi all
```

---

## 📁 Cấu trúc dự án

```
AI-Traffic-Monitoring-System/
├── py/
│   ├── Web/                    # Ứng dụng Flask chính
│   │   ├── all_tong.py        # File main - tích hợp tất cả tính năng
│   │   ├── drive.py           # Module giám sát tài xế
│   │   ├── tay_chuan.py       # Module điều khiển cử chỉ tay
│   │   ├── bien_so.py         # Module nhận diện biển số
│   │   ├── templates/         # HTML templates
│   │   └── static/            # CSS, JS, images
│   ├── weights/               # YOLO model files (.pt)
│   ├── Sound/                 # Audio alerts
│   ├── video_input/           # Video test files
│   ├── pictures/              # Output images
│   └── shape_predictor_68_face_landmarks.dat
├── recordings/                # Video recordings
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker config
├── Dockerfile
└── README.md
```

---

## 🚀 Chạy ứng dụng

### Chạy Flask application

**Cách 1: Sử dụng Flask CLI (Recommended)**
```bash
# Kích hoạt venv trước
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Chạy module chính
flask --app py/Web/all_tong.py run --port 5001 --debug
```

**Cách 2: Sử dụng Python trực tiếp**
```bash
python py/Web/all_tong.py
```

**Cách 3: Sử dụng python -m flask**
```bash
python -m flask --app py/Web/all_tong.py run --port 5001
```

### Truy cập ứng dụng

Sau khi khởi động, mở trình duyệt và truy cập:

| Trang | URL | Mô tả |
|-------|-----|-------|
| **Trang chủ** | http://127.0.0.1:5001/ | Dashboard chính |
| **Giám sát lái xe** | http://127.0.0.1:5001/lai_xe | Theo dõi trạng thái tài xế |
| **Điều khiển tay** | http://127.0.0.1:5001/hands | Điều khiển bằng cử chỉ |

> **Lưu ý**: Port mặc định là **5001**. Nếu port bị chiếm, đổi sang port khác:
> ```bash
> flask --app py/Web/all_tong.py run --port 5002
> ```

---

## ❓ Troubleshooting

### Lỗi thường gặp

#### 1. `ModuleNotFoundError: No module named '...'`

**Nguyên nhân**: Chưa cài đặt dependencies hoặc venv chưa được kích hoạt.

**Giải pháp**:
```bash
# Kiểm tra venv đang active
which python  # macOS/Linux
where python  # Windows

# Cài đặt lại dependencies
pip install -r requirements.txt
```

#### 2. Lỗi cài đặt `dlib` trên Windows

**Nguyên nhân**: Thiếu Visual C++ Build Tools.

**Giải pháp**:
1. Tải và cài đặt: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Chọn "Desktop development with C++"
3. Restart và cài lại: `pip install dlib`

#### 3. Lỗi cài đặt `dlib` trên macOS

**Nguyên nhân**: Thiếu cmake hoặc compiler.

**Giải pháp**:
```bash
brew install cmake
pip install dlib --no-binary dlib
```

#### 4. `ImportError: cannot import name '...' from 'dlib'`

**Nguyên nhân**: Version dlib không tương thích.

**Giải pháp**:
```bash
pip uninstall dlib
pip install dlib==19.22.0
```

#### 5. Không tìm thấy model file `.pt`

**Nguyên nhân**: File weights chưa được tải về.

**Giải pháp**:
```bash
mkdir -p py/weights
cd py/weights
curl -L https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n.pt -o yolov8n.pt
```

#### 6. Port 5001 đã được sử dụng

**Nguyên nhân**: Port đang bị ứng dụng khác chiếm.

**Giải pháp**:
```bash
# Tìm process đang dùng port 5001
lsof -i :5001  # macOS/Linux
netstat -ano | findstr :5001  # Windows

# Kill process hoặc đổi port khác
flask --app py/Web/all_tong.py run --port 5002
```

#### 7. Webcam không hoạt động (Docker trên macOS)

**Nguyên nhân**: Docker trên macOS không thể truy cập webcam host.

**Giải pháp**:
- Chạy native (không dùng Docker)
- Hoặc sử dụng video file thay vì webcam

#### 8. Lỗi `shape_predictor_68_face_landmarks.dat` không tồn tại

**Giải pháp**:
- File đã có sẵn trong `py/shape_predictor_68_face_landmarks.dat`
- Nếu thiếu, tải từ: https://github.com/davisking/dlib-models

---

## 📝 Additional Commands

### Quản lý Virtual Environment

```bash
# Tạo venv mới
python -m venv venv

# Kích hoạt
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Thoát venv
deactivate

# Xem danh sách packages đã cài
pip list

# Xuất danh sách packages
pip freeze > requirements.txt
```

### Cập nhật dự án (khi có changes từ remote)

```bash
# Pull changes mới nhất
git pull origin main

# Cập nhật dependencies (nếu requirements.txt thay đổi)
pip install -r requirements.txt --upgrade

# Nếu có xung đột venv, xóa và tạo lại
rm -rf venv/  # macOS/Linux
rmdir /s venv  # Windows
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

---

## 📄 License

Dự án này được phát triển cho mục đích học tập và nghiên cứu.

---

## 👥 Đóng góp

Mọi đóng góp xin gửi về repository chính thông qua Pull Request.

---

## 📞 Hỗ trợ

Nếu gặp vấn đề khi cài đặt hoặc chạy dự án:

1. Kiểm tra phần [Troubleshooting](#-troubleshooting)
2. Xem logs chi tiết: `docker compose logs -f` (nếu dùng Docker)
3. Tạo issue trên GitHub repository

---

**Phát triển với ❤️ bởi AI Traffic Monitoring Team**
