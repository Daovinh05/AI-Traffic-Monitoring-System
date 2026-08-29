# Chỉnh độ nhạy và thuật toán nhận diện

## Tổng quan

Hệ thống giám sát tài xế gồm **6 module phát hiện hành vi** và **4 module giám sát môi trường**.
Mỗi module có các ngưỡng (threshold), tham số thời gian (duration) và cơ chế chống lặp (cooldown)
riêng. Tất cả tham số được khai báo trong `backend/app/ai/runtime.py`.

---

## 1. Module phát hiện nhắm mắt (Eye Closure Detection)

### Thuật toán

Sử dụng `dlib.get_frontal_face_detector()` để phát hiện khuôn mặt, sau đó dùng
`dlib.shape_predictor()` (68-point facial landmarks) để lấy tọa độ 6 điểm mốc quanh mỗi mắt.

Công thức **Eye Aspect Ratio (EAR)**:

```
EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
```

Trong đó:
- `p1, p4`: góc mắt trái/phải (index 36, 39 cho mắt trái; 42, 45 cho mắt phải)
- `p2-p3`: điểm trên mí mắt
- `p5-p6`: điểm dưới mí mắt

Chỉ số PERCLOS:

```
PERCLOS = (N_closed / N_window) * 100%
```
với `N_window = 150 frame` (~7.5 giây).

### Ngưỡng và tham số

| Tham số | Giá trị | File code |
|---------|---------|-----------|
| `EAR_THRESHOLD` | **0.30** | runtime.py:237 |
| `EAR_MIN_DURATION` | **2 giây** | runtime.py:238 |
| `N_window` (PERCLOS) | 150 frame | --- |
| Ngưỡng PERCLOS cảnh báo | > 15% | --- |

### Luồng xử lý (`runtime.py:924-939`)

1. Tính EAR cho mắt trái và mắt phải
2. `EAR_avg = (EAR_left + EAR_right) / 2.0`
3. Nếu `EAR < 0.30`:
   - Bắt đầu đếm thời gian `eye_closed_time`
   - Nếu `eye_closed_time > 2 giây`:
     - Phát âm thanh `nham_mat.wav`
     - Gửi cảnh báo "NHẮM MẮT QUÁ LÂU!"
4. Nếu `EAR >= 0.30`: reset `eye_closed_time = None`

### Cách chỉnh độ nhạy

- **Giảm `EAR_THRESHOLD`** (vd: 0.25): Chỉ cảnh báo khi mắt nhắm gần hết, giảm dương tính giả
- **Tăng `EAR_THRESHOLD`** (vd: 0.35): Cảnh báo sớm hơn, tăng độ nhạy nhưng dễ cảnh báo nhầm khi chớp mắt
- **Tăng `EAR_MIN_DURATION`** (vd: 3s): Giảm cảnh báo nhầm khi chớp mắt lúc mệt
- **Giảm `EAR_MIN_DURATION`** (vd: 1.5s): Phát hiện buồn ngủ sớm hơn nhưng dễ nhầm

---

## 2. Module phát hiện ngáp (Yawn Detection)

### Thuật toán

Tính **Mouth Aspect Ratio (MAR)** từ 10 điểm mốc môi trong 68-point facial landmarks:

```
MAR = avg(bottom_lip[56,57,58,65,66].y) - avg(top_lip[50,51,52,61,62].y)
```

Khi miệng mở rộng (ngáp), `MAR` tăng đột biến.

### Ngưỡng và tham số

| Tham số | Giá trị | File code |
|---------|---------|-----------|
| `YAWN_THRESHOLD` | **25 pixel** | runtime.py:239 |
| `YAWN_CONSEC_FRAMES` | **15 frame** | runtime.py:240 |
| Khoảng thời gian | 15 frame @ 20 FPS = **0.75 giây** | --- |

### Luồng xử lý (`runtime.py:941-955`)

1. Tính `MAR`
2. Nếu `MAR > 25px`: tăng `counter_yawn`
3. Nếu `counter_yawn >= 15`:
   - Phát âm thanh `ngap_ngu.wav`
   - Cảnh báo "NGÁP NGỦ!"
4. Nếu `MAR <= 25px`: reset `counter_yawn = 0`

### Cách chỉnh độ nhạy

- **Giảm `YAWN_THRESHOLD`** (vd: 20): Phát hiện cả ngáp nhẹ (dễ dương tính giả)
- **Tăng `YAWN_THRESHOLD`** (vd: 30): Chỉ phát hiện ngáp lớn (bỏ sót ngáp nhỏ)
- **Giảm `YAWN_CONSEC_FRAMES`** (vd: 10): Phản ứng nhanh hơn nhưng dễ nhầm nói chuyện với ngáp
- **Tăng `YAWN_CONSEC_FRAMES`** (vd: 20): Chỉ cảnh báo khi ngáp thực sự kéo dài

