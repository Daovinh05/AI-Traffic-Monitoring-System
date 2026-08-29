# Hướng dẫn thiết lập Tuyến đường với Database

## 📋 Tổng quan

Hệ thống bây giờ lưu trữ dữ liệu tuyến đường với **nhiều điểm tọa độ** trong database, cho phép hiển thị đường đi chi tiết trên bản đồ.

## 🗄️ Cấu trúc Database

### Bảng `tuyen_duong` (Lưu thông tin chung)
```sql
CREATE TABLE tuyen_duong (
  id VARCHAR(50) PRIMARY KEY,           -- Mã tuyến (T001, T002, ...)
  ten_tuyen VARCHAR(100),                -- Tên tuyến
  mo_ta TEXT,                            -- Mô tả
  start_lat DECIMAL(10,8),              -- Vĩ độ điểm đầu
  start_lng DECIMAL(11,8),              -- Kinh độ điểm đầu
  end_lat DECIMAL(10,8),                -- Vĩ độ điểm cuối
  end_lng DECIMAL(11,8),                -- Kinh độ điểm cuối
  distance DECIMAL(10,2),               -- Khoảng cách (km)
  duration INT,                         -- Thời gian (phút)
  vehicles VARCHAR(50),                 -- Số lượng xe/ngày
  route_color VARCHAR(20),              -- Màu sắc (#RRGGBB)
  toa_do_lat DECIMAL(10,8),             -- Tọa độ trung tâm (lat)
  toa_do_lng DECIMAL(11,8),             -- Tọa độ trung tâm (lng)
  trang_thai ENUM('active','waiting','offline')
);
```

### Bảng `tuyen_duong_path` (Lưu các điểm tọa độ)
```sql
CREATE TABLE tuyen_duong_path (
  id INT AUTO_INCREMENT PRIMARY KEY,
  id_tuyen_duong VARCHAR(50),           -- FK đến tuyen_duong.id
  point_order INT,                      -- Thứ tự điểm (1, 2, 3, ...)
  latitude DECIMAL(10,8),               -- Vĩ độ
  longitude DECIMAL(11,8),              -- Kinh độ
  FOREIGN KEY (id_tuyen_duong) REFERENCES tuyen_duong(id)
);
```

## 🚀 Cài đặt

### Bước 1: Chạy migration script
```bash
mysql -u root -p giam_sat < migrate_routes_full.sql
```

Hoặc chạy thủ công trong phpMyAdmin/MySQL Workbench:
```sql
USE giam_sat;
SOURCE /path/to/migrate_routes_full.sql;
```

### Bước 2: Khởi động lại Flask server
```bash
cd py/Web
python drive_auth.py
```

### Bước 3: Truy cập Dashboard
- Mở trình duyệt: `http://localhost:5001/dashboard`
- Chọn menu **Tuyến đường**
- Xem danh sách 5 tuyến mẫu với đường đi chi tiết trên bản đồ

## 📝 Thêm tuyến đường mới

### Cách 1: Thêm trực tiếp vào Database

```sql
-- 1. Thêm thông tin tuyến vào bảng tuyen_duong
INSERT INTO tuyen_duong 
(id, ten_tuyen, mo_ta, distance, duration, vehicles, route_color, trang_thai)
VALUES
('T006', 'Hà Nội - Hải Phòng', 'Tuyến đường cao tốc Hà Nội - Hải Phòng', 
 105, 90, '25 xe/ngày', '#FF5722', 'active');

-- 2. Thêm các điểm path (tọa độ)
INSERT INTO tuyen_duong_path (id_tuyen_duong, point_order, latitude, longitude) VALUES
('T006', 1, 21.0285, 105.8542),  -- Điểm đầu: Hà Nội
('T006', 2, 21.0500, 105.9000),  -- Điểm trung gian 1
('T006', 3, 21.0800, 105.9500),  -- Điểm trung gian 2
('T006', 4, 20.8648, 106.6839);  -- Điểm cuối: Hải Phòng
```

### Cách 2: Sử dụng API

```javascript
// POST /api/routes
{
  "id": "T006",
  "name": "Hà Nội - Hải Phòng",
  "description": "Tuyến đường cao tốc Hà Nội - Hải Phòng",
  "distance": 105,
  "duration": 90,
  "vehicles": "25 xe/ngày",
  "color": "#FF5722",
  "status": "active",
  "path": [
    [21.0285, 105.8542],  // Hà Nội
    [21.0500, 105.9000],  // Điểm trung gian 1
    [21.0800, 105.9500],  // Điểm trung gian 2
    [20.8648, 106.6839]   // Hải Phòng
  ]
}
```

## 🔄 Cập nhật tuyến đường

### Sử dụng API

