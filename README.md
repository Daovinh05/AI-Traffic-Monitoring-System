# 🚗 HỆ THỐNG GIÁM SÁT GIAO THÔNG THÔNG MINH AI

Hệ thống giám sát giao thông thông minh sử dụng AI để phát hiện vi phạm của tài xế và cung cấp dashboard quản lý thời gian thực.

---

## 📋 MỤC LỤC

- [Tính năng chính](#-tính-năng-chính)
- [Kiến trúc hệ thống](#-kiến-trúc-hệ-thống)
- [Luồng hoạt động](#-luồng-hoạt-động)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Hướng dẫn cài đặt](#-hướng-dẫn-cài-đặt)
- [Cấu hình](#-cấu-hình)
- [Cách chạy](#-cách-chạy)
- [API Endpoints](#-api-endpoints)
- [Cấu trúc database](#-cấu-trúc-database)
- [Xử lý sự cố](#-xử-lý-sự-cố)

---

## 🎯 TÍNH NĂNG CHÍNH

### 1. **Giám sát tài xế bằng AI** 🤖
- ✅ Phát hiện không đeo dây an toàn (`seatbelt`)
- ✅ Phát hiện dùng điện thoại (`phone`)
- ✅ Phát hiện ngáp ngủ (`yawn`)
- ✅ Phát hiện nhắm mắt (`eye`)
- ✅ Phát hiện mất tập trung (`head`)
- ✅ Phát hiện không cầm vô lăng (`hand`)

### 2. **Giám sát hành trình** 🗺️
- ✅ Theo dõi vị trí xe thời gian thực
- ✅ Hiển thị tuyến đường trên bản đồ
- ✅ Quản lý đội xe và tài xế
- ✅ Camera đa góc (tài xế, trước, hành khách, lùi)

### 3. **Cảnh báo thời gian thực** 🔔
- ✅ Cảnh báo âm thanh tự động
- ✅ Gửi thông báo vào chatbot
- ✅ Lưu vi phạm vào database
- ✅ Phân loại mức độ (warning/critical)

### 4. **Dashboard quản lý** 📊
- ✅ Xem video stream từ camera
- ✅ Thống kê vi phạm
- ✅ Quản lý tuyến đường
- ✅ Chatbot AI hỗ trợ

---

## 🏗️ KIẾN TRÚC HỆ THỐNG

```
┌─────────────────────────────────────────────────────────────┐
│              HỆ THỐNG GIÁM SÁT GIAO THÔNG AI                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Camera     │    │   Camera     │    │   Camera     │  │
│  │   Tài xế     │    │   Hành trình │    │   Giao thông │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │          │
│         └───────────────────┼───────────────────┘          │
│                             │                               │
│                    ┌────────▼────────┐                      │
│                    │   Flask Server  │                      │
│                    │   (drive-auth.py)    │                      │
│                    └────────┬────────┘                      │
│                             │                               │
│         ┌───────────────────┼───────────────────┐          │
│         │                   │                   │          │
│  ┌──────▼───────┐   ┌──────▼───────┐   ┌──────▼───────┐   │
│  │  AI Models   │   │  Database    │   │   Chatbot    │   │
│  │  - YOLO      │   │  - MySQL     │   │  - Rule-based│   │
│  │  - dlib      │   │  - PyMySQL   │   │  - LLM API   │   │
│  │  - MediaPipe │   │  - bcrypt    │   │  - Groq      │   │
│  └──────────────┘   └──────────────┘   └──────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 LUỒNG HOẠT ĐỘNG

### **Luồng giám sát AI:**

```
1. Video Input (camera_input/)
        ↓
2. Đọc frame từ video
        ↓
3. AI Detection:
   - Face landmarks (dlib 68 points)
   - Eye Aspect Ratio (EAR) → Phát hiện nhắm mắt
   - Mouth Aspect Ratio (MAR) → Phát hiện ngáp
   - YOLO object detection → Phone, seatbelt
   - MediaPipe → Hand detection
        ↓
4. Nếu phát hiện vi phạm:
   - Phát âm thanh cảnh báo
   - Gửi alert vào chatbot
   - Lưu vào database (canh_bao_vi_pham)
   - Ghi hình video (nếu bật)
        ↓
5. Hiển thị video với bounding boxes
```

### **Luồng Chatbot AI:**

```
User nhắn tin
        ↓
AI xử lý:
   - Rule-based (if-else)
   - Hoặc LLM API (Groq/OpenAI/Gemini)
        ↓
Trả lời:
   - Thông tin xe
   - Thống kê vi phạm
   - Vị trí tài xế
   - Thời tiết
        ↓
Hiển thị trong chat interface
```

---

## 💻 YÊU CẦU HỆ THỐNG

### **Phần cứng:**
- **CPU:** Intel Core i5 trở lên (hoặc AMD tương đương)
- **RAM:** 8GB tối thiểu (16GB khuyến nghị)
- **GPU:** NVIDIA GPU với CUDA support (tùy chọn, tăng tốc AI)
- **Storage:** 10GB trống cho models và video

### **Phần mềm:**
- **OS:** macOS 10.14+, Ubuntu 18.04+, Windows 10+
- **Python:** 3.8 - 3.10
- **Database:** MySQL 5.7+ hoặc MariaDB 10.3+
- **CMake:** 3.15+ (để build dlib)
- **Git:** Để clone repository

---

## 📥 HƯỚNG DẪN CÀI ĐẶT

### **Bước 1: Clone repository**

```bash
cd /Users/vinhdv/Documents/Clone
git clone <repository-url> AI-Traffic-Monitoring-System
cd AI-Traffic-Monitoring-System
```

### **Bước 2: Cài đặt CMake**

CMake cần thiết để build thư viện dlib.

#### **macOS:**
```bash
# Cài đặt qua Homebrew
brew install cmake

# Kiểm tra phiên bản
cmake --version
```

#### **Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install cmake

# Kiểm tra phiên bản
cmake --version
```

#### **Windows:**
1. Download từ: https://cmake.org/download/
2. Cài đặt và thêm vào PATH

### **Bước 3: Tạo virtual environment**

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### **Bước 4: Cài đặt dependencies**

```bash
# Nâng cấp pip
pip install --upgrade pip

# Cài đặt các package cơ bản trước
pip install numpy==1.21.2

# Cài đặt dlib (cần CMake)
pip install dlib==19.22.0

# Cài đặt các package còn lại
pip install -r requirements.txt
```

**Lưu ý quan trọng:**

Nếu gặp lỗi khi cài `dlib`, hãy cài thêm các dependencies hệ thống:

#### **macOS:**
```bash
brew install cmake
```

#### **Ubuntu/Debian:**
```bash
sudo apt-get install build-essential cmake
sudo apt-get install libopenblas-dev liblapack-dev
sudo apt-get install libx11-dev libgtk-3-dev
```

#### **Windows:**
- Cài đặt Visual Studio Build Tools
- Download từ: https://visualstudio.microsoft.com/downloads/

### **Bước 5: Cài đặt Database**

```bash
# 1. Tạo database
mysql -u root -p -e "CREATE DATABASE giam_sat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 2. Import schema
mysql -u root -p giam_sat < database_schema.sql

# 3. Kiểm tra
mysql -u root -p giam_sat -e "SHOW TABLES;"
```

### **Bước 6: Cấu hình environment**

```bash
# Copy file cấu hình mẫu
cp .env.example .env

# Chỉnh sửa file .env với thông tin của bạn
nano .env  # hoặc dùng vim, code, v.v.
```

**Nội dung file `.env`:**
```env
# Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=mat_khau_cua_ban
MYSQL_DB=giam_sat

# Flask
SECRET_KEY=khoa-bi-mat-cua-ban
FLASK_DEBUG=True
FLASK_PORT=5001
FLASK_HOST=0.0.0.0

# Session
SESSION_TIMEOUT=24

# CORS
CORS_ORIGINS=*
```

### **Bước 7: Download AI Models**

Đảm bảo các files model tồn tại trong thư mục `py/weights/`:

- `yolov8n.pt` - YOLOv8 nano model
- `shape_predictor_68_face_landmarks.dat` - Dlib facial landmarks

**Download shape_predictor:**
```bash
cd py
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
```

**Download YOLOv8:**
```python
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
```

---

## ⚙️ CẤU HÌNH

### **Cấu hình Database**

Sửa file `.env` với thông tin MySQL của bạn:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=mat_khau_cua_ban
MYSQL_DB=giam_sat
```

### **Cấu hình AI API (Tùy chọn)**

Để sử dụng AI chatbot thông minh hơn (không bắt buộc):

#### **Option 1: Groq (Miễn phí - Khuyến nghị)**

```bash
# 1. Đăng ký tại https://console.groq.com
# 2. Lấy API key
# 3. Cài đặt
pip install groq

# 4. Set environment variable
export GROQ_API_KEY="gsk_xxxxxxxxxxxxxx"
```

#### **Option 2: OpenAI ChatGPT (Trả phí)**

```bash
# 1. Đăng ký tại https://platform.openai.com
# 2. Lấy API key
# 3. Cài đặt
pip install openai

# 4. Set environment variable
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

### **Cấu hình Video Input**

Đặt video files trong thư mục `py/video_input/`:

```bash
# Cấu trúc thư mục
py/
├── video_input/
│   ├── truoc1.mp4      # Camera trước
│   ├── truoc2.mp4
│   ├── trongxe1.mp4    # Camera trong xe
│   └── sau1.mp4        # Camera sau
```

---

## 🚀 CÁCH CHẠY

### **Phương pháp 1: Chạy trực tiếp**

```bash
# 1. Kích hoạt virtual environment
source venv/bin/activate  # macOS/Linux
# hoặc
venv\Scripts\activate     # Windows

# 2. Di chuyển vào thư mục Web
cd py/Web

# 3. Chạy Flask server
python drive.py
```

### **Phương pháp 2: Chạy với authentication**

```bash
cd py/Web
python drive_auth.py
```

### **Truy cập Dashboard**

Sau khi server khởi động, mở trình duyệt:

- **Dashboard chính:** http://localhost:5001/dashboard
- **Camera giám sát:** http://localhost:5001/traffic_bus
- **API Routes:** http://localhost:5001/api/routes

---

## 🔌 API ENDPOINTS

### **Authentication**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Đăng nhập |
| POST | `/api/logout` | Đăng xuất |
| GET | `/api/auth/check` | Kiểm tra session |

### **Routes (Tuyến đường)**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/routes` | Lấy tất cả tuyến đường |
| GET | `/api/routes/<id>` | Lấy chi tiết tuyến |
| POST | `/api/routes` | Tạo tuyến mới |
| PUT | `/api/routes/<id>` | Cập nhật tuyến |
| DELETE | `/api/routes/<id>` | Xóa tuyến |

### **Vehicles (Phương tiện)**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vehicles` | Lấy danh sách xe |
| GET | `/api/vehicles/<id>` | Lấy chi tiết xe |
| POST | `/api/vehicles` | Thêm xe mới |
| PUT | `/api/vehicles/<id>` | Cập nhật xe |

### **Violations (Vi phạm)**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/violations` | Lấy danh sách vi phạm |
| GET | `/api/violations/stats` | Thống kê vi phạm |
| POST | `/api/violations` | Tạo cảnh báo vi phạm |

### **Cameras**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cameras` | Lấy danh sách camera |
| GET | `/api/cameras/<id>/stream` | Stream video camera |

---

## 🗄️ CẤU TRÚC DATABASE

### **Bảng chính:**

#### `nguoi_dung` - Người dùng
```sql
- id: int (PK)
- ten_dang_nhap: varchar(50)
- mat_khau: varchar(255) - bcrypt hashed
- vai_tro: enum('admin','user')
- ho_ten: varchar(100)
- trang_thai_hoat_dong: tinyint
```

#### `tai_xe` - Tài xế
```sql
- id: int (PK)
- ma_tai_xe: varchar(20)
- ho_ten: varchar(100)
- so_dien_thoai: varchar(20)
- so_giay_phep_lai_xe: varchar(50)
- diem_danh_gia: int
- id_nguoi_dung: int (FK)
```

#### `phuong_tien` - Phương tiện
```sql
- id: int (PK)
- bien_so: varchar(20)
- loai_xe: varchar(50)
- id_tai_xe: int (FK)
- id_tuyen_duong: varchar(50) (FK)
- vi_tri: varchar(50)
- trang_thai_hoat_dong: varchar(50)
- lat, lng: double (tọa độ)
```

#### `canh_bao_vi_pham` - Cảnh báo vi phạm
```sql
- id: int (PK)
- loai_vi_pham: varchar(50) - seatbelt, phone, yawn, eye, head, hand
- noi_dung_vi_pham: varchar(255)
- muc_do: varchar(20) - warning, critical
- thoi_gian_vi_pham: datetime
- id_phuong_tien: int (FK)
- id_tai_xe: int (FK)
- da_doc: tinyint
```

#### `tuyen_duong` - Tuyến đường
```sql
- id: varchar(50) (PK)
- ten_tuyen: varchar(100)
- mo_ta: text
- start_lat, start_lng: decimal
- end_lat, end_lng: decimal
- distance: decimal (km)
- duration: int (phút)
- route_color: varchar(20)
```

#### `tuyen_duong_path` - Đường đi chi tiết
```sql
- id: int (PK)
- id_tuyen_duong: varchar(50) (FK)
- point_order: int
- latitude, longitude: decimal
```

---

## 🧪 TEST AI CHATBOT

### **Test với Rule-based AI:**

```bash
# 1. Chạy server
cd py/Web
python drive_auth.py

# 2. Mở browser
http://localhost:5001/

# 3. Click vào nút chat 💬 và nhắn:
- "Xin chào"
- "Xe 29B-222.22 ở đâu?"
- "Vi phạm hôm nay thế nào?"
- "Tài xế nào đang lái?"
```

### **Test với LLM API (Groq):**

```bash
# 1. Cài đặt
pip install groq

# 2. Set API key
export GROQ_API_KEY="gsk_xxxxxxxxxxxxxx"

# 3. Chạy server
python drive.py

# 4. Test chat với câu hỏi phức tạp:
- "Làm sao để lái xe an toàn?"
- "Kể chuyện cười về giao thông"
- "Thời tiết Hà Nội hôm nay"
```

---

## 🔧 XỬ LÝ SỰ CỐ

### **Lỗi: "ImportError: No module named 'dlib'"**

```bash
# 1. Đảm bảo CMake đã cài
cmake --version

# 2. Cài lại dlib
pip uninstall dlib
pip install dlib==19.22.0

# 3. Nếu vẫn lỗi, cài dependencies:
# macOS:
brew install cmake

# Ubuntu:
sudo apt-get install build-essential cmake libopenblas-dev
```

### **Lỗi: "MySQL Connection refused"**

```bash
# 1. Kiểm tra MySQL đang chạy
# macOS:
brew services list | grep mysql

# Ubuntu:
sudo systemctl status mysql

# 2. Start MySQL nếu chưa chạy
# macOS:
brew services start mysql

# Ubuntu:
sudo systemctl start mysql

# 3. Kiểm tra thông tin kết nối trong .env
```

### **Lỗi: "Camera not found" hoặc "Video file not found"**

```bash
# 1. Kiểm tra file video tồn tại
ls py/video_input/

# 2. Kiểm tra đường dẫn trong database
mysql -u root -p giam_sat -e "SELECT video_file FROM camera_xe;"

# 3. Đảm bảo video files có định dạng .mp4
```

### **Lỗi: "Port 5001 already in use"**

```bash
# 1. Tìm process đang dùng port
lsof -i :5001

# 2. Kill process
kill -9 <PID>

# 3. Hoặc đổi port trong .env
FLASK_PORT=5002
```

### **Lỗi: "API key not found" (với AI Chatbot)**

```bash
# 1. Kiểm tra environment variable
echo $GROQ_API_KEY

# 2. Set lại
export GROQ_API_KEY="gsk_xxxxxxxxxxxxxx"

# 3. Thêm vào ~/.zshrc hoặc ~/.bashrc để persistent
echo 'export GROQ_API_KEY="gsk_xxxxxxxxxxxxxx"' >> ~/.zshrc
source ~/.zshrc
```

### **Lỗi: "Fallback về rule-based AI"**

- API key không đúng
- Hết rate limit
- Mất internet

**Khắc phục:**
```bash
# Kiểm tra log để biết chi tiết
# Trong drive.py, tìm dòng:
print(f"[LLM Error] {e}")
```

---

## 📊 TÀI KHOẢN MẶC ĐỊNH

Sau khi import database, bạn có thể đăng nhập với:

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Admin |
| `user` | `user123` | User |
| `driver1` | `user123` | Driver |

**Đổi mật khẩu:**
```python
# Chạy script để tạo mật khẩu mới
python cr.py
```

---

## 📁 CẤU TRÚC THƯ MỤC

```
AI-Traffic-Monitoring-System/
├── .env.example              # File cấu hình mẫu
├── .env                      # File cấu hình (tạo sau khi copy)
├── requirements.txt          # Python dependencies
├── database_schema.sql       # Database schema
├── cr.py                     # Script tạo password hash
├── README.md                 # File này
├── py/
│   ├── Web/
│   │ 
│   │   ├── drive_auth.py     # Flask server với auth
│   │   ├── models.py         # Database models
│   │   ├── static/           # CSS, JS, images
│   │   └── templates/        # HTML templates
│   ├── video_input/          # Video files đầu vào
│   ├── weights/              # AI models (YOLO, etc.)
│   ├── Sound/                # Audio alerts
│   ├── pictures/             # Output images
│   └── runs/                 # YOLO runs output
└── venv/                     # Virtual environment
```

---

## 🎯 TÍNH NĂNG MỞ RỘNG (TƯƠNG LAI)

- [ ] Real-time GPS tracking
- [ ] Multi-camera support
- [ ] License plate recognition
- [ ] Speed detection
- [ ] Lane departure warning
- [ ] Collision detection
- [ ] Mobile app integration
- [ ] Cloud deployment
- [ ] Advanced analytics dashboard

---

## 📞 HỖ TRỢ

- **Documentation:** Xem các file `.md` trong project
- **Issues:** đang trong quá trình phát triển
- **Email:** daovinhgm2005@gmail.com

---

## 📝 LICENSE

MIT License - Xem file LICENSE để biết chi tiết.

---

## 👥 CONTRIBUTORS

- **Developer:** AI Traffic Monitoring Team
- **Version:** 1.0.0
- **Last Updated:** Tháng 3 năm 2026

---

**CHÚC BẠN THÀNH CÔNG! 🎉**

> **Lưu ý:** Đảm bảo đã cài đặt đầy đủ CMake, MySQL và các dependencies trước khi chạy.
