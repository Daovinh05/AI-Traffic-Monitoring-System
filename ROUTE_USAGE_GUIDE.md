# Hướng dẫn sử dụng Tuyến đường với Điểm đầu cuối và Đường đi chi tiết

## Tổng quan
Hệ thống bây giờ hỗ trợ hiển thị tuyến đường với **nhiều điểm tọa độ** (không chỉ 2 điểm đầu cuối) để vẽ đường đi chi tiết trên bản đồ.

## Cấu trúc dữ liệu tuyến đường

Mỗi tuyến đường có cấu trúc như sau:

```javascript
{
  code: 'T001',                              // Mã tuyến đường
  name: 'Mỹ Đình - Hải Phòng',              // Tên tuyến
  start: 'Bến xe Mỹ Đình',                  // Điểm đầu
  end: 'Bến xe Hải Phòng',                  // Điểm cuối
  distance: 102,                            // Khoảng cách (km)
  duration: 120,                            // Thời gian (phút)
  vehicles: '12 xe/ngày',                   // Số lượng xe
  status: 'Hoạt động',                      // Trạng thái
  path: [                                   // Mảng tọa độ đường đi
    [21.0300, 105.7800],                    // Điểm 1 (điểm đầu)
    [21.0250, 105.8200],                    // Điểm 2
    [21.0200, 105.8600],                    // Điểm 3
    [20.9500, 106.1000]                     // Điểm 4 (điểm cuối)
  ],
  color: '#4a9eff'                          // Màu sắc trên bản đồ
}
```

## Các tuyến đường mẫu

### T001: Mỹ Đình - Hải Phòng
- **Điểm đầu:** Bến xe Mỹ Đình
- **Điểm cuối:** Bến xe Hải Phòng
- **Khoảng cách:** 102 km
- **Thời gian:** 120 phút
- **Màu:** Xanh dương (#4a9eff)
- **Tọa độ:** 4 điểm trung gian

### T002: Nội Bài - Trung tâm Hà Nội
- **Điểm đầu:** Sân bay Nội Bài
- **Điểm cuối:** Hồ Hoàn Kiếm
- **Khoảng cách:** 28 km
- **Thời gian:** 45 phút
- **Màu:** Xanh lá (#00c853)
- **Tọa độ:** 4 điểm trung gian

### T003: Hồ Tây - Lăng Bác
- **Điểm đầu:** Hồ Tây
- **Điểm cuối:** Lăng Chủ tịch
- **Khoảng cách:** 8 km
- **Thời gian:** 25 phút
- **Màu:** Vàng (#ffc107)
- **Tọa độ:** 3 điểm trung gian

### T004: Cầu Giấy - Long Biên
- **Điểm đầu:** Cầu Giấy
- **Điểm cuối:** Long Biên
- **Khoảng cách:** 15 km
- **Thời gian:** 40 phút
- **Màu:** Đỏ (#ff5252)
- **Tọa độ:** 4 điểm trung gian

### T005: Hà Đông - Hoàn Kiếm
- **Điểm đầu:** Hà Đông
- **Điểm cuối:** Hồ Gươm
- **Khoảng cách:** 12 km
- **Thời gian:** 35 phút
- **Màu:** Tím (#9c27b0)
- **Tọa độ:** 4 điểm trung gian

## Cách sử dụng

### 1. Xem danh sách tuyến đường
- Vào Dashboard → Chọn menu "Tuyến đường"
- Xem danh sách các tuyến với thông tin chi tiết

### 2. Xem chi tiết trên bản đồ
- Click nút **"Xem"** trên mỗi tuyến
- Bản đồ sẽ hiển thị:
  - **Đường kẻ nét đứt** nối các điểm tọa độ
  - **Marker xanh** (📍) tại điểm đầu
  - **Marker đỏ** (🏁) tại điểm cuối
  - Popup thông tin khi click vào marker

### 3. Thêm tuyến đường mới

Để thêm tuyến đường mới, thêm vào mảng `routesData` trong `Dashboard.html`:

```javascript
var routesData = [
  // ... các tuyến hiện có ...
  { 
    code: 'T006', 
    name: 'Tên tuyến mới', 
    start: 'Điểm đầu', 
    end: 'Điểm cuối', 
    distance: 50, 
    duration: 60, 
    vehicles: '10 xe/ngày', 
    status: 'Hoạt động',
    path: [
      [21.0100, 105.8000],  // Tọa độ điểm 1
      [21.0200, 105.8100],  // Tọa độ điểm 2
      [21.0300, 105.8200]   // Tọa độ điểm 3
    ], 
    color: '#ff9800' 
  }
];
```

## Cách lấy tọa độ các điểm

### Sử dụng Google Maps:
1. Mở Google Maps
2. Click chuột phải vào vị trí muốn lấy tọa độ
3. Tọa độ sẽ hiển thị ở đầu popup (ví dụ: `21.0285, 105.8542`)
4. Click vào tọa độ để copy

### Sử dụng trang web tọa độ:
- https://www.latlong.net/
- https://coordinatesfinder.com/

## Lưu ý

1. **Thứ tự tọa độ:** `[vĩ độ, kinh độ]` (lat, lng)
2. **Số lượng điểm:** Tối thiểu 2 điểm (đầu và cuối), có thể thêm nhiều điểm trung gian
3. **Màu sắc:** Sử dụng mã hex color (#RRGGBB)
4. **Trạng thái:** 'Hoạt động' hoặc 'Ngừng hoạt động'

## Chuyển đổi giữa dữ liệu mẫu và database

### Dùng dữ liệu mẫu (mặc định):
```javascript
var routesData = [
  { code: 'T001', ... },  // Các tuyến mẫu
];
// var routesData = {{ routes|default([], true)|tojson|safe }};  // Comment dòng này
```

### Dùng dữ liệu từ database:
```javascript
// var routesData = [ ... ];  // Comment dữ liệu mẫu
var routesData = {{ routes|default([], true)|tojson|safe }};  // Bỏ comment dòng này
```

## API Endpoints (nếu dùng database)

- `GET /api/routes` - Lấy tất cả tuyến đường
- `GET /api/routes/<id>` - Lấy chi tiết tuyến
- `POST /api/routes` - Tạo mới tuyến
- `PUT /api/routes/<id>` - Cập nhật tuyến
- `DELETE /api/routes/<id>` - Xóa tuyến

## Hỗ trợ

Nếu cần trợ giúp, liên hệ với quản trị viên hệ thống.