```javascript
// PUT /api/routes/T006
{
  "name": "Hà Nội - Hải Phòng (Mới)",
  "distance": 110,
  "path": [
    [21.0285, 105.8542],  // Điểm đầu mới
    [21.0600, 105.9200],  // Điểm trung gian mới
    [20.8648, 106.6839]   // Điểm cuối
  ]
}
```

## 🗺️ Lấy tọa độ các điểm

### Google Maps
1. Mở https://maps.google.com
2. Click chuột phải vào vị trí muốn lấy tọa độ
3. Tọa độ hiển thị ở đầu popup (ví dụ: `21.0285, 105.8542`)
4. Click vào số để copy

### Công cụ online
- https://www.latlong.net/
- https://coordinatesfinder.com/
- https://www.gps-coordinates.net/

## 📊 API Endpoints

### GET /api/routes
Lấy tất cả tuyến đường với path chi tiết

**Response:**
```json
{
  "success": true,
  "routes": [
    {
      "id": "T001",
      "code": "T001",
      "name": "Mỹ Đình - Hải Phòng",
      "description": "...",
      "distance": 102,
      "duration": 120,
      "vehicles": "12 xe/ngày",
      "color": "#4a9eff",
      "status": "Hoạt động",
      "path": [
        [21.0300, 105.7800],
        [21.0250, 105.8200],
        [21.0200, 105.8600],
        [20.9500, 106.1000]
      ]
    }
  ]
}
```

### GET /api/routes/<id>
Lấy chi tiết một tuyến đường

### POST /api/routes
Tạo mới tuyến đường

### PUT /api/routes/<id>
Cập nhật tuyến đường

### DELETE /api/routes/<id>
Xóa tuyến đường

## 🎨 Màu sắc gợi ý

| Màu | Hex Code | Sử dụng cho |
|-----|----------|-------------|
| Xanh dương | `#4a9eff` | Tuyến chính |
| Xanh lá | `#00c853` | Tuyến sinh thái |
| Vàng | `#ffc107` | Tuyến du lịch |
| Đỏ | `#ff5252` | Tuyến cao tốc |
| Tím | `#9c27b0` | Tuyến nội đô |
| Cam | `#ff9800` | Tuyến ngoại ô |
| Hồng | `#e91e63` | Tuyến đặc biệt |

## ✅ Kiểm tra dữ liệu

### Xem tất cả tuyến đường
```sql
SELECT id, ten_tuyen, distance, duration, route_color, trang_thai 
FROM tuyen_duong;
```

### Xem các điểm path của một tuyến
```sql
SELECT point_order, latitude, longitude 
FROM tuyen_duong_path 
WHERE id_tuyen_duong = 'T001' 
ORDER BY point_order;
```

### Kiểm tra đầy đủ dữ liệu
```sql
SELECT 
  t.id,
  t.ten_tuyen,
  COUNT(p.id) as so_diem,
  t.start_lat,
  t.start_lng,
  t.end_lat,
  t.end_lng
FROM tuyen_duong t
LEFT JOIN tuyen_duong_path p ON t.id = p.id_tuyen_duong
GROUP BY t.id;
```

## ⚠️ Lưu ý quan trọng

1. **Thứ tự tọa độ:** Luôn là `[latitude, longitude]` (vĩ độ, kinh độ)
2. **Số điểm:** Tối thiểu 2 điểm (đầu và cuối)
3. **point_order:** Phải liên tiếp (1, 2, 3, ...)
4. **Màu sắc:** Sử dụng mã hex (#RRGGBB)
5. **Trạng thái:** 'active' (Hoạt động), 'waiting' (Chờ), 'offline' (Ngừng)

## 🔧 Xử lý sự cố

### Không hiển thị đường trên bản đồ
- Kiểm tra dữ liệu path trong database
- Đảm bảo có ít nhất 2 điểm
- F12 Console xem có lỗi JavaScript không

### Lỗi migration
```sql
-- Xóa bảng và tạo lại
DROP TABLE IF EXISTS tuyen_duong_path;
DROP TABLE IF EXISTS tuyen_duong;

-- Chạy lại migration
SOURCE migrate_routes_full.sql;
```

### Dữ liệu không đúng
```sql
-- Xóa dữ liệu cũ
DELETE FROM tuyen_duong_path;
DELETE FROM tuyen_duong;

-- Insert lại
SOURCE migrate_routes_full.sql;
```

## 📞 Hỗ trợ

Nếu cần trợ giúp:
1. Kiểm tra log Flask console
2. Kiểm tra Browser Console (F12)
3. Xem database trong phpMyAdmin
4. Liên hệ quản trị viên hệ thống

---
**Chúc bạn thành công! 🎉**
