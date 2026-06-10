# AI Traffic Monitoring System

Hệ thống giám sát tài xế và giao thông bằng Flask API, Next.js, OpenCV, YOLO, MediaPipe, Dlib, MySQL và MQTT.

Tài liệu chi tiết đã được gom vào [docs/guides/README.md](docs/guides/README.md).

## Chạy nhanh

1. Tạo database `giam_sat` và import `database_schema.sql`.
2. Cài Python dependencies: `pip install -r requirements.txt`.
3. Kích hoạt môi trường ảo: `source .venv/bin/activate`.
4. Chạy backend: `python -m backend.app.main`.
5. Mở terminal khác, vào `frontend/`, cài package và chạy dev server:

```bash
cd frontend
npm install
npm run dev
```

6. Mở `http://localhost:3001/login`.

Nếu backend không có thiết bị âm thanh, chạy:

```bash
SDL_AUDIODRIVER=dummy python -m backend.app.main
```

## Cấu hình tối thiểu

Backend đọc cấu hình MySQL và cổng chạy từ `.env` hoặc `backend/.env`.
Các giá trị hay dùng:

```dotenv
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=giam_sat
PORT=5001
FRONTEND_URL=http://localhost:3001
```

Nếu muốn bật AI runtime, đảm bảo có đủ file trong `backend/assets/weights`, `backend/assets/videos`, `backend/assets/sounds` và đặt `AI_ENABLED=true`.
