# 🐳 Hướng dẫn chạy AI Traffic Monitoring System trên macOS M1 với Docker

## Yêu cầu trước khi bắt đầu

### 1. Cài đặt Docker Desktop trên Mac M1

1. Tải **Docker Desktop for Mac** từ https://www.docker.com/products/docker-desktop
2. Chọn phiên bản **Apple Silicon (M1/M2/M3)** (không phải Intel)
3. Cài đặt và khởi động Docker Desktop
4. Mở Terminal và kiểm tra:
   ```bash
   docker --version
   docker compose version
   ```

### 2. Chuẩn bị dự án

Đảm bảo bạn có thư mục gốc dự án:

```
/Users/vinhdv/Documents/clone/AI-Traffic-Monitoring-System/
```

Với các thư mục con:

- `py/` — Source code chính
- `py/weights/` — Model YOLO (.pt files)
- `py/Sound/` — File âm thanh cảnh báo
- `py/video_input/` — Video test (tùy chọn)
- `requirements.txt` — Dependencies Python
- `Dockerfile` — Config Docker
- `docker-compose.yml` — Config compose

---

## Hướng dẫn chạy (Step by step)

### Bước 1: Mở Terminal

Trong Terminal trên Mac, chuyển đến thư mục gốc dự án:

```bash
cd /Users/vinhdv/Documents/clone/AI-Traffic-Monitoring-System
```

### Bước 2: Build Docker image

Lệnh này sẽ tạo image từ Dockerfile (lần đầu sẽ mất 10-30 phút tùy tốc độ mạng):

```bash
docker compose build
```

**Output mong đợi**: Kết thúc bằng `Successfully tagged ...` hoặc `BUILD SUCCESS`

Nếu gặp lỗi:

- Đảm bảo Docker Desktop đang chạy (kiểm tra menu Mac)
- Thử lại: `docker compose build --no-cache` (build lại từ đầu)

### Bước 3: Chạy container

```bash
docker compose up
```

**Output mong đợi**:

```
ai-traffic-monitor  | * Running on http://0.0.0.0:5000
ai-traffic-monitor  | * Debugger is active!
ai-traffic-monitor  | * Debugger PIN: ...
```

**Truy cập ứng dụng**: Mở browser và vào http://localhost:5000

### Bước 4: Dừng container

Trong Terminal, nhấn `Ctrl+C`

---

## Các lệnh hữu ích

### Chạy container ở background (không hiển thị logs)

```bash
docker compose up -d
```

### Xem logs của container đang chạy

```bash
docker compose logs -f ai-traffic-monitor
```

### Dừng container background

```bash
docker compose down
```

### Xóa image (giải phóng dung lượng)

```bash
docker image rm ai-traffic-monitoring-system-ai-traffic-monitor
```

hoặc

```bash
docker compose down --rmi all
```

### Chạy container với script khác (ví dụ: `drive.py` thay vì `all_tong.py`)

Sửa file `docker-compose.yml`:

```yaml
environment:
  - FLASK_APP=py/Web/drive.py
```

Sau đó:

```bash
docker compose up --build
```

### Chạy command tùy chỉnh trong container

```bash
docker compose exec ai-traffic-monitor python -c "import cv2; print(cv2.__version__)"
```

### Truy cập shell của container (debug)

```bash
docker compose exec ai-traffic-monitor bash
```

---

## ⚠️ Những điều cần biết trên macOS

### 1. **Webcam không hoạt động trong Docker**

**Lý do**: Docker Desktop trên Mac chạy trong Linux VM — không thể truy cập trực tiếp webcam của Mac.

**Giải pháp**:

- ✅ **Cách đơn giản**: Chạy ứng dụng trực tiếp trên macOS (không dùng Docker):

  ```bash
  pip install -r requirements.txt
  flask --app=py/Web/all_tong.py run
  ```

- ✅ **Hoặc**: Sử dụng video file thay vì webcam:
  - Đặt video vào `py/video_input/`
  - Sửa code để dùng video file thay vì `cv2.VideoCapture(0)`

### 2. **Audio/Sound hạn chế**

- Nghe âm thanh từ container Docker trên Mac rất khó.
- **Giải pháp**: Chạy trực tiếp trên macOS để có âm thanh đầy đủ.

### 3. **Dung lượng image lớn**

- Image có thể 2-4 GB vì chứa OpenCV, dlib, mediapipe, torch, v.v.
- **Giải pháp**: Dùng câu lệnh `docker compose down --rmi all` để xóa khi không dùng.

### 4. **Performance chậm hơn**

