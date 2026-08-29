# Tài liệu dự án

Đây là thư mục chứa toàn bộ tài liệu hướng dẫn đã được cập nhật theo trạng thái hiện tại của repo.

## Nên đọc theo thứ tự

1. [huong_dan.md](huong_dan.md) - cách clone về và chạy dự án.
2. [SETUP_DATABASE_ROUTES.md](SETUP_DATABASE_ROUTES.md) - import database và dữ liệu tuyến đường.
3. [SETUP_AI_API.md](SETUP_AI_API.md) - cấu hình Groq hoặc LLM khác cho chatbot.
4. [AI_DA_SAN_SANG.md](AI_DA_SAN_SANG.md) - điều kiện để AI runtime sẵn sàng.
5. [AI_DA_CO_DATA.md](AI_DA_CO_DATA.md) - cách AI dùng dữ liệu thật từ hệ thống.
6. [AI_CHATBOT_GUIDE.md](AI_CHATBOT_GUIDE.md) - cách dùng chatbot và các endpoint liên quan.
7. [ROUTE_USAGE_GUIDE.md](ROUTE_USAGE_GUIDE.md) - cách quản lý và hiển thị tuyến đường.
8. [IMPLEMENT.md](IMPLEMENT.md) - ghi chú kiến trúc và định hướng refactor.

## Ghi chú chung

- Backend hiện chạy bằng Flask entrypoint `python -m backend.app.main`.
- Frontend hiện là Next.js ở thư mục `frontend/`.
- Database chính là MySQL với schema ở `database_schema.sql`.