---

## 3. Module phát hiện mất tập trung (Head Pose Estimation)

### Thuật toán

Sử dụng thuật toán **solvePnP** (Perspective-n-Point) của OpenCV với mô hình khuôn mặt 3D
gồm 6 điểm mốc:

| Điểm mốc 2D (dlib index) | Tọa độ 3D (model_points) |
|--------------------------|--------------------------|
| Mũi (30) | (0.0, 0.0, 0.0) |
| Cằm (8) | (0.0, -330.0, -65.0) |
| Khóe mắt trái (36) | (-225.0, 170.0, -135.0) |
| Khóe mắt phải (45) | (225.0, 170.0, -135.0) |
| Khóe miệng trái (48) | (-150.0, -150.0, -125.0) |
| Khóe miệng phải (54) | (150.0, -150.0, -125.0) |

Ma trận camera `K`:

```
K = [[f, 0, cx],
     [0, f, cy],
     [0, 0, 1]]
```

với `f = frame_width`, `(cx, cy) = (f/2, frame_height/2)`

Kết quả decompose ra 3 góc Euler:
- **Pitch**: gật gù lên xuống
- **Yaw**: quay trái/phải
- **Roll**: nghiêng đầu

Hiệu chỉnh wrapping:
```
if pitch > 90:  pitch -= 180
if pitch < -90: pitch += 180
# tương tự với yaw, roll
```

### Ngưỡng và tham số

| Tham số | Giá trị | File code |
|---------|---------|-----------|
| Ngưỡng **yaw** | **> 40 độ** | runtime.py:960 |
| Ngưỡng **pitch** | **> 35 độ** | runtime.py:960 |
| Ngưỡng roll | Không dùng cho cảnh báo | --- |

### Luồng xử lý (`runtime.py:957-965`)

1. Gọi `get_head_pose(points, frame.shape)`:
   - `pitch, yaw, roll = cv2.solvePnP(model_points, image_points, K, dist_coeffs)`
   - Chuyển rvec → Rodrigues → decomposeProjectionMatrix
2. Nếu `|yaw| > 40°` hoặc `pitch > 35°`:
   - Phát âm thanh `chuylaixe.wav`
   - Cảnh báo "MẤT TẬP TRUNG !"

### Cách chỉnh độ nhạy

- **Giảm ngưỡng yaw** (vd: 30°): Cảnh báo khi chỉ hơi quay đầu, phù hợp tài xế mới
- **Tăng ngưỡng yaw** (vd: 50°): Bỏ qua các lần quay đầu ngắn
- **Giảm ngưỡng pitch** (vd: 25°): Cảnh báo khi cúi nhìn điện thoại hoặc bảng đồ
- **Tăng ngưỡng pitch** (vd: 45°): Chỉ cảnh báo khi ngửa đầu nhiều (ngáp lớn hoặc mệt)

---

## 4. Module phát hiện điện thoại (Phone Detection)

### Thuật toán

Dùng **YOLOv8n** tiền huấn luyện trên COCO, phát hiện lớp "cell phone" (class 67).

Loss function YOLOv8:

```
L = λ_coord * ΣΣ1_obj[(x-x̂)^2 + (y-ŷ)^2 + (w-ŵ)^2 + (h-ĥ)^2]
    + λ_obj * ΣΣ1_obj(C-Ĉ)^2
    + λ_class * ΣΣ1_objΣ(p(c)-p̂(c))^2
```

Trong đó:
- `1_obj` = 1 nếu ô lưới chứa vật thể
- `(x,y,w,h)`: bounding box
- `C`: confidence score
- `p(c)`: class probability

### Ngưỡng và tham số

| Tham số | Giá trị | File code |
|---------|---------|-----------|
| `conf` | **> 0.5** | runtime.py:983 |
| Model | `yolov8n.pt` | runtime.py:196 |
| Kỹ thuật | Fine-tuning + Transfer learning | --- |
| Input size | 640×640 | --- |

### Luồng xử lý (`runtime.py:975-991`)

1. `results = phone_model(frame)`
2. Duyệt từng box:
   - Lọc lớp chứa "phone"
   - Nếu `conf > 0.5`:
     - Phát âm thanh `not_phone.wav`
     - Cảnh báo "DÙNG ĐIỆN THOẠI!"
     - Vẽ bounding box đỏ

### Cách chỉnh độ nhạy

