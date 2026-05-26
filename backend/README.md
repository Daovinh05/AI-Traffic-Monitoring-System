# Backend Architecture

Entrypoint mới: `python -m backend.app.main`

Trong giai đoạn hiện tại, backend mới vẫn mount app Flask cũ trong
`py/Web/drive_auth.py`. Cách này giữ nguyên giao diện, route, API và video
stream ban đầu trong khi repo đã có cấu trúc để refactor dần.

## Cách chạy local

Từ root project:

```bash
python -m backend.app.main
```

URL mặc định:

```text
http://localhost:5001/login
```

Cấu hình có thể đặt bằng biến môi trường hoặc file `.env` tương ứng với
`backend/.env.example`:

- `SECRET_KEY`
- `PORT`
- `FLASK_DEBUG`
- `SESSION_TYPE`
- `SESSION_PERMANENT`
- `SESSION_LIFETIME_HOURS`
- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DB`
- `MQTT_ENABLED`
- `MQTT_BROKER`
- `MQTT_PORT`
- `MQTT_TOPIC`
- `GROQ_API_KEY`

Mặc định MySQL vẫn tương thích code cũ:

```text
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=giam_sat
```

## Cấu trúc

Kiến trúc đã được dựng theo các tầng:

- `api/`: Flask/FastAPI route hoặc blueprint
- `services/`: nghiệp vụ
- `repositories/`: truy vấn database
- `models/`: model/domain object
- `schemas/`: request/response schema
- `ai/`: xử lý OpenCV, YOLO, MediaPipe, Dlib
- `realtime/`: queue, cooldown, websocket/SSE
- `mqtt/`: gửi cảnh báo ESP32
- `chatbot/`: Groq/chatbot
- `voice/`: xử lý lệnh giọng nói
- `core/`: cấu hình chung
- `db/`: kết nối database

## Adapter hiện tại

- `backend/app/main.py`: entrypoint mới, mount lại Flask app cũ để giữ UI.
- `backend/app/core/config.py`: cấu hình env dùng chung.
- `backend/app/db/database.py`: adapter connection MySQL cho repository mới.
- `backend/app/api/*_routes.py`: chia route theo nhóm chức năng và giữ mapping
  endpoint cũ để migrate dần.
- `backend/app/services/*_service.py`: lớp nghiệp vụ đã tách cho auth,
  dashboard, alert, route và video/camera.
- `backend/app/repositories/*_repository.py`: lớp query database tương ứng.
- `backend/app/ai/*`, `backend/app/realtime/*`, `backend/app/mqtt/*`,
  `backend/app/chatbot/*`, `backend/app/voice/*`: adapter theo module chức
  năng cho AI, realtime, MQTT, chatbot và voice.

## Lộ trình tách route

Tách từng nhóm nhỏ, mỗi nhóm xong phải giữ nguyên endpoint cũ để template hiện
tại không cần thay đổi:

1. `auth_routes.py`: `/login`, `/api/login`, `/api/logout`, `/api/check-auth`.
2. `dashboard_routes.py`: `/dashboard` và dữ liệu dashboard.
3. `alert_routes.py`: `/api/alerts`, `/api/all-alerts`, `/api/admin-warnings`.
4. `stream_routes.py`: `/video_driver`, `/video_traffic`, `/video_sign`,
   `/video_vacham`.
5. `route_routes.py`: `/api/routes` và `/api/routes/<route_id>`.

Mẫu tách:

```text
api/*_routes.py -> services/*_service.py -> repositories/*_repository.py -> db/database.py
```

Hiện tại các file `api/*_routes.py` ghi nhận ranh giới route và mapping view
legacy. Auth login đã được wire qua `auth_service`; các nhóm còn lại đã có
service/repository để chuyển dần route mà không đổi URL hoặc template.

Các module AI/realtime/MQTT/chatbot/voice mới dùng lazy adapter qua
`backend/app/legacy/loaders.py`. Import module mới không tự load YOLO/dlib/pygame;
legacy model chỉ được load khi gọi function thật. Điều này giữ luồng cũ ổn định
trong lúc vẫn có cấu trúc để tách dần.

Trong lúc chưa chuyển sang Next.js, toàn bộ template trong `py/Web/templates`
và static asset trong `py/Web/static` vẫn là giao diện chính.
