# Backend

## Cấu trúc thư mục

```text
backend/
|___ app/
|    |___ api/              Flask routes: auth, dashboard, cảnh báo và video stream
|    |___ services/         Xử lý nghiệp vụ giữa API và tầng dữ liệu
|    |___ repositories/     Truy vấn và ghi dữ liệu MySQL
|    |___ ai/               AI runtime, detector, trạng thái model và video
|    |___ chatbot/          Chatbot Groq, fallback và tư vấn luật giao thông
|    |___ mqtt/             Kết nối Mosquitto, gửi cảnh báo tới ESP32
|    |___ realtime/         Queue cảnh báo, cooldown và event nội bộ
|    |___ voice/            Nhận dạng, phân tích và thực thi lệnh giọng nói
|    |___ core/             Đọc biến môi trường và cấu hình ứng dụng
|    |___ db/               Khởi tạo và quản lý kết nối cơ sở dữ liệu
|    |___ models/           Định nghĩa model miền dữ liệu
|    |___ schemas/          Cấu trúc dữ liệu request và response
|    |___ utils/            Tiện ích dùng chung
|    |___ extensions.py     Khởi tạo session, CORS và bcrypt
|    |___ main.py           Flask app factory và điểm khởi chạy backend
|___ assets/
|    |___ weights/          Model YOLO định dạng .pt
|    |___ videos/           Video mẫu cho các luồng giám sát AI
|    |___ sounds/           Âm thanh cảnh báo tài xế
|    |___ pictures/         Ảnh kết quả và ảnh trạng thái AI
|___ recordings/            Video được ghi từ hệ thống giám sát
|___ training/              Kết quả và dữ liệu phục vụ huấn luyện model
|___ uploads/               File do người dùng tải lên
|___ .env.example           Mẫu cấu hình backend, MySQL, AI, MQTT và Groq
|___ Dockerfile             Cấu hình image backend khi cần chạy Docker
|___ requirements.txt       Tham chiếu danh sách thư viện Python của dự án
```

## Luồng xử lý

Entrypoint:

```bash
python -m backend.app.main
```

Luồng xử lý:

```text
api -> services -> repositories -> db
api -> ai/runtime -> services/repositories/mqtt
```

Backend render các giao diện cũ trong `frontend/legacy-templates` và cung cấp
API, AI runtime cho frontend Next.js.

## Chạy local

Chạy bằng `.venv` và MySQL local:

```bash
.venv/bin/python -m backend.app.main
```

Trong môi trường không có audio device:

```bash
SDL_AUDIODRIVER=dummy MQTT_ENABLED=false .venv/bin/python -m backend.app.main
```
