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

```bash
docker compose up mysql
```

Backend:

```bash
source .venv/bin/activate
SDL_AUDIODRIVER=dummy MQTT_ENABLED=false python -m backend.app.main
```

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

Mở `http://localhost:3001/login`.

## Kiểm tra

```bash
python3 -m py_compile $(rg --files backend -g '*.py')
cd frontend && npm run build
docker compose config
```

Stream AI cần model trong `backend/assets/weights`, video trong
`backend/assets/videos`, Dlib landmark file và quyền camera/audio phù hợp.
