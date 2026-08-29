# Route Usage Guide

## Tổng quan

Module route hiện quản lý tuyến đường qua MySQL và expose API để frontend/legacy UI đọc dữ liệu.

## Endpoint hiện tại

- `GET /api/routes` - lấy danh sách tuyến đường.
- `GET /api/routes/<route_id>` - lấy chi tiết một tuyến.
- `POST /api/routes` - tạo tuyến mới.
- `PUT /api/routes/<route_id>` - cập nhật tuyến.
- `DELETE /api/routes/<route_id>` - xóa tuyến.

## Dữ liệu backend đang dùng

Route data nên được lưu trong database, thường là:

- bảng thông tin tuyến đường
- bảng path/tọa độ tuyến đường

Các service liên quan nằm trong `backend/app/services/route_service.py` và `backend/app/repositories/route_repository.py`.

## Cách dùng trên UI

- Trang admin dashboard có thể lấy danh sách tuyến từ API `/api/routes`.
- Mỗi route có thể vẽ bằng mảng tọa độ `path` thay vì chỉ 2 điểm đầu cuối.

## Gợi ý khi thêm tuyến mới

1. Tạo bản ghi tuyến trong MySQL.
2. Thêm các điểm path theo thứ tự.
3. Gọi lại API `/api/routes` để kiểm tra.

## Lưu ý

- Tọa độ nên giữ đúng thứ tự `lat, lng`.
- Nên có ít nhất 2 điểm cho một tuyến.