# 🚀 HỆ THỐNG GIÁM SÁT TÀI XẾ - AI CHATBOT

> **Phiên bản:** 1.0 | **Cập nhật:** 2024

## 📋 Mô tả

Hệ thống giám sát tài xế bằng AI và gửi cảnh báo vào chatbot để thông báo cho admin theo thời gian thực.

### ⚠️ 8 Loại cảnh báo:

| # | Cảnh báo | Mức độ | Mô tả |
|---|----------|--------|-------|
| 1 | 👁️ **Nhắm mắt quá lâu** | 🔴 Critical | Tài xế buồn ngủ, mệt mỏi |
| 2 | 😴 **Ngáp ngủ** | 🟡 Warning | Dấu hiệu mệt mỏi |
| 3 | 🔄 **Mất tập trung** | 🟡 Warning | Quay đầu/ngửa đầu quá mức |
| 4 | 📱 **Dùng điện thoại** | 🔴 Critical | Sử dụng ĐT khi lái xe |
| 5 | ⚠️ **Không dây an toàn** | 🔴 Critical | Vi phạm an toàn |
| 6 | 🙌 **Không cầm vô lăng** | 🟡 Warning | Tay không đúng vị trí |
| 7 | 🚨 **Va chạm** | 🔴 Critical | Phát hiện va chạm sắp xảy ra |
| 8 | ⚠️ **Lệch làn** | 🟡 Warning | Xe đi chệch làn đường |

---

## 🎯 Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMERA GIÁM SÁT                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              BACKEND (drive.py / all_tong.py)                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  AI Detection: Dlib, YOLO, MediaPipe                  │   │
│  │  → Phát hiện vi phạm → add_ai_alert()                 │   │
│  │  → Lưu vào ai_alerts_queue                            │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │ API: /api/get_ai_warnings
                     │ (Polling mỗi 3 giây)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           FRONTEND (traffic_bus.html)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Chatbot Widget:                                      │   │
│  │  - Hiển thị cảnh báo với thời gian                    │   │
│  │  - Anti-spam: gửi lại sau 10 giây                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Cài đặt

### Bước 1: Cài dependencies
```bash
cd /Users/vinhdv/Documents/Clone/AI-Traffic-Monitoring-System
pip install -r requirements.txt
pip install flask-cors
```

### Bước 2: Kiểm tra files
```bash
# Backend
ls py/Web/drive.py
ls py/Web/all_tong.py
ls py/Web/templates/traffic_bus.html

# Models (phải có)
ls py/weights/yolov8n.pt
ls py/weights/lasttx.pt
ls py/shape_predictor_68_face_landmarks.dat
```

---

## 🚀 Chạy chương trình

### **Cách 1: Với drive.py** (Camera webcam)
```bash
cd /Users/vinhdv/Documents/Clone/AI-Traffic-Monitoring-System/py/Web
python drive.py
```

### **Cách 2: Với all_tong.py** (Nhiều tính năng hơn)
```bash
cd /Users/vinhdv/Documents/Clone/AI-Traffic-Monitoring-System/py/Web
python all_tong.py
```

### Truy cập:
```
http://localhost:5001/traffic_bus
```

---

## 📊 Kết quả mong đợi

### Trong Chatbot:
```
🔔 📱 Tài xế đang DÙNG ĐIỆN THOẠI!
⏰ 14:30:25 - 03/12/2024

🔔 😴 Tài xế đang NGÁP NGỦ!
⏰ 14:30:35 - 03/12/2024

🔔 🚨 CẢNH BÁO VA CHẠM SẮP XẢY RA!
⏰ 14:30:45 - 03/12/2024
```

### Anti-spam:
- Mỗi cảnh báo chỉ gửi **1 lần duy nhất**
- Nếu vi phạm **tiếp diễn** → Gửi lại sau **10 giây**
- Có thể tùy chỉnh thời gian resend

---

## 🔧 Tùy chỉnh

### Thay đổi thời gian resend (trong `traffic_bus.html`):
```javascript
var ALERT_RESEND_INTERVAL = 10000;  // 10000ms = 10 giây
```

**Các lựa chọn:**
- `5000` = 5 giây (gửi thường xuyên)
- `10000` = 10 giây (mặc định)
- `30000` = 30 giây (ít spam)
- `60000` = 60 giây (rất ít)

### Thay đổi thời gian poll:
```javascript
function startAlertsPolling() {
    fetchAICurrentWarnings();
    alertsPollingInterval = setInterval(() => {
        fetchAICurrentWarnings();
    }, 3000);  // Thay đổi số này (ms)
}
```

---

## 🧪 Test API

### Kiểm tra cảnh báo hiện tại:
```bash
curl http://localhost:5001/api/get_ai_warnings
```

