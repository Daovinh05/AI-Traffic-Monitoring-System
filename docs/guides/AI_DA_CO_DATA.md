# AI Đã Có Data Thực Tế Từ Hệ Thống

## Ý nghĩa hiện tại

Tài liệu này mô tả trạng thái mà AI đọc dữ liệu thật từ hệ thống, không còn hardcode theo ví dụ demo cũ.

Trong repo hiện tại, dữ liệu được tách qua:

- `backend/app/repositories/` để truy vấn MySQL.
- `backend/app/services/` để ghép dữ liệu cho dashboard/chatbot.
- `backend/app/api/dashboard_routes.py` và `backend/app/api/route_routes.py` để trả JSON hoặc render giao diện legacy.

## Loại data có thể dùng cho AI

- biển số xe
- tên tài xế
- vị trí hiện tại
- trạng thái xe
- tuyến đường
- cảnh báo vi phạm
- lịch sử video/recording

## Cách dùng đúng

Khi chatbot hoặc dashboard cần trả lời câu hỏi, hãy lấy dữ liệu từ service/repository thay vì tạo danh sách cứng trong code. Ví dụ:

- `route_service.list_routes()` cho tuyến đường
- `dashboard_service.build_dashboard(page)` cho thống kê dashboard
- repository cảnh báo cho lịch sử alert

## Nếu muốn thêm data thử nghiệm

1. Thêm bản ghi vào MySQL.
2. Cập nhật service nếu cần join thêm bảng.
3. Test lại endpoint tương ứng ở frontend hoặc bằng curl/Postman.

## Ghi chú

Nếu một câu hỏi không có dữ liệu trong database, chatbot nên nói rõ là chưa tìm thấy thay vì đoán.