# Setup Database Routes

## Mục tiêu

Hướng dẫn này dành cho phần tuyến đường và dữ liệu MySQL của project hiện tại.

## Bước 1: tạo database

```bash
mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS giam_sat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -uroot -p giam_sat < database_schema.sql
```

## Bước 2: kiểm tra route tables

Các bảng liên quan thường gồm:

- bảng thông tin tuyến đường
- bảng path/tọa độ tuyến đường

Nếu bạn đang bổ sung route mới, hãy ưu tiên sửa schema trong `database_schema.sql` thay vì hardcode trong Python.

## Bước 3: kiểm tra API

- `GET /api/routes`
- `GET /api/routes/<route_id>`
- `POST /api/routes`
- `PUT /api/routes/<route_id>`
- `DELETE /api/routes/<route_id>`

## Bước 4: kiểm tra trong code

Các phần hay cần xem:

- `backend/app/services/route_service.py`
- `backend/app/repositories/route_repository.py`
- `backend/app/api/route_routes.py`

## Ghi chú

- Nên giữ dữ liệu path theo thứ tự điểm đi.
- Nên dùng `utf8mb4` để tránh lỗi tiếng Việt.