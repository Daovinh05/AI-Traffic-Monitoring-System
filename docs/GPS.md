# GPS và định tuyến theo địa chỉ

## 1. Mục tiêu

Chức năng thêm tuyến đường cho phép quản trị viên:

1. Nhập địa chỉ điểm đi và điểm đến.
2. Dùng GPS của trình duyệt làm điểm đi nếu cần.
3. Chuyển địa chỉ thành tọa độ.
4. Tìm đường lái xe thực tế.
5. Xem trước tuyến trên bản đồ.
6. Tự động tính khoảng cách và thời gian.
7. Lưu toàn bộ đường đi vào MySQL.

Hệ thống không nối thẳng điểm đầu và điểm cuối. Đường được lấy theo mạng lưới
giao thông, vì vậy polyline bám theo đường bộ.

## 2. Công nghệ sử dụng

| Thành phần | Vai trò |
|---|---|
| Leaflet | Thư viện JavaScript hiển thị và thao tác với bản đồ |
| OpenStreetMap | Cung cấp các ô ảnh nền bản đồ |
| Nominatim | Chuyển địa chỉ thành tọa độ GPS |
| OSRM | Tìm đường lái xe giữa các tọa độ |
| Flask | Cung cấp API trung gian cho frontend |
| MySQL | Lưu thông tin tuyến và toàn bộ các điểm của đường đi |

Luồng xử lý tổng quát:

```text
Người dùng nhập địa chỉ
        |
        v
Frontend gọi POST /api/routes/plan
        |
        v
Nominatim chuyển địa chỉ thành GPS
        |
        v
OSRM tìm đường lái xe thực tế
        |
        v
Backend trả path, khoảng cách, thời gian
        |
        v
Leaflet vẽ đường lên OpenStreetMap
        |
        v
Người dùng xác nhận và lưu vào MySQL
```

## 3. Các file liên quan

### Frontend

```text
frontend/legacy-templates/Dashboard.html
```

File này chứa:

- Modal thêm tuyến.
- Trường nhập điểm đi và điểm đến.
- Nút lấy GPS hiện tại.
- Nút tìm đường.
- Bản đồ xem trước.
- Logic gửi tuyến xuống backend để lưu.

### Backend API

```text
backend/app/api/route_routes.py
```

File này định nghĩa:

- `POST /api/routes/plan`: tìm đường theo địa chỉ.
- `POST /api/routes`: lưu tuyến mới.
- `GET /api/routes`: lấy danh sách tuyến.
- `GET /api/routes/<route_id>`: lấy chi tiết tuyến.
- `PUT /api/routes/<route_id>`: cập nhật tuyến.
- `DELETE /api/routes/<route_id>`: xóa tuyến.

### Business logic

```text
backend/app/services/route_service.py
```

File này:

- Gọi Nominatim.
- Gọi OSRM.
- Chuẩn hóa dữ liệu trả về.
- Kiểm tra tọa độ, khoảng cách, thời gian và trạng thái.

### Repository

```text
backend/app/repositories/route_repository.py
```

File này lưu:

- Thông tin chung vào bảng `tuyen_duong`.
- Các điểm của polyline vào bảng `tuyen_duong_path`.

## 4. Leaflet và OpenStreetMap

Leaflet được nạp trong phần `<head>` của `Dashboard.html`:

```html
<link
  rel="stylesheet"
  href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

Khởi tạo bản đồ xem trước:

```javascript
newRoutePreviewMap = L.map('newRoutePreviewMap')
  .setView([21.0285, 105.8542], 12);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap contributors'
}).addTo(newRoutePreviewMap);
```

Giải thích:

- `L.map(...)` tạo một bản đồ Leaflet.
- `[21.0285, 105.8542]` là vị trí mặc định tại Hà Nội.
- `12` là mức phóng to.
- `L.tileLayer(...)` lấy ảnh nền từ OpenStreetMap.

OpenStreetMap chỉ cung cấp lớp nền bản đồ trong đoạn này. Nó không tự tìm
đường lái xe.

## 5. Nhập địa chỉ

Modal có trường điểm đến và hai cách chọn điểm đi:

- **Nhập địa chỉ:** dùng ô nhập địa chỉ thủ công.
- **Dùng GPS:** hiển thị tọa độ trong một ô riêng chỉ đọc.

Hai chế độ tách biệt giúp GPS không ghi đè địa chỉ người dùng đã nhập.

```html
<input
  id="newRouteStartAddress"
  name="start_address"
  type="text"
  placeholder="Ví dụ: 207 Phố Triều Khúc, Thanh Xuân, Hà Nội"