- **Giảm `conf`** (vd: 0.3): Phát hiện cả khi camera xa hoặc thiếu sáng
- **Tăng `conf`** (vd: 0.7): Giảm dương tính giả, chỉ cảnh báo khi chắc chắn

---

## 5. Module phát hiện dây an toàn (Seatbelt Detection)

### Thuật toán

Dùng YOLOv8 custom (`day_an_toan.pt`) huấn luyện trên 1.200 ảnh cabin.
Nhận diện lớp "seat_belt" với ngưỡng `conf > 0.5`.

### Ngưỡng và tham số

| Tham số | Giá trị | File code |
|---------|---------|-----------|
| `conf` | **> 0.5** | runtime.py:1002 |
| Model | `day_an_toan.pt` | runtime.py:203 |
| Dataset | 1.200 ảnh, 6 góc nhìn | --- |
| mAP50 | 0.892 | --- |

### Luồng xử lý (`runtime.py:993-1010+`)

1. `seatbelt_model.predict(frame)`
2. Duyệt từng box:
   - Nếu lớp "seat_belt" với `conf > 0.5`: đánh dấu `seatbelt_detected = True`
3. Nếu `seatbelt_detected == False`:
   - Phát âm thanh `seatbelt_alert.wav`
   - Cảnh báo "KHÔNG ĐEO DÂY AN TOÀN!"

### Cách chỉnh độ nhạy

- **Giảm `conf`**: Phát hiện dây an toàn trong điều kiện thiếu sáng
- **Tăng `conf`**: Tránh nhầm lẫn với quần áo hoặc vật thể khác
- CNN-based: có thể retrain với data augmentation mới

---

## 6. Module theo dõi tay lái (Hand Tracking)

### Thuật toán

Dùng **MediaPipe Hands** (21 hand landmarks) và **MediaPipe Pose** (33 pose landmarks).

Fist score classification:

```
FistScore = Σ_{k ∈ [trỏ, giữa, áp út, út]} 1[tip_k.y > pip_k.y]
```

Nếu `FistScore >= 3` trên 4 ngón → tay đang nắm vô lăng.

### Ngưỡng và tham số

| Tham số | Giá trị | File code |
|---------|---------|-----------|
| `detectionCon` (MediaPipe) | **0.5** | runtime.py:406 |
| `warning_duration` | **3 giây** | runtime.py:415 |
| `warning_interval` | **5 giây** | runtime.py:416 |
| `FistScore >=` | **3** | runtime.py:428 |

### Luồng xử lý (`runtime.py:419-487`)

1. `hands.process(frameRGB)` → 21 hand landmarks
2. `pose.process(frameRGB)` → arm skeleton (vai-khuỷu-cổ tay)
3. Với mỗi bàn tay:
   - `is_fist()`: so sánh `tip.y > pip.y` cho 4 ngón
4. Nếu không có nắm tay (`has_fist == False`):
   - Bắt đầu đếm `no_fist_start_time`
   - Nếu `>= 3 giây`:
     - Phát `tay_lai_xe.wav`
     - Cảnh báo "KHÔNG CẦM VÔ LĂNG!"
5. Nếu có nắm tay: reset bộ đếm

### Cách chỉnh độ nhạy

- **Giảm `warning_duration`** (vd: 2s): Cảnh báo sớm hơn, phù hợp đường đông
- **Tăng `warning_duration`** (vd: 5s): Bỏ qua các thao tác ngắn (sang số, chỉnh gương)
- **Giảm FistScore** (vd: 2): Phát hiện cả khi chỉ 2 ngón trên vô lăng
- **Tăng FistScore** (vd: 4): Yêu cầu nắm chặt mới không cảnh báo

---

## 7. Các module giám sát giao thông

### 7.1. Phát hiện vật cản

| Tham số | Giá trị | File code |
|---------|---------|-----------|
| `conf` | **> 0.3** | runtime.py (logic ẩn) |
| Model | `vat_can.pt` | runtime.py:231 |
| Công thức | `distance = 2500 / box_height` | runtime.py:315 |
| Ngưỡng cảnh báo | `distance < 15m` | --- |

### 7.2. Phát hiện lệch làn

Kết hợp YOLO (lech_lan.pt) + Hough Transform cổ điển:

- ROI tam giác: `[(0, H), (W/2, H*0.6), (W, H)]`
- Canny edge: ngưỡng dưới 100, ngưỡng trên 200
- HoughLinesP: `rho=1, theta=π/180, threshold=100, minLineLength=50, maxLineGap=30`
- Lọc slope: bỏ đường có `|slope| < 0.5` (đường ngang)
- Phân loại: `slope < 0` → lane trái, `slope > 0` → lane phải
- Cảnh báo khi tổng số lane < 2 (thiếu 1 bên)

