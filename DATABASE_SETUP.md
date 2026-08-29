# Hướng Dẫn Cài Đặt Database

## 1. Import Database vào MySQL

### Cách 1: Sử dụng MySQL CLI
```bash
# Đăng nhập MySQL
mysql -u root -p

# Chạy file SQL
source /Users/vinhdv/Documents/Clone/AI-Traffic-Monitoring-System/database_schema.sql;
```

### Cách 2: Sử dụng lệnh trực tiếp
```bash
mysql -u root -p < database_schema.sql
```

### Cách 3: Sử dụng phpMyAdmin
1. Mở phpMyAdmin (http://localhost/phpmyadmin)
2. Chọn tab "Import"
3. Chọn file `database_schema.sql`
4. Click "Go"

## 2. Xác minh Database

Sau khi import, kiểm tra các bảng đã được tạo:

```sql
USE giam_sat;

-- Kiểm tra các bảng
SHOW TABLES;

-- Kiểm tra dữ liệu mẫu
SELECT * FROM nguoi_dung;
SELECT * FROM tai_xe;
SELECT * FROM tuyen_duong;
SELECT * FROM phuong_tien;
SELECT * FROM canh_bao_vi_pham;
SELECT * FROM thong_bao_admin;

-- Thống kê nhanh
SELECT 
    (SELECT COUNT(*) FROM nguoi_dung) AS total_users,
    (SELECT COUNT(*) FROM tai_xe) AS total_drivers,
    (SELECT COUNT(*) FROM tuyen_duong) AS total_routes,
    (SELECT COUNT(*) FROM phuong_tien) AS total_vehicles,
    (SELECT COUNT(*) FROM canh_bao_vi_pham) AS total_alerts,
    (SELECT COUNT(*) FROM thong_bao_admin) AS total_admin_warnings;
```

## 3. Cấu hình Flask Application

Database đã được cấu hình trong `drive_auth.py`:

```python
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'giam_sat'
```

## 4. Chạy Ứng Dụng

```bash
# Kích hoạt virtual environment
source .venv/bin/activate  # macOS/Linux
# hoặc
.venv\Scripts\activate  # Windows

# Chạy Flask app
cd py/Web
python drive_auth.py
```

Truy cập: http://localhost:5000

## 5. Tài Khoản Đăng Nhập Mặc Định

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |
| user | user123 | user |

**Lưu ý:** Password đã được hash bằng bcrypt. Nếu muốn đổi password, tạo hash mới:

```python
from flask_bcrypt import Bcrypt
bcrypt = Bcrypt()
password_hash = bcrypt.generate_password_hash('your_password').decode('utf-8')
print(password_hash)
```

Sau đó cập nhật trong database:

```sql
UPDATE nguoi_dung 
SET mat_khau = 'hash_mới' 
WHERE ten_dang_nhap = 'admin';
```

## 6. API Endpoints Đã Thêm

### Dashboard Summary
```
GET /api/dashboard/summary
```
Trả về thống kê tổng quan cho KPIs.

### Vehicles
```
GET /api/dashboard/vehicles
```
Lấy danh sách phương tiện.

### Drivers
```
GET /api/dashboard/drivers
```
Lấy danh sách tài xế.

### Routes
```
GET /api/dashboard/routes
```
Lấy danh sách tuyến đường.

### Recent Alerts
```
GET /api/dashboard/alerts/recent
```
Lấy 10 cảnh báo gần nhất.

### Recent Admin Warnings
```
GET /api/dashboard/admin-warnings/recent
```
Lấy 10 thông báo admin gần nhất.

## 7. Xử Lý Sự Cố

### Lỗi: Database không tồn tại
```sql
CREATE DATABASE giam_sat DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Lỗi: Access denied
```sql
-- Cấp quyền cho user
GRANT ALL PRIVILEGES ON giam_sat.* TO 'root'@'localhost' IDENTIFIED BY '';
FLUSH PRIVILEGES;
```

### Lỗi: Foreign key constraint
```sql
-- Tạm thời tắt foreign key checks
SET FOREIGN_KEY_CHECKS = 0;
-- Import lại database
-- Bật lại foreign key checks
SET FOREIGN_KEY_CHECKS = 1;
```

## 8. Backup Database

```bash
# Backup toàn bộ database
mysqldump -u root -p giam_sat > giam_sat_backup.sql

# Backup chỉ cấu trúc
mysqldump -u root -p --no-data giam_sat > giam_sat_structure.sql

# Backup chỉ dữ liệu
mysqldump -u root -p --no-create-info giam_sat > giam_sat_data.sql
```

## 9. Khôi Phục Database

```bash
mysql -u root -p giam_sat < giam_sat_backup.sql
```