>

<input
  id="newRouteStartGps"
  type="text"
  placeholder="Chưa lấy vị trí GPS"
  readonly
>

<input
  id="newRouteEndAddress"
  name="end_address"
  type="text"
  placeholder="Ví dụ: Bến xe Mỹ Đình, Nam Từ Liêm, Hà Nội"
  required
>
```

Người dùng cần nhập địa chỉ đủ rõ, nên có:

- Số nhà hoặc địa điểm.
- Tên đường.
- Quận/huyện.
- Tỉnh/thành phố.

Ví dụ:

```text
207 Phố Triều Khúc, Thanh Xuân, Hà Nội
Bến xe Mỹ Đình, Nam Từ Liêm, Hà Nội
```

## 6. Lấy vị trí GPS của trình duyệt

Nút GPS gọi hàm:

```javascript
function useCurrentLocationForRoute() {
  navigator.geolocation.getCurrentPosition(
    position => {
      const latitude = position.coords.latitude.toFixed(6);
      const longitude = position.coords.longitude.toFixed(6);

      document.getElementById('newRouteStartGps').value =
        `${latitude}, ${longitude}`;
    }
  );
}
```

Trình duyệt sẽ yêu cầu người dùng cấp quyền vị trí.

Điều kiện thường cần:

- Website chạy trên `localhost`; hoặc
- Website chạy bằng HTTPS.

Kết quả GPS được ghi vào ô GPS riêng theo dạng:

```text
20.979660, 105.802090
```

Backend nhận biết chuỗi này là tọa độ nên không gọi Nominatim lại.

Trước khi tìm đường, frontend chọn giá trị theo chế độ đang bật:

```javascript
function getRouteStartValue() {
  const mode = document.querySelector(
    'input[name="start_mode"]:checked'
  )?.value;

  return mode === 'gps'
    ? document.getElementById('newRouteStartGps').value.trim()
    : document.getElementById('newRouteStartAddress').value.trim();
}
```

## 7. Frontend gửi yêu cầu tìm đường

Khi người dùng bấm **Tìm đường GPS**, hàm `planNewRoute()` chạy:

```javascript
const response = await fetch('/api/routes/plan', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    start_address: startAddress,
    end_address: endAddress
  })
});
```

Request mẫu:

```json
{
  "start_address": "207 Phố Triều Khúc, Thanh Xuân, Hà Nội",
  "end_address": "Bến xe Mỹ Đình, Hà Nội"
}
```

Frontend không gọi trực tiếp Nominatim hoặc OSRM. Backend thực hiện việc đó để:

- Tránh lỗi CORS.
- Quản lý timeout và lỗi tập trung.
- Thêm cache.
- Giới hạn tần suất gọi Nominatim.
- Không để logic dịch vụ bản đồ phân tán trong trình duyệt.

## 8. API lập tuyến của Flask

Endpoint được định nghĩa trong `route_routes.py`:

```python
@login_required
def plan_route():
    if session.get("role") != "admin":
        return jsonify(
            success=False,
            message="Không có quyền truy cập",
        ), 403

    data = request.get_json(silent=True) or {}
    plan = route_service.plan_route(
        data.get("start_address"),
        data.get("end_address"),
    )
    return jsonify(success=True, plan=plan)