| Tham số | Giá trị |
|---------|---------|
| Canny low/high | 100 / 200 |
| Hough threshold | 100 |
| Min line length | 50 px |
| Max line gap | 30 px |
| Slope min | 0.5 |
| Margin center | ±50 px |

### 7.3. Nhận diện biển báo

| Tham số | Giá trị |
|---------|---------|
| Model | `bien_bao.pt` |
| `conf` | 0.4 |
| Input | 640×640 |
| Lọc đặc biệt | Biển tốc độ (speed) → text OCR |

### 7.4. Đếm lưu lượng phương tiện

YOLOv8 tracking với `persist=True`, đếm theo vùng đa giác.

Trạng thái giao thông dựa trên tổng số phương tiện:

| Mức | Tổng số | Màu | Thông báo |
|-----|---------|-----|-----------|
| normal | < 10 | Xanh | Thông thoáng |
| warning | 10–19 | Vàng | Hơi đông |
| danger | 20–29 | Đỏ | Có dấu hiệu tắc nghẽn |
| critical | ≥ 30 | Đỏ đậm | Kẹt xe nghiêm trọng |

---

## 8. Cơ chế chống lặp cảnh báo (Cooldown)

### Thuật toán (`runtime.py:96-119`)

```
WARNING_INTERVALS = {
    "eye": 2s,      "yawn": 3s,     "head": 3s,
    "phone": 3s,    "seatbelt": 4s, "hand": 4s
}

Hàm CAN_PLAY(warning_type):
    now = current_time()
    if now - last_warning_times[warning_type] >= WARNING_INTERVALS[warning_type]:
        last_warning_times[warning_type] = now
        return True
    return False
```

### Phân cấp mức độ cảnh báo

| Mức | Loại | Hành động |
|-----|------|-----------|
| **critical** | eye, phone, seatbelt | Cảnh báo tức thì + ghi DB + WebSocket |
| **warning** | yawn, head, hand, collision, lane, obstacle, sign | Cảnh báo + ghi DB |

### Hàng đợi cảnh báo (`runtime.py:42-74`)

- `ai_alerts_queue`: deque tối đa 50 sự kiện
- `threading.Lock()` an toàn đa luồng
- Khi thêm: tự động publish qua ai_alert_service + ghi DB + WebSocket

---

## 9. Tổng hợp tham số chỉnh độ nhạy

| Module | Tham số chính | Mặc định | Tác dụng | Nhạy ↑ | Nhạy ↓ |
|--------|--------------|----------|----------|--------|--------|
| Mắt | EAR_THRESHOLD | 0.30 | Phát hiện nhắm mắt | ↑ 0.35 | ↓ 0.25 |
| Mắt | EAR_MIN_DURATION | 2s | Thời gian nhắm liên tục | ↓ 1.5s | ↑ 3s |
| Ngáp | YAWN_THRESHOLD | 25px | Độ mở miệng tối thiểu | ↓ 20px | ↑ 30px |
| Ngáp | YAWN_CONSEC_FRAMES | 15 | Số frame mở miệng liên tục | ↓ 10 | ↑ 20 |
| Tư thế đầu | YAW_THRESH | 40° | Góc quay đầu | ↓ 30° | ↑ 50° |
| Tư thế đầu | PITCH_THRESH | 35° | Góc gật đầu | ↓ 25° | ↑ 45° |
| Điện thoại | CONF_PHONE | 0.5 | Độ tin cậy phát hiện | ↓ 0.3 | ↑ 0.7 |
| Dây an toàn | CONF_SEATBELT | 0.5 | Độ tin cậy phát hiện | ↓ 0.3 | ↑ 0.7 |
| Tay lái | warning_duration | 3s | Thời gian không nắm vô lăng | ↓ 2s | ↑ 5s |
| Tay lái | FistScore | 3 | Số ngón tay nắm | ↓ 2 | ↑ 4 |

---

## 10. Bật/tắt module theo nhu cầu

Mỗi module có thể bật/tắt riêng qua biến `warning_states` (`runtime.py:508-518`):

```python
warning_states = {
    "eye": True,        "yawn": True,       "head": True,
    "phone": True,      "seatbelt": True,   "hand": True,
    "collision": True,  "lane": True,       "obstacle": True
}
```

Khi một module tắt (`False`), toàn bộ logic phát hiện tương ứng bị bỏ qua, giúp
tiết kiệm CPU khi không cần thiết.
