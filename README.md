# 🚀 AI TRAFFIC MONITORING SYSTEM
> **Hệ thống giám sát tài xế bằng AI và Chatbot cảnh báo thời gian thực**

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.10-green)
![Flask](https://img.shields.io/badge/flask-2.0-red)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

## 📖 MỤC LỤC

1. [Giới thiệu](#-1-giới-thiệu)
2. [Mục tiêu hệ thống](#-2-mục-tiêu-hệ-thống)
3. [Kiến trúc hệ thống](#-3-kiến-trúc-hệ-thống)
4. [Luồng hoạt động](#-4-luồng-hoạt-động)
5. [Phân quyền người dùng](#-5-phân-quyền-người-dùng)
6. [8 Loại cảnh báo AI](#-6-8-loại-cảnh-báo-ai)
7. [Cài đặt môi trường](#-7-cài-đặt-môi-trường)
8. [Chạy ứng dụng](#-8-chạy-ứng-dụng)
9. [API Documentation](#-9-api-documentation)
10. [AI Chatbot](#-10-ai-chatbot)
11. [Docker Deployment](#-11-docker-deployment)
12. [Troubleshooting](#-12-troubleshooting)
13. [Cấu trúc dự án](#-13-cấu-trúc-dự-án)

---

## 🎯 1. GIỚI THIỆU

**AI Traffic Monitoring System** là hệ thống giám sát hành vi tài xế lái xe sử dụng trí tuệ nhân tạo (AI) để phát hiện các vi phạm và hành vi nguy hiểm, sau đó gửi cảnh báo thời gian thực đến admin và tài xế qua chatbot.

### 🌟 Tính năng chính

| Tính năng | Mô tả |
|-----------|-------|
| **AI Detection** | Phát hiện 8 loại vi phạm bằng YOLO, Dlib, MediaPipe |
| **Real-time Alerts** | Cảnh báo gửi vào chatbot trong < 1 giây |
| **Voice Commands** | Điều khiển bằng giọng nói tiếng Việt |
| **Video Recording** | Ghi hình vi phạm tự động |
| **Sound Alerts** | Phát âm thanh cảnh báo cho từng loại vi phạm |
| **Multi-camera** | Hỗ trợ webcam và video file |
| **Anti-spam** | Chống spam cảnh báo (10s/lần) |
| **Phân quyền** | Admin (Dashboard) và User (trang_chu) |
| **Two-way Communication** | Admin ↔ Chatbot ↔ Tài xế |

---

## 🎯 2. MỤC TIÊU HỆ THỐNG

### 2.1 Mục tiêu chính

```
┌─────────────────────────────────────────────────────────────┐
│  🎯 GIẢM TAI NẠN GIAO THÔNG                                  │
│     - Phát hiện sớm hành vi nguy hiểm                        │
│     - Cảnh báo kịp thời cho tài xế và admin                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  📊 GIÁM SÁT TẬP TRUNG                                       │
│     - Theo dõi nhiều xe cùng lúc                             │
│     - Dashboard trực quan với bản đồ                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  ⚡ CẢNH BÁO THỜI GIAN THỰC                                  │
│     - Độ trễ < 1 giây                                        │
│     - Chatbot tự động gửi tin                                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Đối tượng sử dụng

| Đối tượng | Lợi ích |
|-----------|---------|
| **Công ty vận tải** | Giám sát đội xe, giảm tai nạn |
| **Tài xế** | Được cảnh báo kịp thời, lái xe an toàn hơn |
| **Admin/Quản lý** | Theo dõi tập trung, xử lý vi phạm |
| **Cơ quan chức năng** | Giám sát giao thông, xử phạt |

---

## 👥 5. PHÂN QUYỀN NGƯỜI DÙNG

### 5.1 Tổng quan phân quyền

Hệ thống có **2 loại người dùng** với quyền hạn và giao diện khác nhau:

```
┌──────────────────────────────────────────────────────────────┐
│  🔐 HỆ THỐNG ĐĂNG NHẬP                                        │
│                                                              │
│  ┌─────────────────┐        ┌─────────────────┐             │
│  │   👤 ADMIN      │        │   👤 USER       │             │
│  │   (Quản lý)     │        │   (Tài xế)      │             │
│  └────────┬────────┘        └────────┬────────┘             │
│           │                          │                       │
│           ▼                          ▼                       │
│  📊 Dashboard.html          📱 trang_chu.html               │
│  - Giám sát tất cả xe       - Tư vấn cá nhân                │
│  - Xem camera               - Nhận cảnh báo từ lái_xe       │
│  - Gửi cảnh cáo             - Chat với bot                  │
│  - Thống kê, báo cáo        - Xem lịch sử vi phạm           │
│  - CRUD dữ liệu             - Nhận xử phạt từ admin         │
│  - Xử lý vi phạm            - Cải thiện hành vi             │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Admin (Dashboard.html)

#### **Chức năng chính:**

| Chức năng | Mô tả |
|-----------|-------|
| **📊 Giám sát thời gian thực** | Xem vị trí, trạng thái tất cả xe trên bản đồ |
| **📹 Xem camera** | Xem video từ 4 camera (tài xế, trước, khách, lùi) |
| **⚠️ Nhận cảnh báo AI** | Cảnh báo từ lái_xe gửi sang thời gian thực |
| **📢 Gửi cảnh cáo** | Gửi cảnh cáo, xử phạt đến tài xế |
| **🔍 Tìm kiếm** | Tìm xe theo biển số, tài xế, tuyến đường |
| **📈 Thống kê** | Báo cáo vi phạm, doanh thu, hiệu suất |
| **➕ Thêm/Sửa/Xóa** | Quản lý dữ liệu xe, tài xế, tuyến đường |
| **📤 Xuất file** | Xuất Excel, PDF báo cáo |

#### **Giao diện Dashboard:**

- **KPI Cards**: Xe hoạt động, chuyến hôm nay, cảnh báo AI, vi phạm, điểm an toàn
- **Bản đồ Leaflet**: Hiển thị vị trí 7 xe thời gian thực
- **Camera Grid**: 4 camera giám sát mỗi xe
- **Table**: Danh sách chuyến đang chạy với 13 cột thông tin
- **AI Alerts Panel**: Panel cảnh báo AI thời gian thực
- **Chatbot Widget**: Chat với AI và nhận cảnh báo

#### **Quyền hạn:**

```javascript
✅ Xem tất cả xe và tài xế
✅ Xem camera từ xa
✅ Nhận cảnh báo AI từ lái_xe
✅ Gửi cảnh cáo đến tài xế
✅ Thêm/Sửa/Xóa xe, tài xế, tuyến đường
✅ Xem thống kê, báo cáo
✅ Xuất dữ liệu Excel/PDF
✅ Tìm kiếm, lọc dữ liệu
✅ Xử lý vi phạm
```

### 5.3 User (trang_chu.html)

#### **Chức năng chính:**

| Chức năng | Mô tả |
|-----------|-------|
| **💬 Tư vấn cá nhân** | Chat với AI về thông tin cá nhân, xe |
| **⚠️ Nhận cảnh báo** | Nhận cảnh báo từ lái_xe (AI detection) |
| **📨 Nhận xử phạt** | Nhận cảnh cáo, xử phạt từ admin gửi sang |
| **📊 Xem lịch sử** | Xem lịch sử vi phạm, hành vi lái xe |
| **🎤 Chat voice** | Chat bằng giọng nói với bot |
| **📱 Mobile friendly** | Giao diện tối ưu cho mobile |

#### **Giao diện trang_chu:**

- **Chat Widget**: Chat với AI, nhận cảnh báo
- **Alert Timeline**: Timeline cảnh báo và xử phạt
- **Personal Stats**: Thống kê cá nhân (điểm an toàn, vi phạm)
- **Voice Button**: Nút chat voice
- **Profile**: Thông tin tài xế, xe

#### **Quyền hạn:**

```javascript
✅ Xem thông tin cá nhân
✅ Nhận cảnh báo từ lái_xe
✅ Nhận xử phạt từ admin
✅ Chat với AI tư vấn
✅ Xem lịch sử vi phạm cá nhân
✅ Xem điểm an toàn cá nhân
❌ KHÔNG xem được xe khác
❌ KHÔNG xem camera xe khác
❌ KHÔNG gửi cảnh cáo cho người khác
```

### 5.4 Luồng giao tiếp Admin ↔ User

```
┌──────────────────────────────────────────────────────────────┐
│  LUỒNG GIAO TIẾP 2 CHIỀU                                      │
│                                                              │
│  👤 TÀI XẾ (lái_xe.py)        🔐 ADMIN (Dashboard)          │
│         │                              │                     │
│         │  1. AI phát hiện vi phạm     │                     │
│         │─────────────────────────────>│                     │
│         │    (gửi cảnh báo sang)       │                     │
│         │                              │                     │
│         │  2. Admin xem cảnh báo       │                     │
│         │<─────────────────────────────│                     │
│         │    (hiển thị trong Dashboard)│                     │
│         │                              │                     │
│         │  3. Admin gửi cảnh cáo       │                     │
│         │<─────────────────────────────│                     │
│         │    (xử phạt, nhắc nhở)       │                     │
│         │                              │                     │
│         │  4. Tài xế nhận xử phạt      │                     │
│         │─────────────────────────────>│                     │
│         │    (hiển thị trong trang_chu)│                     │
│         │                              │                     │
│         │  5. Tài xế cải thiện         │                     │
│         │─────────────────────────────>│                     │
│         │    (giảm vi phạm, tăng điểm) │                     │
│         │                              │                     │
└──────────────────────────────────────────────────────────────┘
```

### 5.5 Phân quyền chi tiết

| Chức năng | Admin | User (Tài xế) |
|-----------|-------|---------------|
| **Xem Dashboard** | ✅ | ❌ |
| **Xem trang_chu** | ❌ | ✅ |
| **Xem tất cả xe** | ✅ | ❌ (Chỉ xem xe mình) |
| **Xem camera** | ✅ | ❌ |
| **Nhận cảnh báo AI** | ✅ | ✅ |
| **Gửi cảnh cáo** | ✅ | ❌ |
| **Nhận xử phạt** | ❌ | ✅ |
| **Thêm/Sửa/Xóa xe** | ✅ | ❌ |
| **Thống kê** | ✅ (Tất cả) | ❌ (Chỉ cá nhân) |
| **Xuất file** | ✅ | ❌ |
| **Tìm kiếm** | ✅ | ❌ |
| **Chat với AI** | ✅ | ✅ |

### 5.6 Đăng nhập và phân luồng

```python
# Backend Flask (auth_app.py)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    role = authenticate(username, password)  # 'admin' hoặc 'user'
    
    if role == 'admin':
        return redirect('/dashboard')  # Dashboard.html
    elif role == 'user':
        return redirect('/trang_chu')  # trang_chu.html
    else:
        return 'Invalid credentials'

@app.route('/dashboard')
def dashboard():
    if current_user.role != 'admin':
        return redirect('/login')
    return render_template('Dashboard.html')

@app.route('/trang_chu')
def trang_chu():
    if current_user.role != 'user':
        return redirect('/login')
    return render_template('trang_chu.html')
```

### 5.7 Ví dụ luồng hoạt động

#### **Kịch bản: Tài xế sử dụng điện thoại**

```
1. [lái_xe.py] AI phát hiện tài xế 29B-222.22 dùng điện thoại
   → add_ai_alert('phone', 'Tài xế đang DÙNG ĐIỆN THOẠI!')

2. [API] Cảnh báo gửi đến server qua API
   → POST /api/send_alert {type: 'phone', vehicle: '29B-222.22'}

3. [Dashboard.html] Admin thấy cảnh báo trong AI Alerts Panel
   → 🔔 📱 Tài xế đang DÙNG ĐIỆN THOẠI!
   → ⏰ 14:30:25 - 03/12/2024

4. [Admin] Click "Gửi cảnh cáo"
   → POST /api/send_warning {vehicle: '29B-222.22', message: 'Cảnh cáo lần 1'}

5. [trang_chu.html] Tài xế nhận được cảnh cáo
   → 📨 CẢNH CÁO TỪ ADMIN
   → Nội dung: Cảnh cáo lần 1 - Sử dụng điện thoại
   → ⏰ 14:31:00 - 03/12/2024

6. [Tài xế] Đọc cảnh cáo, cải thiện hành vi
   → Không dùng điện thoại nữa

7. [Hệ thống] Ghi nhận cải thiện
   → Điểm an toàn tăng từ 7.5 → 8.0
```

---

## 🏗️ 3. KIẾN TRÚC HỆ THỐNG

### 3.1 Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CAMERA GIÁM SÁT                               │
│                    (Webcam / Video File / IP Cam)                    │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ RTSP / USB
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND FLASK (drive.py / all_tong.py)            │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  📹 Video Capture Module                                      │   │
│  │     - Đọc frame từ camera (30 FPS)                            │   │
│  │     - Resize 1280x720                                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              ↓                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  🤖 AI Detection Module                                       │   │
│  │     - YOLOv8: Phát hiện điện thoại, dây an toàn              │   │
│  │     - Dlib 68 landmarks: Nhắm mắt, ngáp, mất tập trung       │   │
│  │     - MediaPipe: Phát hiện tay cầm vô lăng                   │   │
│  │     - Custom Logic: Va chạm, lệch làn                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              ↓                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  📢 Alert Processing Module                                   │   │
│  │     - add_ai_alert() → Lưu vào queue                          │   │
│  │     - Anti-spam logic (10s resend)                            │   │
│  │     - Phát âm thanh cảnh báo (pygame)                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              ↓                                        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  🌐 API Endpoints                                             │   │
│  │     - /api/get_ai_warnings (Polling 3s)                       │   │
│  │     - /api/get_ai_alerts_history                              │   │
│  │     - /video_feed                                             │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ HTTP/JSON
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  FRONTEND (traffic_bus.html)                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  🗺️ Leaflet Map                                               │   │
│  │     - Hiển thị vị trí 7 xe                                    │   │
│  │     - Popup thông tin xe                                      │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  💬 AI Chatbot Widget                                         │   │
│  │     - Nhận cảnh báo tự động                                   │   │
│  │     - Chat với AI (rule-based / LLM)                          │   │
│  │     - Anti-spam: 10s/gửi lại                                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  🎤 Voice Command                                             │   │
│  │     - Speech recognition tiếng Việt                           │   │
│  │     - 10+ lệnh giọng nói                                      │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Luồng dữ liệu cảnh báo

```
[Camera] → [Frame] → [AI Detection] → [Vi phạm?]
                                      ↓
                        ┌─────────────┴─────────────┐
                        │  CÓ                       │  KHÔNG
                        ↓                           ↓
              [add_ai_alert()]              [Bỏ qua]
                        ↓
              [Lưu vào ai_alerts_queue]
                        ↓
              [Phát âm thanh cảnh báo]
                        ↓
              [Frontend polling 3s]
                        ↓
              [Hiển thị trong Chatbot]
                        ↓
              [Anti-spam check (10s)]
                        ↓
              [Gửi tin đến admin]
```

---

## ⚠️ 5. 8 LOẠI CẢNH BÁO AI

### Bảng tổng quan

| # | Cảnh báo | Mức độ | AI Model | Âm thanh | Mô tả |
|---|----------|--------|----------|----------|-------|
| 1 | 👁️ **Nhắm mắt quá lâu** | 🔴 Critical | Dlib 68 landmarks | `nham_mat.wav` | Tài xế buồn ngủ, mệt mỏi, nhắm mắt > 2s |
| 2 | 😴 **Ngáp ngủ** | 🟡 Warning | Dlib 68 landmarks | `buon_ngu.wav` | Dấu hiệu mệt mỏi, MAR > 0.5 |
| 3 | 🔄 **Mất tập trung** | 🟡 Warning | Dlib 68 landmarks | `chuylaixe.wav` | Quay đầu/ngửa đầu quá mức |
| 4 | 📱 **Dùng điện thoại** | 🔴 Critical | YOLOv8 | `not_phone.wav` | Sử dụng điện thoại khi lái xe |
| 5 | ⚠️ **Không dây an toàn** | 🔴 Critical | YOLOv8 | `seatbelt_alert.wav` | Vi phạm an toàn, không đeo seatbelt |
| 6 | 🙌 **Không cầm vô lăng** | 🟡 Warning | MediaPipe Hands | `tay_lai_xe.wav` | Tay không đúng vị trí |
| 7 | 🚨 **Va chạm** | 🔴 Critical | YOLOv8 + Custom Logic | `va_cham.wav` | Phát hiện người, phương tiện, chướng ngại vật phía trước |
| 8 | ⚠️ **Lệch làn** | 🟡 Warning | YOLO + Hough Line | `lech_lan.wav` | Xe đi chệch làn đường |

### Chi tiết kỹ thuật

#### 1. 👁️ Nhắm mắt quá lâu (Eye Closure)

```python
#EAR (Eye Aspect Ratio)
EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)

# Threshold
if EAR < 0.25 for > 2 seconds:
    add_ai_alert('eye', 'NHẮM MẮT QUÁ LÂU!')
    play_sound('nham_mat.wav')
```

#### 2. 😴 Ngáp ngủ (Yawn Detection)

```python
#MAR (Mouth Aspect Ratio)
MAR = (||q2-q6|| + ||q3-q5||) / (2 * ||q1-q4||)

# Threshold
if MAR > 0.5:
    add_ai_alert('yawn', 'NGÁP NGỦ!')
    play_sound('buon_ngu.wav')
```

#### 3. 🔄 Mất tập trung (Head Pose)

```python
# Tính toán góc quay đầu từ 68 landmarks
pitch, yaw, roll = solvePnP(landmarks)

# Threshold
if abs(yaw) > 30° or abs(pitch) > 20°:
    add_ai_alert('head', 'MẤT TẬP TRUNG!')
    play_sound('chuylaixe.wav')
```

#### 4. 📱 Dùng điện thoại (Phone Detection)

```python
# YOLOv8 detection
results = model(frame)
boxes = results[0].boxes

for box in boxes:
    if class == 'cell phone' and confidence > 0.5:
        add_ai_alert('phone', 'DÙNG ĐIỆN THOẠI!')
        play_sound('not_phone.wav')
```

#### 5. ⚠️ Không dây an toàn (Seatbelt Detection)

```python
# YOLOv8 detection
results = model(frame)

if person detected and no seatbelt detected:
    add_ai_alert('seatbelt', 'KHÔNG ĐEO DÂY AN TOÀN!')
    play_sound('seatbelt_alert.wav')
```

#### 6. 🙌 Không cầm vô lăng (Hand Detection)

```python
# MediaPipe Hands
hands = mp_hands.process(frame)

if no hands detected or hands not on wheel:
    add_ai_alert('hand', 'KHÔNG CẦM VÔ LĂNG!')
    play_sound('tay_lai_xe.wav')
```

#### 7. 🚨 Va chạm (Collision Warning)

```python
# YOLOv8 detection + Custom logic
# Phát hiện: Người (person), Phương tiện (car, truck, bus, motorbike), Chướng ngại vật

results = model_vehicle(frame)

for box in results.boxes:
    label = model.names[int(box.cls[0])]
    
    if label in ['person', 'car', 'truck', 'bus', 'motorbike']:
        # Ước tính khoảng cách từ chiều cao bounding box
        distance = estimate_distance(y1, y2)
        
        # Ngưỡng khoảng cách khác nhau tùy đối tượng
        if label == 'person':
            critical_distance = 12  # Dưới 12m → Nguy hiểm
            warning_distance = 20   # Dưới 20m → Cảnh báo
            alert_message = "🚨 PHÁT HIỆN NGƯỜI TRƯỚC ĐẦU XE!"
        else:
            critical_distance = 8
            warning_distance = 15
            alert_message = "🚨 CẢNH BÁO VA CHẠM SẮP XẢY RA!"
        
        # Xử lý cảnh báo
        if distance < critical_distance:
            add_ai_alert('collision', alert_message)
            play_sound('va_cham.wav')
            color = (0, 0, 255)  # Đỏ
        elif distance < warning_distance:
            warnings['collision'] = "GIỮ KHOẢNG CÁCH!"
            color = (0, 255, 255)  # Vàng
        else:
            color = (0, 255, 0)  # Xanh lá
```

**Đối tượng phát hiện:**
- 👤 **Người (person)**: Ngưỡng an toàn cao nhất (12m/20m)
- 🚗 **Phương tiện**: Car, Truck, Bus, Motorbike
- 🚧 **Chướng ngại vật**: Vật cản, ổ gà, vũng nước

**Visual indicators:**
- Vòng tròn đỏ quanh người khi phát hiện
- Khoảng cách hiển thị thời gian thực
- Màu sắc thay đổi theo mức độ nguy hiểm

#### 8. ⚠️ Lệch làn (Lane Departure)

```python
# Custom logic: Phát hiện làn đường
lanes = detect_lanes(frame)
vehicle_position = get_vehicle_position()

if vehicle not in lane boundaries:
    add_ai_alert('lane', 'LỆCH LÀN!')
    play_sound('lech_lan.wav')
```

---

## 🛠️ 6. CÀI ĐẶT MÔI TRƯỜNG

### 6.1 Yêu cầu hệ thống

| Thành phần | Yêu cầu | Khuyến nghị |
|------------|---------|-------------|
| **OS** | macOS 10.15+, Windows 10+, Linux | macOS M1/M2, Ubuntu 20.04+ |
| **CPU** | Intel i5 / Apple M1 | Apple M1/M2 (tối ưu) |
| **RAM** | 8GB | 16GB+ |
| **Storage** | 10GB free | SSD 50GB+ |
| **Python** | 3.8 - 3.10 | 3.10 |
| **Camera** | Webcam 720p | 1080p 30FPS |

### 6.2 Cài đặt dependencies

#### **Bước 1: Clone repository**

```bash
cd /Users/vinhdv/Documents/Clone/AI-Traffic-Monitoring-System
```

#### **Bước 2: Tạo virtual environment**

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### **Bước 3: Cài đặt packages**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### **Bước 4: Cài đặt thêm flask-cors**

```bash
pip install flask-cors
```

### 6.3 Kiểm tra files cần thiết

```bash
# ✅ Backend files
ls -la py/Web/drive.py
ls -la py/Web/all_tong.py
ls -la py/Web/templates/traffic_bus.html

# ✅ Model files (phải có)
ls -la py/weights/yolov8n.pt
ls -la py/weights/lasttx.pt
ls -la py/shape_predictor_68_face_landmarks.dat

# ✅ Sound files
ls -la py/Sound/*.wav
```

### 6.4 Download models (nếu chưa có)

```bash
# YOLOv8n
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O py/weights/yolov8n.pt

# Dlib 68 landmarks
wget https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.gz -O py/shape_predictor_68_face_landmarks.dat.gz
gunzip py/shape_predictor_68_face_landmarks.dat.gz
```

---

## 🚀 7. CHẠY ỨNG DỤNG

### 7.1 Chạy trực tiếp (Native - Khuyến nghị cho development)

#### **Option 1: Với drive.py** (Camera webcam)

```bash
cd /Users/vinhdv/Documents/Clone/AI-Traffic-Monitoring-System/py/Web
python drive.py
```

#### **Option 2: Với all_tong.py** (Nhiều tính năng hơn)

```bash
cd /Users/vinhdv/Documents/Clone/AI-Traffic-Monitoring-System/py/Web
python all_tong.py
```

#### **Truy cập ứng dụng:**

```
http://localhost:5001/traffic_bus
```

### 7.2 Chạy với Docker (Khuyến nghị cho production)

```bash
# Build image
docker compose build

# Chạy container
docker compose up

# Chạy background
docker compose up -d

# Xem logs
docker compose logs -f ai-traffic-monitor

# Dừng container
docker compose down
```

### 7.3 Kiểm tra hoạt động

```bash
# Test API
curl http://localhost:5001/api/get_ai_warnings

# Test frontend
open http://localhost:5001/traffic_bus
```

### 7.4 Kết quả mong đợi

#### **Trong Terminal:**

```
[AI ALERT] eye: NHẮM MẮT QUÁ LÂU!
[AI ALERT] phone: DÙNG ĐIỆN THOẠI!
[AI ALERT] seatbelt: KHÔNG ĐEO DÂY AN TOÀN!
 * Running on http://0.0.0.0:5001
```

#### **Trong Chatbot:**

```
🔔 📱 Tài xế đang DÙNG ĐIỆN THOẠI!
⏰ 14:30:25 - 03/12/2024

🔔 😴 Tài xế đang NGÁP NGỦ!
⏰ 14:30:35 - 03/12/2024

🔔 🚨 CẢNH BÁO VA CHẠM SẮP XẢY RA!
⏰ 14:30:45 - 03/12/2024
```

---

## 📡 8. API DOCUMENTATION

### 8.1 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/get_ai_warnings` | Lấy cảnh báo AI hiện tại |
| GET | `/api/get_ai_alerts_history` | Lấy lịch sử cảnh báo |
| GET | `/video_feed` | Stream video từ camera |
| POST | `/api/save_alert_to_db` | Lưu cảnh báo vào DB |
| GET | `/api/get_daily_stats` | Thống kê vi phạm trong ngày |
| POST | `/api/update_vehicle_data` | Cập nhật dữ liệu xe |

### 8.2 Chi tiết API

#### **GET /api/get_ai_warnings**

Lấy trạng thái cảnh báo hiện tại (polling mỗi 3 giây).

**Request:**
```bash
curl http://localhost:5001/api/get_ai_warnings
```

**Response:**
```json
{
  "eye": "NHẮM MẮT QUÁ LÂU!",
  "yawn": "NGÁP NGỦ!",
  "head": "MẤT TẬP TRUNG !",
  "phone": "DÙNG ĐIỆN THOẠI!",
  "seatbelt": "KHÔNG ĐEO DÂY AN TOÀN!",
  "hand": "CẢNH BÁO: KHÔNG CẦM VÔ LĂNG!",
  "collision": "",
  "lane": ""
}
```

#### **GET /api/get_ai_alerts_history**

Lấy lịch sử cảnh báo (tối đa 50 cảnh báo).

**Request:**
```bash
curl http://localhost:5001/api/get_ai_alerts_history
```

**Response:**
```json
{
  "status": "success",
  "alerts": [
    {
      "type": "phone",
      "message": "Tài xế đang dùng điện thoại!",
      "timestamp": "14:30:25",
      "level": "critical"
    },
    {
      "type": "eye",
      "message": "Tài xế nhắm mắt quá lâu!",
      "timestamp": "14:30:15",
      "level": "critical"
    }
  ]
}
```

#### **GET /video_feed**

Stream video từ camera (MJPEG format).

**Request:**
```bash
# VLC
vlc http://localhost:5001/video_feed

# Browser
<img src="http://localhost:5001/video_feed" />
```

### 8.3 Test API với Python

```python
import requests
import time

# Polling cảnh báo
while True:
    response = requests.get('http://localhost:5001/api/get_ai_warnings')
    data = response.json()
    
    for key, value in data.items():
        if value:
            print(f"⚠️ {key}: {value}")
    
    time.sleep(3)
```

---

## 💬 9. AI CHATBOT

### 9.1 Tính năng chatbot

| Tính năng | Mô tả |
|-----------|-------|
| **Auto Alerts** | Tự động nhận cảnh báo từ AI |
| **Smart Chat** | Trả lời tin nhắn với AI (rule-based / LLM) |
| **Vehicle Info** | Hỏi thông tin 7 xe đang giám sát |
| **Voice Control** | 10+ lệnh giọng nói tiếng Việt |

### 9.2 Dữ liệu xe trong hệ thống

AI đã được cung cấp thông tin **7 xe đang giám sát**:

| Biển số | Tài xế | Vị trí | Trạng thái | Tốc độ |
|---------|--------|--------|------------|--------|
| 29A-111.11 | Nguyễn Văn Đức | Võ Chí Công | Đang chạy | 45 km/h |
| 29B-222.22 | Trần Văn Hoan | Bến xe Mỹ Đình | Đang dừng | 0 km/h |
| 30E-333.33 | Lê Thị Đào | Minh Khai | Đang chạy | 30 km/h |
| 29H-444.44 | Phạm Văn Dũng | Ngã tư Sở | Đang chạy | 50 km/h |
| 15B-555.55 | Hoàng Văn Việt | Cao tốc 5B | Đang chạy | 40 km/h |
| 30G-666.66 | Vũ Thị Hồng | Phủ Tây Hồ | Đang chạy | 40 km/h |
| 29LD-777.77 | Công ty Travel | Cầu Chương Dương | Đang chạy | 60 km/h |

### 9.3 Test AI Chatbot

#### **Hỏi vị trí xe:**
```
👤 Bạn: Xe 29A-111.11 đang ở đâu?
🤖 AI: 🚗 Xe 29A-111.11 do tài xế Nguyễn Văn Đức lái,
       đang ở vị trí Võ Chí Công, tốc độ 45 km/h.
```

#### **Hỏi tài xế:**
```
👤 Bạn: Ai lái xe 30E-333.33?
🤖 AI: 👨‍✈️ Xe 30E-333.33 do tài xế Lê Thị Đào lái,
       đang ở Minh Khai, tốc độ 30 km/h.
```

#### **Hỏi vi phạm:**
```
👤 Bạn: Vi phạm hôm nay thế nào?
🤖 AI: 📊 Thống kê vi phạm hôm nay:
       - 📱 Dùng điện thoại: 3 lần
       - 😴 Ngáp ngủ: 5 lần
       - ⚠️ Không dây an toàn: 2 lần
```

### 9.4 Lệnh giọng nói

| Lệnh | Tác vụ |
|------|--------|
| "Hiển thị xe 29B-222.22" | Focus vào xe trên bản đồ |
| "Tìm xe gần nhất" | Tìm xe gần vị trí hiện tại |
| "Mở camera tài xế" | Xem camera từ xe |
| "Gọi hỗ trợ" | Mở chatbot |
| "Xem cảnh báo" | Mở AI Alerts Panel |

### 9.5 Setup AI API (Optional - Nâng cao)

Để dùng ChatGPT/Gemini thay vì rule-based:

```bash
# Cài đặt
pip install groq

# Setup API key
export GROQ_API_KEY="gsk_xxxxxxxxxxxxxx"

# Chạy ứng dụng
python drive.py
```

Xem chi tiết trong [SETUP_AI_API.md](SETUP_AI_API.md)

---

## 🐳 10. DOCKER DEPLOYMENT

### 10.1 Cấu hình Docker

**File: `docker-compose.yml`**

```yaml
version: "3.8"

services:
  ai-traffic-monitor:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ai-traffic-monitor
    ports:
      - "5000:5000"
    environment:
      - FLASK_APP=py/Web/all_tong.py
      - FLASK_ENV=development
      - PYTHONUNBUFFERED=1
    volumes:
      - ./py/weights:/app/py/weights
      - ./recordings:/app/recordings
      - ./py/Sound:/app/py/Sound
      - ./py/video_input:/app/py/video_input
    restart: unless-stopped
```

### 10.2 Lệnh Docker hữu ích

```bash
# Build image
docker compose build

# Chạy container
docker compose up

# Chạy background
docker compose up -d

# Xem logs
docker compose logs -f ai-traffic-monitor

# Dừng container
docker compose down

# Xóa image
docker compose down --rmi all

# Truy cập shell
docker compose exec ai-traffic-monitor bash

# Chạy với script khác
# Sửa docker-compose.yml: FLASK_APP=py/Web/drive.py
docker compose up --build
```

### 10.3 Lưu ý khi dùng Docker

| Vấn đề | Giải pháp |
|--------|-----------|
| **Webcam không hoạt động** | Chạy native hoặc dùng video file |
| **Audio không nghe được** | Chạy native để có âm thanh đầy đủ |
| **Performance chậm** | Dùng native hoặc Linux server |
| **Dung lượng image lớn** | Xóa image khi không dùng: `docker compose down --rmi all` |

---

## 🔧 11. TROUBLESHOOTING

### 11.1 Lỗi thường gặp

#### **❌ Lỗi: "ModuleNotFoundError: No module named 'flask'"**

```bash
# Fix
pip install -r requirements.txt
```

#### **❌ Lỗi: "CORS policy blocked"**

```bash
# Fix
pip install flask-cors
# Restart backend
```

#### **❌ Lỗi: "Không thấy cảnh báo trong chat"**

```bash
# Kiểm tra backend
curl localhost:5001/api/get_ai_warnings

# Kiểm tra Console log (F12)
# Kiểm tra camera có hoạt động không
```

#### **❌ Lỗi: "Video file not found"**

```bash
# Kiểm tra đường dẫn video trong code
# Hoặc dùng webcam thay vì video file
```

#### **❌ Lỗi: "shape_predictor_68_face_landmarks.dat not found"**

```bash
# Download model
wget https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.gz
gunzip shape_predictor_68_face_landmarks.dat.gz
```

#### **❌ Lỗi: "API key not found" (AI Chatbot)**

```bash
# Check key
echo $GROQ_API_KEY

# Set lại
export GROQ_API_KEY="gsk_xxxxx"
```

### 11.2 Debug checklist

```bash
# 1. Kiểm tra Python version
python --version  # Should be 3.8-3.10

# 2. Kiểm tra packages đã cài
pip list | grep flask
pip list | grep opencv
pip list | grep dlib

# 3. Kiểm tra files cần thiết
ls -la py/weights/*.pt
ls -la py/Sound/*.wav
ls -la py/Web/templates/traffic_bus.html

# 4. Test API
curl http://localhost:5001/api/get_ai_warnings

# 5. Kiểm tra port đang dùng
lsof -i :5001

# 6. Xem logs
docker compose logs ai-traffic-monitor
```

### 11.3 Xử lý sự cố theo triệu chứng

| Triệu chứng | Nguyên nhân | Giải pháp |
|-------------|-------------|-----------|
| Chatbot không hiện cảnh báo | Backend không chạy | `python drive.py` |
| Spam cảnh báo liên tục | `ALERT_RESEND_INTERVAL` quá thấp | Sửa thành 10000 (10s) |
| Camera không hiển thị | Path video sai | Kiểm tra đường dẫn |
| AI không nhận diện | Model không tải được | Download lại `.pt` files |
| Chatbot không trả lời | AI API key sai | Kiểm tra `GROQ_API_KEY` |

---

## 📁 12. CẤU TRÚC DỰ ÁN

```
AI-Traffic-Monitoring-System/
│
├── 📄 README.md                      # Tài liệu chính (file này)
├── 📄 DOCKER_README.md               # Hướng dẫn Docker
├── 📄 SETUP_AI_API.md                # Setup AI API key
├── 📄 AI_CHATBOT_GUIDE.md            # Hướng dẫn AI Chatbot
├── 📄 AI_DA_CO_DATA.md               # Data xe trong hệ thống
├── 📄 requirements.txt               # Python dependencies
├── 📄 Dockerfile                     # Docker image config
├── 📄 docker-compose.yml             # Docker compose config
├── 📄 .dockerignore                  # Files loại trừ khi build Docker
├── 📄 .gitignore                     # Files loại trừ khi git
│
├── 📂 py/                            # Source code chính
│   ├── 📂 Web/
│   │   ├── drive.py                  # Backend AI (Camera webcam)
│   │   ├── all_tong.py               # Backend AI (Full tính năng)
│   │   ├── bien_so.py                # Nhận diện biển số
│   │   ├── hands.py                  # Detection tay
│   │   ├── HandTrackingModule.py     # MediaPipe hand tracking
│   │   ├── tay_chuan.py              # Chuẩn tay
│   │   │
│   │   ├── 📂 templates/
│   │   │   └── traffic_bus.html      # Frontend + Chatbot + Map
│   │   │
│   │   ├── 📂 api/                   # API routes
│   │   ├── 📂 services/              # Business logic
│   │   ├── 📂 static/                # CSS, JS, images
│   │   └── 📂 __pycache__/
│   │
│   ├── 📂 weights/                   # AI Models
│   │   ├── yolov8n.pt               # YOLOv8 nano
│   │   ├── lasttx.pt                # Custom model
│   │   └── best.torchscript         # TorchScript model
│   │
│   ├── 📂 Sound/                     # Âm thanh cảnh báo
│   │   ├── nham_mat.wav             # Nhắm mắt
│   │   ├── buon_ngu.wav             # Buồn ngủ
│   │   ├── not_phone.wav            # Điện thoại
│   │   ├── seatbelt_alert.wav       # Dây an toàn
│   │   ├── chuylaixe.wav            # Mất tập trung
│   │   ├── tay_lai_xe.wav           # Tay vô lăng
│   │   ├── lech_lan.wav             # Lệch làn
│   │   └── va_cham.wav              # Va chạm
│   │
│   ├── 📂 video_input/               # Video test
│   ├── 📂 pictures/                  # Ảnh test
│   ├── 📂 runs/                      # Output runs
│   └── shape_predictor_68_face_landmarks.dat  # Dlib model
│
├── 📂 recordings/                    # Video ghi hình vi phạm
├── 📂 .venv/                         # Virtual environment
├── 📂 venv/                          # Virtual environment (backup)
├── 📂 .vscode/                       # VSCode settings
└── 📂 .git/                          # Git repository
```

---

## 📊 HIỆU NĂNG HỆ THỐNG

| Thành phần | Thời gian xử lý |
|------------|-----------------|
| AI Detection (1 frame) | ~30-50ms |
| add_ai_alert() | <1ms |
| API GET | ~10ms |
| Frontend render | ~5ms |
| **Tổng độ trễ** | **~50-70ms** |

→ **Real-time**: Cảnh báo xuất hiện trong chat < 1 giây

---

## 🔐 CHỨC NĂNG ADMIN (DASHBOARD.HTML)

### 1. 👁️ Giám sát thời gian thực

#### **Bản đồ Leaflet:**
- Hiển thị vị trí **7 xe** đang chạy
- Marker phân loại theo loại xe (car/bus/truck)
- Popup thông tin khi click vào marker
- Auto-refresh vị trí mỗi 2 giây

#### **Camera Grid:**
- 4 camera góc nhìn (tài xế, trước, khách, lùi)
- Video stream thời gian thực
- Click để mở full-screen
- Status indicator (Online/Offline)

#### **KPI Cards:**
```
┌──────────────────────────────────────────────────────────────┐
│  📊 KPI CARDS                                               │
│                                                              │
│  🚗 Xe hoạt động      📦 Chuyến hôm nay    ⚠️ Cảnh báo AI   │
│     48                    124                  5            │
│                                                              │
│  🚫 Vi phạm           🛡️ Điểm an toàn                       │
│     4                    86/100                              │
└──────────────────────────────────────────────────────────────┘
```

### 2. ⚠️ Nhận cảnh báo AI từ lái_xe

#### **AI Alerts Panel:**
- Panel bên phải màn hình
- Hiển thị cảnh báo thời gian thực
- Phân loại theo mức độ (Critical/Warning/Info)
- Timestamp chính xác

```javascript
// Polling API mỗi 3 giây
function fetchAICurrentWarnings() {
    fetch('http://localhost:5002/api/get_ai_warnings')
        .then(res => res.json())
        .then(data => {
            updateAlertsPanel(data);
        });
}

setInterval(fetchAICurrentWarnings, 3000);
```

#### **Các loại cảnh báo:**
| Loại | Mức độ | Icon |
|------|--------|------|
| Nhắm mắt quá lâu | 🔴 Critical | 👁️ |
| Ngáp ngủ | 🟡 Warning | 😴 |
| Mất tập trung | 🟡 Warning | 🔄 |
| Dùng điện thoại | 🔴 Critical | 📱 |
| Không dây an toàn | 🔴 Critical | ⚠️ |
| Không cầm vô lăng | 🟡 Warning | 🙌 |
| Va chạm | 🔴 Critical | 🚨 |
| Lệch làn | 🟡 Warning | ⚠️ |

### 3. 📢 Gửi cảnh cáo đến tài xế

#### **Chức năng gửi cảnh cáo:**
```javascript
// Dashboard.html
function sendWarning(vehiclePlate) {
    const message = prompt('Nhập nội dung cảnh cáo:');
    
    if (message) {
        fetch('/api/send_warning', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                vehicle_plate: vehiclePlate,
                message: message,
                admin_id: 'admin001',
                timestamp: new Date().toISOString()
            })
        })
        .then(res => res.json())
        .then(data => {
            showToast('success', 'Đã gửi cảnh cáo!');
        });
    }
}
```

#### **Action Buttons trong table:**
```html
<div class="action-buttons">
    <button class="btn-action btn-call" onclick="callDriver('0909888999')">
        <i class="fa-solid fa-phone"></i> Gọi
    </button>
    <button class="btn-action btn-alert" onclick="sendWarning('29B-222.22')">
        <i class="fa-solid fa-bell"></i> Cảnh báo
    </button>
    <button class="btn-action btn-camera" onclick="viewCamera('29B-222.22')">
        <i class="fa-solid fa-video"></i> Camera
    </button>
    <button class="btn-action btn-report" onclick="viewReport('29B-222.22')">
        <i class="fa-solid fa-file-lines"></i> Báo cáo
    </button>
</div>
```

### 4. 🔍 Tìm kiếm và Lọc dữ liệu

#### **Tìm kiếm xe:**
```javascript
// Tìm theo biển số
function searchVehicle() {
    const plateInput = document.getElementById('searchPlate').value.trim().toUpperCase();
    const driverInput = document.getElementById('searchDriver').value.trim().toLowerCase();
    
    // Tìm trong danh sách
    for (const vehicle of vehicles) {
        if (vehicle.plate.includes(plateInput) || 
            vehicle.driver.toLowerCase().includes(driverInput)) {
            focusVehicle(vehicle.id);
            showToast('success', `Đã tìm thấy xe ${vehicle.plate}`);
            return;
        }
    }
    
    showToast('warning', 'Không tìm thấy xe');
}

// Focus xe trên bản đồ
function focusVehicle(id) {
    const vehicle = vehicles.find(v => v.id === id);
    map.flyTo([vehicle.lat, vehicle.lng], 16);
    markers[id].openPopup();
}
```

#### **Bộ lọc:**
```html
<!-- Lọc theo trạng thái -->
<select id="statusFilter">
    <option value="all">Tất cả trạng thái</option>
    <option value="running">Đang chạy</option>
    <option value="stopped">Đã dừng</option>
    <option value="offline">Offline</option>
</select>

<!-- Lọc theo vi phạm -->
<select id="violationFilter">
    <option value="all">Tất cả vi phạm</option>
    <option value="phone">Dùng điện thoại</option>
    <option value="seatbelt">Không thắt dây</option>
    <option value="drowsy">Buồn ngủ</option>
    <option value="lane">Lệch làn</option>
</select>
```

### 5. 📈 Thống kê và Báo cáo

#### **Thống kê tổng quan:**
```javascript
// Statistics page
const stats = {
    totalTrips: 1247,
    totalPassengers: 8562,
    totalViolations: 89,
    revenue: '2.4B VNĐ',
    activeVehicles: 42,
    activeDrivers: 38
};
```

#### **Biểu đồ:**
- **Trips Chart**: Lượt chuyến theo ngày/tuần/tháng
- **Violation Pie Chart**: Tỷ lệ vi phạm theo loại
- **Violation Bar Chart**: Số vụ vi phạm theo loại
- **Violation Trend Chart**: Xu hướng vi phạm theo thời gian
- **Hourly Trips Chart**: Lượt chuyến theo giờ

#### **Báo cáo:**
```javascript
// Xuất báo cáo Excel
function exportExcel() {
    const table = document.getElementById('tripTableBody');
    exportTableToExcel(table.id, 'bao_cao_vi_pham');
    showToast('success', 'Đã xuất báo cáo Excel!');
}

// Xuất báo cáo PDF
function exportReport() {
    showToast('info', 'Xuất PDF', 'Đang chuẩn bị báo cáo PDF...');
}
```

### 6. ➕ CRUD Dữ liệu

#### **Thêm xe mới:**
```javascript
function openAddVehicleModal() {
    const modal = createModal('addVehicleModal', '🚗 Thêm xe mới', `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
            <div>
                <label>Biển số</label>
                <input type="text" id="newVehiclePlate">
            </div>
            <div>
                <label>Loại xe</label>
                <select id="newVehicleType">
                    <option value="car">Xe con</option>
                    <option value="bus">Xe khách</option>
                    <option value="truck">Xe tải</option>
                </select>
            </div>
            <div>
                <label>Tài xế</label>
                <input type="text" id="newVehicleDriver">
            </div>
            <div>
                <label>Số ghế</label>
                <input type="number" id="newVehicleSeats">
            </div>
        </div>
    `, `
        <button onclick="saveNewVehicle()">Thêm xe</button>
    `);
}

function saveNewVehicle() {
    const plate = document.getElementById('newVehiclePlate').value;
    // Lưu vào database
    showToast('success', `Đã thêm xe ${plate}`);
}
```

#### **Sửa thông tin xe:**
```javascript
function editVehicle(plate) {
    showToast('info', 'Chỉnh sửa', `Đang chỉnh sửa xe ${plate}`);
    // Mở modal với thông tin hiện tại
}
```

#### **Xóa xe:**
```javascript
function deleteVehicle(plate) {
    if (confirm(`Bạn có chắc muốn xóa xe ${plate}?`)) {
        // Xóa từ database
        showToast('success', `Đã xóa xe ${plate}`);
        loadVehiclesData();  // Reload danh sách
    }
}
```

#### **Quản lý tài xế:**
- **loadDriversData()**: Tải danh sách tài xế
- **showAddDriverModal()**: Thêm tài xế mới
- **editDriver(name)**: Sửa thông tin
- **deleteDriver(name)**: Xóa tài xế
- **callDriver(phone)**: Gọi điện

#### **Quản lý tuyến đường:**
- **loadRoutesData()**: Tải danh sách tuyến
- **openAddModal()**: Thêm tuyến mới
- **viewRoute(code)**: Xem chi tiết tuyến trên bản đồ
- **editRoute(code)**: Sửa tuyến
- **exportRoutes()**: Xuất danh sách tuyến

### 7. 📤 Xuất file

```javascript
// Xuất Excel
function exportTableToExcel(tableId, filename) {
    const table = document.getElementById(tableId);
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(col => {
            rowData.push('"' + col.innerText.replace(/"/g, '""') + '"');
        });
        csv.push(rowData.join(','));
    });
    
    downloadCSV(csv.join('\n'), filename + '.csv');
    showToast('success', `Đã xuất ${filename}.csv`);
}

// Download file
function downloadCSV(csv, filename) {
    const csvFile = new Blob([csv], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.click();
}
```

### 8. 🎤 Voice Commands

#### **Lệnh giọng nói:**
```javascript
// Speech Recognition
var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
recognition = new SpeechRecognition();
recognition.lang = 'vi-VN';

recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript.toLowerCase();
    processVoiceCommand(transcript);
};

function processVoiceCommand(cmd) {
    if (cmd.includes('hiển thị xe')) {
        // Tìm và focus xe
        const plate = extractPlate(cmd);
        focusVehicleByPlate(plate);
    }
    else if (cmd.includes('mở camera')) {
        viewCamera();
    }
    else if (cmd.includes('gọi hỗ trợ')) {
        toggleChat(true);
    }
    else if (cmd.includes('xem cảnh báo')) {
        toggleAlertsPanel(true);
    }
}
```

---

## 📱 CHỨC NĂNG USER (TRANG_CHU.HTML)

### 1. 💬 Tư vấn cá nhân

```javascript
// Chat với AI về thông tin cá nhân
function sendUserMsg() {
    const text = document.getElementById('chatInput').value;
    
    fetch('/api/send_chat_message', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            message: text,
            user_id: currentUserId
        })
    })
    .then(res => res.json())
    .then(data => {
        displayUserMessage(text);
        displayBotMessage(data.bot_response);
    });
}
```

### 2. ⚠️ Nhận cảnh báo từ lái_xe

```javascript
// Polling cảnh báo AI
function checkMyAlerts() {
    fetch('/api/get_my_alerts')
        .then(res => res.json())
        .then(data => {
            displayAlerts(data.alerts);
        });
}

setInterval(checkMyAlerts, 3000);
```

### 3. 📨 Nhận xử phạt từ Admin

```javascript
// Nhận cảnh cáo từ Admin
function checkWarnings() {
    fetch('/api/get_my_warnings')
        .then(res => res.json())
        .then(data => {
            data.warnings.forEach(warning => {
                addWarningToTimeline(warning);
            });
        });
}

setInterval(checkWarnings, 5000);
```

### 4. 📊 Xem lịch sử vi phạm

```javascript
// Lịch sử vi phạm cá nhân
function loadMyHistory() {
    fetch('/api/get_my_history')
        .then(res => res.json())
        .then(data => {
            displayHistory(data.violations);
        });
}
```

### 5. 🎤 Chat voice

```javascript
// Chat bằng giọng nói
function toggleVoiceRecognition() {
    if (isVoiceListening) {
        recognition.stop();
    } else {
        recognition.start();
    }
}
```

---

## 🔄 TÓM TẮT LUỒNG HOẠT ĐỘNG

### Luồng 1: AI Detection → Admin Dashboard

```
lái_xe.py (AI) → Server API → Dashboard.html (Admin)
     ↓              ↓              ↓
  Phát hiện    Lưu trữ và    Hiển thị cảnh
  vi phạm      forward       báo trong panel
```

### Luồng 2: Admin → User (Cảnh cáo/Xử phạt)

```
Dashboard.html → Server API → trang_chu.html (User)
     ↓              ↓              ↓
  Admin gửi    Lưu và        Tài xế nhận
  cảnh cáo     forward       cảnh cáo
```

### Luồng 3: User cải thiện → Admin xem thống kê

```
trang_chu.html → Server API → Dashboard.html
     ↓              ↓              ↓
  Tài xế cải   Cập nhật      Admin xem
  thiện        điểm số       thống kê
```

---

## ✅ CHECKLIST KIỂM TRA

### Setup
- [ ] Python 3.8-3.10 đã cài
- [ ] Virtual environment đã tạo
- [ ] Dependencies đã cài (`pip install -r requirements.txt`)
- [ ] Models đã download (`.pt` files)
- [ ] Sound files đã có (`py/Sound/*.wav`)

### Chạy ứng dụng
- [ ] Backend Flask chạy port 5001
- [ ] Frontend truy cập được tại `/traffic_bus`
- [ ] Camera mở và hiển thị video
- [ ] Đưa điện thoại vào → Có cảnh báo trong chat
- [ ] Chatbot hiển thị thời gian đầy đủ
- [ ] Anti-spam hoạt động (10 giây/gửi lại)
- [ ] Click nút "🔔" → Thấy AI Alerts Panel
- [ ] Click nút "🎤" → Nói lệnh → Hoạt động

### API Test
- [ ] `curl localhost:5001/api/get_ai_warnings` → JSON response
- [ ] `curl localhost:5001/api/get_ai_alerts_history` → Lịch sử cảnh báo
- [ ] Video stream hoạt động tại `/video_feed`

### AI Chatbot Test
- [ ] Nhắn "Xin chào" → Bot chào lại
- [ ] Nhắn "Xe 29A-111.11 ở đâu" → Trả lời đúng vị trí
- [ ] Đưa điện thoại vào camera → Bot tự động cảnh báo

---

## 🎓 TÍNH NĂNG NÂNG CAO

### 1. Lưu cảnh báo vào Database

```python
@app.route('/api/save_alert_to_db', methods=['POST'])
def save_alert_to_db():
    data = request.get_json()
    # Lưu vào SQLite/MySQL
    conn = sqlite3.connect('traffic.db')
    cursor = conn.execute(
        "INSERT INTO alerts (type, message, timestamp, level) VALUES (?, ?, ?, ?)",
        (data['type'], data['message'], data['timestamp'], data['level'])
    )
    conn.commit()
    return jsonify({'status': 'success'})
```

### 2. Gửi email/SMS khi nguy hiểm

```python
if alert_type in ['collision', 'eye']:
    send_email_to_admin(alert)
    send_sms_to_driver(alert)
```

### 3. Thống kê theo ngày

```python
@app.route('/api/get_daily_stats')
def get_daily_stats():
    # COUNT alerts by type for today
    stats = {
        'phone': count_alerts_today('phone'),
        'eye': count_alerts_today('eye'),
        'seatbelt': count_alerts_today('seatbelt'),
    }
    return jsonify(stats)
```

### 4. WebSocket (real-time không cần poll)

```python
from flask_socketio import SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Emit alert
socketio.emit('new_alert', alert)

# Frontend
socket.on('new_alert', (data) => {
    displayAlert(data);
});
```

---

## 📞 HỖ TRỢ

### Tài liệu liên quan

| Tài liệu | Mô tả |
|----------|-------|
| [DOCKER_README.md](DOCKER_README.md) | Hướng dẫn chạy Docker chi tiết |
| [SETUP_AI_API.md](SETUP_AI_API.md) | Setup API key cho AI Chatbot |
| [AI_CHATBOT_GUIDE.md](AI_CHATBOT_GUIDE.md) | Hướng dẫn sử dụng AI Chatbot |
| [AI_DA_CO_DATA.md](AI_DA_CO_DATA.md) | Dữ liệu xe trong hệ thống |

### Debug tools

```bash
# Xem logs chi tiết
docker compose logs -f ai-traffic-monitor

# Kiểm tra API
curl -v http://localhost:5001/api/get_ai_warnings

# Test video stream
vlc http://localhost:5001/video_feed

# Check port
lsof -i :5001
```

### Thông tin liên hệ

- **GitHub:** [AI-Traffic-Monitoring-System](https://github.com/aitraffic)
- **Email:** support@aitraffic.com
- **Documentation:** [README.md](README.md)

---

## 📄 LICENSE

Dự án mã nguồn mở, tự do sử dụng và phát triển theo giấy phép MIT.

---

## 🙏 CẢM ƠN

Cảm ơn bạn đã sử dụng **AI Traffic Monitoring System**!

> **Phát triển bởi:** AI Traffic Monitoring Team  
> **Version:** 2.0  
> **Cập nhật:** 2024  
> **Ngôn ngữ:** Python 3.10, Flask, OpenCV, YOLOv8, Dlib, MediaPipe

---

**Chúc bạn thành công! 🎉**

```bash
# Quick start
cd /Users/vinhdv/Documents/Clone/AI-Traffic-Monitoring-System
source venv/bin/activate
cd py/Web && python drive.py

# Open browser
open http://localhost:5001/traffic_bus
```
