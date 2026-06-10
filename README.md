# AI Traffic Monitoring System

Hệ thống giám sát tài xế và giao thông bằng Flask API, Next.js, OpenCV,
YOLO, MediaPipe, Dlib, MySQL và MQTT.

## Kiến trúc

```text
backend/
  app/
    api/            HTTP handlers theo nhóm tính năng
    services/       nghiệp vụ
    repositories/   truy vấn MySQL
    ai/             AI runtime và detector
    mqtt/           MQTT/ESP32
    chatbot/        chatbot và tư vấn luật
    realtime/       queue/cooldown/event
  assets/
    weights/        model YOLO
    videos/         video đầu vào
    sounds/         âm thanh cảnh báo
    pictures/       ảnh AI sinh ra
frontend/
  src/app/          Next.js pages
  public/legacy/    static image đã chuyển từ giao diện cũ
esp32/              firmware ESP32 MQTT
```

Backend sở hữu toàn bộ API và AI runtime. Frontend là React/Next.js thuần,
không còn iframe hoặc Flask template. Thư mục `py/` và compatibility runtime
đã được xóa.

## Chạy local

Mô hình chạy local không dùng Docker:

- MySQL chạy trực tiếp trên máy ở cổng `3306`.
- Backend chạy trong `.venv` ở cổng `5001`.
- Frontend chạy bằng npm ở cổng `3001`.

Tạo database lần đầu:

```bash
mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS giam_sat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -uroot -p giam_sat < database_schema.sql
```

Backend:

```bash
source .venv/bin/activate
python -m backend.app.main
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

Mở `http://localhost:3001/login`.

Backend tự đọc `backend/.env`. Khi MySQL có mật khẩu, sửa:

```dotenv
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=mat_khau_mysql
MYSQL_DB=giam_sat
AI_ENABLED=true
MQTT_ENABLED=false
```

Nếu máy chạy backend không có thiết bị phát âm thanh:

```bash
SDL_AUDIODRIVER=dummy python -m backend.app.main
```

## Kiểm tra

```bash
python3 -m py_compile $(rg --files backend -g '*.py')
cd frontend && npm run build
docker compose config
```

Stream AI cần model trong `backend/assets/weights`, video trong
`backend/assets/videos`, Dlib landmark file và quyền camera/audio phù hợp.

## Bat AI tren VPS

Model `.pt` khong duoc luu trong Git. Dong bo asset tu may co day du model:

```bash
./scripts/check-ai-assets.sh
./scripts/sync-ai-assets.sh vinh@103.195.5.126:~/project/AI-Traffic-Monitoring-System
```

Tren VPS, kiem tra asset va bat AI:

```bash
./scripts/check-ai-assets.sh
printf 'AI_ENABLED=true\n' > .env
docker compose up -d --build --force-recreate backend frontend
curl http://localhost:5001/api/ai-status
```

AI runtime nap model theo tung luong video thay vi nap tat ca khi backend khoi
dong. `/api/ai-status` tra ve trang thai va danh sach asset con thieu.