- Docker Desktop trên M1 Mac nhanh hơn Intel nhưng vẫn chậm hơn native.
- Model inference có thể mất thêm 20-30% thời gian.
- **Giải pháp**: Nếu cần tốc độ, chạy native trên Mac hoặc sử dụng Linux VM/server.

### 5. **`pycaw` / `comtypes` không hoạt động**

- Đây là Windows-only libs.
- Trong container Linux, không thể điều khiển âm thanh Windows.
- Code sẽ skip hoặc error — không ảnh hưởng chức năng chính.

### 6. **File models (`py/weights/*.pt`) không copy vào image**

- Để tiết kiệm dung lượng, `.dockerignore` loại trừ `py/weights/`.
- Container mount `py/weights/` từ host → không cần copy.
- ✅ Đảm bảo file `.pt` tồn tại trên host trước khi chạy.

---

## Troubleshooting

### ❌ Lỗi: "docker: command not found"

- Docker Desktop chưa được cài hoặc không chạy.
- **Fix**: Cài Docker Desktop từ https://www.docker.com/products/docker-desktop (chọn Apple Silicon).

### ❌ Lỗi: "Cannot connect to Docker daemon"

- Docker Desktop không running.
- **Fix**: Mở Docker Desktop từ Applications.

### ❌ Lỗi: "No such file or directory: 'py/shape_predictor_68_face_landmarks.dat'"

- File `py/shape_predictor_68_face_landmarks.dat` không tồn tại.
- **Fix**: Tải file từ https://github.com/davisking/dlib-models hoặc yêu cầu từ maintainer.

### ❌ Lỗi: "ModuleNotFoundError: No module named 'comtypes'"

- Lỗi đó không ảnh hưởng trên container Linux (Windows-only).
- **Fix**: Không cần lo — code sẽ bỏ qua.

### ❌ Flask crash hoặc không start

Xem logs:

```bash
docker compose logs ai-traffic-monitor
```

Nếu model YOLO không tìm thấy:

- Đảm bảo `py/weights/` có chứa `.pt` files.
- Hoặc sửa đường dẫn trong code (ví dụ: `py/weights/yolov8n.pt`).

### ❌ Container khởi động nhưng không thể truy cập http://localhost:5000

- Kiểm tra port 5000 không bị dùng:
  ```bash
  lsof -i :5000
  ```
- Nếu port đang dùng, đổi port trong `docker-compose.yml`:
  ```yaml
  ports:
    - "5001:5000" # Localhost 5001 -> Container 5000
  ```

---

## So sánh: Docker vs Native trên macOS

| Tính năng       | Docker                                 | Native (pip install)       |
| --------------- | -------------------------------------- | -------------------------- |
| **Setup**       | Dễ, mọi gói đã đầy đủ                  | Cần cài tay từng gói       |
| **Webcam**      | ❌ Không hoạt động                     | ✅ Hoạt động               |
| **Audio**       | ❌ Khó                                 | ✅ Hoạt động tốt           |
| **Performance** | Chậm hơn ~20-30%                       | 🚀 Tối ưu                  |
| **Portability** | ✅ Chạy được trên bất kì máy có Docker | ❌ Phụ thuộc setup         |
| **Isolation**   | ✅ Không ảnh hưởng system              | ❌ Có thể conflict version |

---

## Lời khuyên

### 🎯 Nếu bạn cần **test nhanh & đơn giản**

1. Chạy native:
   ```bash
   pip install -r requirements.txt
   python -m flask --app=py/Web/all_tong.py run
   ```
2. Mở http://localhost:5000

### 🎯 Nếu bạn cần **deploy sang máy khác (Linux server)**

1. Dùng Docker (container giống nhau trên bất kỳ máy).
2. Chỉ cần `Dockerfile`, `docker-compose.yml`, và source code.
3. Chạy `docker compose up` — xong!

### 🎯 Nếu bạn cần **cả webcam + audio + Docker**

1. Chạy Flask trong container.
2. Chạy webcam/audio capture trên native macOS.
3. Stream video HTTP từ native sang container (dùng ffmpeg).
   → Phức tạp hơn — nên chạy full native nếu có thể.

---

## Thêm tài liệu

- Docker docs: https://docs.docker.com
- Docker Compose: https://docs.docker.com/compose
- Flask on Docker: https://docs.docker.com/language/python
- Apple Silicon (M1): https://www.docker.com/blog/apple-silicon-support/

---

**Bạn có câu hỏi gì? Hãy check lại logs hoặc liên hệ!** 🚀
