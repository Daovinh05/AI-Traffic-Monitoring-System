# Hướng dẫn chạy dự án AI Traffic Monitoring System

## Yêu cầu trước khi chạy

- Python 3.11+
- Node.js 18+
- MySQL (XAMPP hoặc cài riêng)
- MQTT Broker (Mosquitto) - tùy chọn

## 1. Cài đặt và cấu hình

### Tạo database

```bash
mysql -u root -p -e "CREATE DATABASE giam_sat;"
mysql -u root -p giam_sat < docs/guides/database_schema.sql
```

### Cài Python dependencies

```bash
pip install -r requirements.txt
```

### Kích hoạt môi trường ảo

```bash
source .venv/bin/activate
```

### Cấu hình file `.env`

Tạo file `backend/.env` với nội dung:

```dotenv
SECRET_KEY=change-me
PORT=5001
FLASK_DEBUG=false
FRONTEND_URL=http://localhost:3001
AI_ENABLED=true
DRIVER_VIDEO_SOURCE=0
SESSION_TYPE=filesystem
SESSION_PERMANENT=true
SESSION_LIFETIME_HOURS=24

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=giam_sat

MQTT_ENABLED=true
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_TOPIC=traffic/alert
```

**Ghi chú `DRIVER_VIDEO_SOURCE`:**
- `0` - Webcam (camera vật lý)
- `backend/assets/videos/ca_bin.mp4` - File video mẫu

## 2. Chạy backend

```bash
python -m backend.app.main
```

Nếu máy không có thiết bị âm thanh:

```bash
SDL_AUDIODRIVER=dummy python -m backend.app.main
```

Backend chạy tại: **http://localhost:5001**

## 3. Chạy frontend

Mở terminal khác:

```bash
cd frontend
npm install
npm run dev
```

Frontend chạy tại: **http://localhost:3001**

## 4. Truy cập ứng dụng

Mở trình duyệt: **http://localhost:3001/login**

**Tài khoản mặc định:**

| Vai trò | Tên đăng nhập | Mật khẩu |
|---------|---------------|-----------|
| Admin | admin | admin123 |
| User | user | user123 |

## 5. MQTT (tùy chọn)

Nếu muốn bật MQTT, chạy Mosquitto:

```bash
# macOS
brew services start mosquitto

# Linux
sudo systemctl start mosquitto
```

## 6. AI Runtime (tùy chọn)

Để bật tính năng AI (nhận diện buồn ngủ, ngáp, điện thoại, dây an toàn):

1. Đặt `AI_ENABLED=true` trong `backend/.env`
2. Đảm bảo có đủ file model trong `backend/assets/weights/`
3. Đảm bảo có file video trong `backend/assets/videos/`
4. Đảm bảo có file âm thanh cảnh báo trong `backend/assets/sounds/`

## Troubleshooting

| Vấn đề | Cách khắc phục |
|--------|----------------|
| Camera không hiện | Kiểm tra quyền truy cập Camera trong System Settings > Privacy & Security > Camera |
| MySQL không kết nối được | Đảm bảo MySQL đang chạy trên cổng 3306 |
| Port 5001/3001 đang bị chiếm | Đổi port trong file `.env` hoặc `frontend/next.config.ts` |
| MediaPipe lỗi | Đảm bảo đã cài đúng version: `pip install mediapipe==0.10.9` |
| Camera fallback về video | Nếu máy không có webcam, hệ thống tự động dùng file `ca_bin.mp4` |