```

Đăng ký route:

```python
AppRoute(
    "/api/routes/plan",
    "plan_route",
    "plan_route",
    ("POST",),
    handler=plan_route,
)
```

Chỉ tài khoản Admin được phép gọi API này.

## 9. Nominatim chuyển địa chỉ thành GPS

URL dịch vụ được khai báo trong `route_service.py`:

```python
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
```

Hàm `_geocode(address)` thực hiện chuyển đổi.

Request chính:

```python
results = _get_json(
    NOMINATIM_URL,
    {
        "q": candidate,
        "format": "jsonv2",
        "limit": 1,
        "countrycodes": "vn",
        "addressdetails": 1,
    },
)
```

Ý nghĩa tham số:

| Tham số | Ý nghĩa |
|---|---|
| `q` | Địa chỉ cần tìm |
| `format=jsonv2` | Yêu cầu kết quả JSON |
| `limit=1` | Chỉ lấy kết quả phù hợp nhất |
| `countrycodes=vn` | Giới hạn tìm kiếm trong Việt Nam |
| `addressdetails=1` | Trả thêm thông tin địa chỉ |

Kết quả được chuyển thành:

```python
result = {
    "address": results[0]["display_name"],
    "lat": float(results[0]["lat"]),
    "lng": float(results[0]["lon"]),
}
```

Ví dụ:

```json
{
  "address": "Phố Triều Khúc, Thanh Liệt, Hà Nội, Việt Nam",
  "lat": 20.9858499,
  "lng": 105.798446
}
```

### Tìm kiếm địa chỉ linh hoạt

Địa chỉ tại Việt Nam đôi khi không được Nominatim nhận diện khi có quá nhiều
thành phần. Hệ thống thử thêm biến thể rút gọn:

```python
address_parts = [
    part.strip()
    for part in address.split(",")
    if part.strip()
]

candidates = [address]

if len(address_parts) >= 2:
    candidates.append(
        f"{address_parts[0]}, {address_parts[-1]}, Việt Nam"
    )
```

Ví dụ:

```text
207 Phố Triều Khúc, Thanh Xuân, Hà Nội
```

có thể được thử lại thành:

```text
207 Phố Triều Khúc, Hà Nội, Việt Nam
```

### Cache và giới hạn tần suất

Hệ thống lưu kết quả địa chỉ trong bộ nhớ:

```python
_geocode_cache = {}
```

Nếu địa chỉ đã được tìm trước đó, kết quả được lấy từ cache:

```python
if cache_key in _geocode_cache:
    return _geocode_cache[cache_key]
```

Hệ thống cũng chờ ít nhất khoảng một giây giữa các request Nominatim:

```python
wait_time = 1.05 - (
    time.monotonic() - _last_geocode_request
)

if wait_time > 0:
    time.sleep(wait_time)
```

Điều này giúp tuân thủ giới hạn của máy chủ Nominatim công cộng.

## 10. OSRM tìm đường lái xe

Sau khi có tọa độ điểm đi và điểm đến, hệ thống gọi OSRM.

URL dịch vụ:

```python
OSRM_URL = (
    "https://router.project-osrm.org/route/v1/driving"
)
```

OSRM sử dụng thứ tự:

```text
kinh độ,vĩ độ
```

Vì vậy code tạo chuỗi:

```python
coordinates = (
    f"{start['lng']},{start['lat']};"
    f"{end['lng']},{end['lat']}"
)
```

Request:

```python
result = _get_json(
    f"{OSRM_URL}/{coordinates}",
    {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    },
)
```

Ý nghĩa tham số:

| Tham số | Ý nghĩa |
|---|---|
| `driving` | Tìm đường dành cho phương tiện |
| `overview=full` | Trả toàn bộ hình dạng đường đi |
| `geometries=geojson` | Trả geometry theo GeoJSON |
| `steps=false` | Không cần hướng dẫn rẽ từng bước |

## 11. Chuyển dữ liệu OSRM cho Leaflet

GeoJSON của OSRM trả tọa độ theo thứ tự:

```text
[kinh độ, vĩ độ]
```

Leaflet sử dụng:

```text
[vĩ độ, kinh độ]
```

Vì vậy cần đảo vị trí:

```python
path = [
    [float(latitude), float(longitude)]
    for longitude, latitude
    in route["geometry"]["coordinates"]
]
```

Backend trả:

```python
return {
    "start": start,
    "end": end,
    "path": path,
    "distance": round(
        float(route["distance"]) / 1000,
        1,
    ),
    "duration": max(
        1,
        round(float(route["duration"]) / 60),
    ),
}
```

OSRM trả khoảng cách theo mét và thời gian theo giây, nên:

- Khoảng cách được chia `1000` để thành km.
- Thời gian được chia `60` để thành phút.

Response mẫu:

```json
{
  "success": true,
  "plan": {
    "start": {
      "address": "Phố Triều Khúc, Hà Nội, Việt Nam",
      "lat": 20.9858499,
      "lng": 105.798446
    },
    "end": {
      "address": "Bến xe Mỹ Đình, Hà Nội, Việt Nam",
      "lat": 21.028735,
      "lng": 105.778297
    },
    "distance": 8.1,
    "duration": 10,
    "path": [
      [20.98593, 105.79841],
      [20.98602, 105.79855],
      [20.98618, 105.79879]
    ]
  }
}
```

Trong thử nghiệm thực tế của dự án, một tuyến dài khoảng `8.1 km` trả về
`201` điểm. Vì có nhiều điểm nên đường vẽ bám theo mạng lưới đường giao thông,
không phải đường thẳng.

## 12. Vẽ tuyến trên bản đồ

Frontend nhận `plan.path` và vẽ bằng Leaflet:

```javascript
newRoutePreviewLine = L.polyline(plan.path, {
  color: document
    .getElementById('newRouteColor')
    .value,
  weight: 6,
  opacity: 0.9
}).addTo(newRoutePreviewMap);
```

Thêm marker điểm đầu và cuối:

```javascript
L.marker(plan.path[0])
  .addTo(newRoutePreviewMap)
  .bindPopup(`Điểm đi: ${plan.start.address}`);

