# IMPLEMENT Guide

## Mục tiêu kiến trúc hiện tại

Repo hiện đang đi theo hướng:

- Backend Flask API.
- Frontend Next.js.
- MySQL cho dữ liệu nghiệp vụ.
- AI runtime riêng trong `backend/app/ai/`.
- Realtime/alert/chatbot/voice được tách theo module.

## Nguyên tắc chính

1. Route chỉ nhận request và trả response.
2. Service xử lý nghiệp vụ.
3. Repository làm việc với MySQL.
4. AI, MQTT, chatbot và voice không nên viết trực tiếp trong route.
5. Giao diện nên nằm ở frontend, backend chỉ trả JSON hoặc stream.

## Cấu trúc module đang phù hợp

- `backend/app/api/` - HTTP handlers.
- `backend/app/services/` - business logic.
- `backend/app/repositories/` - query DB.
- `backend/app/ai/` - detection/runtime.
- `backend/app/realtime/` - queue/cooldown/event.
- `backend/app/chatbot/` - chatbot adapter.
- `backend/app/mqtt/` - ESP32/MQTT.

## Khi mở rộng code

- Thêm endpoint mới thì ưu tiên thêm service/repository tương ứng.
- Nếu dữ liệu thuộc dashboard/route/alert thì đưa vào MySQL trước.
- Nếu phát hiện AI mới thì tách thành detector riêng.

## Ghi chú

Tài liệu này là bản ghi nhớ ngắn cho agent/codebase hiện tại, không phải plan migration đầy đủ.