**Kết quả:**
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

### Kiểm tra lịch sử cảnh báo:
```bash
curl http://localhost:5001/api/get_ai_alerts_history
```

**Kết quả:**
```json
{
  "status": "success",
  "alerts": [
    {
      "type": "phone",
      "message": "Tài xế đang dùng điện thoại!",
      "timestamp": "14:30:25",
      "level": "critical"
    }
  ]
}
```

---

## 🎤 Điều khiển bằng giọng nói

### Các lệnh hỗ trợ:

| Lệnh | Tác vụ |
|------|--------|
| "Hiển thị xe 29B-222.22" | Focus vào xe |
| "Tìm xe gần nhất" | Tìm xe gần |
| "Mở camera tài xế" | Xem camera |
| "Gọi hỗ trợ" | Mở chatbot |
| "Xem cảnh báo" | Mở AI Alerts Panel |

### Cách dùng:
1. Click nút **🎤 Microphone** (góc dưới phải)
2. Nói lệnh
3. Hệ thống tự động thực hiện

---

## 🐛 Xử lý sự cố

### Lỗi: "Không thấy cảnh báo trong chat"
**Kiểm tra:**
1. Backend có chạy không? `curl localhost:5001/api/get_ai_warnings`
2. Console log có lỗi không? (F12)
3. Camera có hoạt động không?

### Lỗi: "CORS policy blocked"
**Fix:**
```bash
pip install flask-cors
# Restart backend
```

### Lỗi: "Module not found"
```bash
pip install -r requirements.txt
```

### Lỗi: "Video file not found"
```bash
# Kiểm tra đường dẫn video trong code
# Hoặc dùng webcam thay vì video file
```

---

## 📈 Hiệu năng

| Thành phần | Thời gian |
|------------|-----------|
| AI Detection (1 frame) | ~30-50ms |
| add_ai_alert() | <1ms |
| API GET | ~10ms |
| Frontend render | ~5ms |
| **Tổng độ trễ** | **~50-70ms** |

→ **Real-time**: Cảnh báo xuất hiện trong chat < 1 giây

---

## 📁 Cấu trúc files

```
AI-Traffic-Monitoring-System/
├── py/
│   └── Web/
│       ├── drive.py              # Backend AI (Camera)
│       ├── all_tong.py           # Backend AI (Full)
│       └── templates/
│           └── traffic_bus.html  # Frontend + Chatbot
├── traffic_bus.html              # Frontend (standalone)
├── requirements.txt              # Python dependencies
└── README.md                     # File này
```

---

## 🎓 Tính năng nâng cao

### 1. Lưu cảnh báo vào Database
```python
@app.route('/api/save_alert_to_db', methods=['POST'])
def save_alert_to_db():
    data = request.get_json()
    # Lưu vào SQLite/MySQL
```

### 2. Gửi email/SMS khi nguy hiểm
```python
if alert_type in ['collision', 'eye']:
    send_email_to_admin(...)
    send_sms_to_driver(...)
```

### 3. Thống kê theo ngày
```python
@app.route('/api/get_daily_stats')
def get_daily_stats():
    # COUNT alerts by type for today
```

### 4. WebSocket (real-time không cần poll)
```python
from flask_socketio import SocketIO
socketio.emit('new_alert', alert)
```

---

## ✅ Checklist kiểm tra

- [ ] Backend Flask chạy port 5001
- [ ] Frontend truy cập được tại `/traffic_bus`
- [ ] Camera mở và hiển thị video
- [ ] Đưa điện thoại vào → Có cảnh báo trong chat
- [ ] Chatbot hiển thị thời gian đầy đủ
- [ ] Anti-spam hoạt động (10 giây/gửi lại)
- [ ] Click nút "🔔" → Thấy AI Alerts Panel
- [ ] Click nút "🎤" → Nói lệnh → Hoạt động

---

## 📞 Hỗ trợ

**Vấn đề thường gặp:**

1. **Không có cảnh báo:** Kiểm tra backend đang chạy
2. **Spam liên tục:** Kiểm tra `ALERT_RESEND_INTERVAL`
3. **Lỗi CORS:** Cài `flask-cors`
4. **Không nhận diện:** Kiểm tra camera/models

**Kiểm tra log:**
- Terminal backend: Xem `[AI ALERT]` messages
- Browser Console (F12): Xem lỗi JavaScript
- Network tab: Xem API requests status

---

## 📄 License

Dự án mã nguồn mở, tự do sử dụng và phát triển.

---

**Chúc bạn thành công! 🎉**

> **Tác giả:** AI Traffic Monitoring System  
> **Email:** support@aitraffic.com  
> **GitHub:** github.com/aitraffic