L.marker(plan.path[plan.path.length - 1])
  .addTo(newRoutePreviewMap)
  .bindPopup(`Điểm đến: ${plan.end.address}`);
```

Điều chỉnh bản đồ để nhìn thấy toàn bộ tuyến:

```javascript
newRoutePreviewMap.fitBounds(
  newRoutePreviewLine.getBounds(),
  { padding: [30, 30] }
);
```

## 13. Tự động điền khoảng cách và thời gian

Sau khi API trả kết quả:

```javascript
document.getElementById('newRouteDistance').value =
  plan.distance;

document.getElementById('newRouteDuration').value =
  plan.duration;
```

Thông tin tóm tắt cũng được cập nhật:

```javascript
document.getElementById(
  'newRoutePlanDistance'
).textContent = `${plan.distance} km`;

document.getElementById(
  'newRoutePlanDuration'
).textContent = `${plan.duration} phút`;
```

## 14. Lưu tuyến vào MySQL

Sau khi người dùng xem trước và bấm **Lưu tuyến mới**, frontend gửi:

```javascript
const payload = {
  id: routeCode,
  name: routeName,
  description: description,
  distance: plan.distance,
  duration: plan.duration,
  vehicles: vehicles,
  color: color,
  status: status,
  path: plan.path
};

await fetch('/api/routes', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(payload)
});
```

Thông tin chung được lưu trong bảng:

```text
tuyen_duong
```

Các điểm của polyline được lưu trong:

```text
tuyen_duong_path
```

Repository lấy điểm đầu và cuối:

```python
start_lat, start_lng = path[0]
end_lat, end_lng = path[-1]
```

Sau đó lưu từng điểm:

```python
for index, (lat, lng) in enumerate(path, start=1):
    cur.execute(
        """
        INSERT INTO tuyen_duong_path
            (id_tuyen_duong, point_order,
             latitude, longitude)
        VALUES (%s, %s, %s, %s)
        """,
        (route_id, index, lat, lng),
    )
```

`point_order` giữ đúng thứ tự các điểm để khi đọc lại, đường được nối chính
xác như OSRM đã trả.

## 15. Vì sao không cần Google Maps API key?

Chức năng đang dùng các dịch vụ mở:

- OpenStreetMap: ảnh nền bản đồ.
- Nominatim: tìm tọa độ theo địa chỉ.
- OSRM: tìm đường lái xe.
- Leaflet: hiển thị bản đồ.

Không có request nào gửi tới:

```text
maps.googleapis.com
```

Do đó không cần:

```text
GOOGLE_MAPS_API_KEY
```

Tuy nhiên, các máy chủ Nominatim và OSRM công cộng phù hợp cho:

- Học tập.
- Demo.
- Phát triển.
- Lưu lượng nhỏ.

Với hệ thống production có nhiều người dùng, nên:

- Tự triển khai Nominatim và OSRM; hoặc
- Dùng nhà cung cấp bản đồ có SLA và API key riêng.

## 16. Chứng chỉ SSL

Python trên một số máy macOS có thể gặp lỗi:

```text
SSL: CERTIFICATE_VERIFY_FAILED
```

Dự án sử dụng `certifi`:

```python
import certifi
import ssl

