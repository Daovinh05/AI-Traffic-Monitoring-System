# AI Chatbot Guide

## Tổng quan

Chatbot hiện tại đi qua backend Flask, không còn phụ thuộc vào file HTML cũ. Luồng chính là:

- Frontend gọi các endpoint chatbot hoặc voice command.
- Backend route trong `backend/app/api/alert_routes.py` chuyển request sang `backend/app/chatbot/chatbot_service.py`.
- `chatbot_service.py` gọi tiếp sang `backend/app/ai/runtime.py` để sinh câu trả lời.

## Endpoint đang dùng

- `POST /api/send_chat_message` - gửi tin nhắn cho chatbot.
- `POST /api/groq_law_chat` - hỏi trợ lý luật giao thông.
- `POST /api/process_voice_command` - xử lý lệnh giọng nói.
- `GET /api/get_ai_alerts_history` - lấy lịch sử cảnh báo AI gần nhất.
- `GET /api/ai-status` - kiểm tra trạng thái AI runtime.

## Nguồn dữ liệu của chatbot

Chatbot không chỉ trả lời theo mẫu tĩnh. Nó có thể đọc dữ liệu từ hệ thống qua service/repository, ví dụ:

- xe đang giám sát
- tài xế đang đăng nhập
- tuyến đường
- cảnh báo AI gần đây
- lịch sử video và vi phạm

## Cách test nhanh

1. Chạy backend bằng `python -m backend.app.main`.
2. Mở frontend ở `http://localhost:3001/login`.
3. Vào màn hình có chatbot hoặc cảnh báo.
4. Thử các câu như:
   - `Xin chào`
   - `Xe 29B-222.22 ở đâu?`
   - `Vi phạm hôm nay thế nào?`
   - `Xem cảnh báo`

## Lưu ý

- Nếu thiếu API key hoặc AI runtime chưa sẵn sàng, backend vẫn chạy nhưng chatbot có thể rơi về rule-based response.
- Tất cả logic xử lý nên nằm trong service/runtime, không đặt trực tiếp trong route.