ssl_context = ssl.create_default_context(
    cafile=certifi.where()
)
```

Khi gọi HTTPS:

```python
with urlopen(
    request,
    timeout=15,
    context=ssl_context,
) as response:
    ...
```

Dependency được khai báo trong:

```text
requirements.txt
```

```text
certifi
```

Không nên xử lý lỗi SSL bằng cách tắt kiểm tra chứng chỉ.

## 17. Cách chạy

Kích hoạt môi trường:

```bash
source .venv/bin/activate
```

Chạy backend:

```bash
.venv/bin/python -m backend.app.main
```

Chạy frontend ở terminal khác:

```bash
cd frontend
npm run dev
```

Mở:

```text
http://localhost:3001/dashboard
```

Sau đó:

1. Chọn **Quản lý tuyến đường**.
2. Bấm **Thêm tuyến mới**.
3. Nhập điểm đi và điểm đến.
4. Bấm **Tìm đường GPS**.
5. Kiểm tra lộ trình trên bản đồ.
6. Bấm **Lưu tuyến mới**.

## 18. Kiểm thử API

Sau khi đăng nhập Admin, frontend gọi:

```http
POST /api/routes/plan
Content-Type: application/json
```

Body:

```json
{
  "start_address": "207 Phố Triều Khúc, Hà Nội",
  "end_address": "Bến xe Mỹ Đình, Hà Nội"
}
```

Cần kiểm tra:

- `success` bằng `true`.
- `plan.path` có nhiều hơn hai điểm.
- `distance` lớn hơn `0`.
- `duration` lớn hơn `0`.
- Đường trên bản đồ không phải đoạn thẳng.

## 19. Lỗi thường gặp

### Không tìm thấy địa chỉ

Thông báo:

```text
Không tìm thấy địa chỉ
```

Cách xử lý:

- Bổ sung tỉnh/thành phố.
- Bỏ bớt phường/quận nếu địa chỉ quá chi tiết.
- Thử tên địa điểm nổi bật.
- Kiểm tra lỗi chính tả.

### Không tìm thấy đường lái xe

Nguyên nhân có thể:

- Điểm nằm ngoài mạng lưới đường OSRM.
- Điểm nằm trong khu vực chỉ dành cho người đi bộ.
- Tọa độ GPS không chính xác.

### GPS không hoạt động

Kiểm tra:

- Trình duyệt đã được cấp quyền vị trí.
- Website chạy trên `localhost` hoặc HTTPS.
- Dịch vụ định vị của hệ điều hành đang bật.

### Lỗi kết nối dịch vụ bản đồ

Kiểm tra:

- Máy có kết nối Internet.
- Nominatim hoặc OSRM công cộng có đang hoạt động.
- Firewall không chặn HTTPS.
- `certifi` đã được cài.

### Đổi địa chỉ nhưng tuyến cũ vẫn còn

Frontend gọi `invalidateNewRoutePlan()` mỗi khi địa chỉ thay đổi. Hàm này:

- Xóa dữ liệu tuyến đã tìm.
- Ẩn khoảng cách và thời gian cũ.
- Xóa polyline và marker cũ.
- Bắt buộc người dùng bấm **Tìm đường GPS** lại.

## 20. Tài liệu tham khảo

- Nominatim Search API:
  <https://nominatim.org/release-docs/latest/api/Search/>
- Chính sách sử dụng Nominatim:
  <https://operations.osmfoundation.org/policies/nominatim/>
- OSRM Route Service:
  <https://project-osrm.org/docs/v5.24.0/api/#route-service>
- Leaflet:
  <https://leafletjs.com/reference.html>
- OpenStreetMap:
  <https://www.openstreetmap.org/>
