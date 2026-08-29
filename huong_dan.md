# Hướng Dẫn Cài Đặt Và Chạy Dự Án (Windows + macOS)

Tài liệu này hướng dẫn chi tiết để chạy dự án `AI-Traffic-Monitoring-System` trên máy mới, áp dụng cho cả Windows và macOS.

## 1. Tổng quan yêu cầu

Dự án này **không chỉ cần** cài `requirements.txt`. Bạn cần đầy đủ các thành phần sau:

- Python + môi trường ảo
- Thư viện Python từ `requirements.txt`
- MySQL + import schema
- Model files trong thư mục `py/weights/` và các file dữ liệu liên quan
- (Nếu dùng giao diện React) Node.js + build frontend

## 2. Chuẩn bị trước

### 2.1. Clone dự án

```bash
git clone <URL_REPO>
cd AI-Traffic-Monitoring-System
```

### 2.2. Chọn nhánh cần chạy

Ví dụ với nhánh `danmodels`:

```bash
git checkout danmodels
git pull
```

## 3. Cài Python và tạo môi trường ảo

Khuyến nghị Python 3.10.

### 3.1. macOS

Kiểm tra Python:

```bash
python3 --version
```

Tạo venv và kích hoạt:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Nâng pip và cài thư viện:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.2. Windows (PowerShell)

Kiểm tra Python:

```powershell
py --version
```

Tạo venv và kích hoạt:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Nếu bị chặn script:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Nâng pip và cài thư viện:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Cài MySQL bằng XAMPP + phpMyAdmin

Phần này viết theo đúng cách bạn đang dùng: **XAMPP + phpMyAdmin**.

## 4.1. Cài và bật MySQL trong XAMPP

### Windows

1. Cài XAMPP từ trang chính thức.
2. Mở **XAMPP Control Panel**.
3. Nhấn **Start** ở module **MySQL** (nếu dùng web admin thì có thể Start luôn Apache).

### macOS

1. Cài XAMPP bản cho macOS.
2. Mở ứng dụng **Manager-OSX** (XAMPP Manager).
3. Start service **MySQL** (và Apache nếu cần dùng phpMyAdmin qua web).

## 4.2. Tạo database bằng phpMyAdmin

1. Mở phpMyAdmin:
	- thường là `http://localhost/phpmyadmin`
2. Chọn tab **Databases**.
3. Tạo database mới tên: `giam_sat`
4. Collation khuyến nghị: `utf8mb4_unicode_ci`

## 4.3. Import schema `database_schema.sql` bằng phpMyAdmin

1. Click vào database `giam_sat`.
2. Chọn tab **Import**.
3. Chọn file: `database_schema.sql` (ở thư mục gốc dự án).
4. Nhấn **Go** để import.
5. Kiểm tra danh sách bảng đã xuất hiện đầy đủ.

## 4.4. Kiểm tra config kết nối DB

Dự án đang đọc config DB trong file:

- `py/Web/drive_auth.py`

Bạn cần đảm bảo các giá trị đúng với máy mới:

- host
- port
- user
- password
- database

Với XAMPP mặc định thường là:

- host: `localhost`
- port: `3306`
- user: `root`
- password: rỗng (`''`)
- database: `giam_sat`

Nếu bạn đã đặt mật khẩu `root` trong phpMyAdmin/XAMPP, hãy cập nhật lại trong code cho khớp.

## 5. Chuẩn bị model và dữ liệu

Đảm bảo các file sau tồn tại:

- `yolov8n.pt`
- thư mục `py/weights/` (các model custom)
- các thư mục dữ liệu video/ảnh mà dự án đang tham chiếu

Nếu thiếu model, hệ thống AI sẽ lỗi khi chạy.

## 6. (Bắt buộc nếu dùng giao diện React) Build frontend

Nếu dự án đang chạy giao diện React SPA, bạn cần build frontend:

Thư mục frontend:

- `py/Web/frontend`

### 6.1. Kiểm tra Node.js

```bash
node -v
npm -v
```

Khuyến nghị Node 18+.

### 6.2. Cài và build

```bash
cd py/Web/frontend
npm install
npm run build
cd ../../..
```

Build xong sẽ sinh file vào:

- `py/Web/static/react-spa/`

## 7. Chạy dự án

Từ thư mục gốc dự án:

### 7.1. macOS

```bash
source .venv/bin/activate
python py/Web/drive_auth.py
```

### 7.2. Windows (PowerShell)

```powershell
.\.venv\Scripts\Activate.ps1
python py\Web\drive_auth.py
```

Mở trình duyệt theo URL Flask in ra terminal (thường là `http://127.0.0.1:5000`).

## 8. Kiểm tra nhanh sau khi chạy

- Truy cập trang login được
- Đăng nhập thành công
- Tải được dashboard/trang chủ
- Không báo lỗi kết nối DB
- Camera/video stream hoạt động
- Nếu dùng React: route frontend hiển thị đúng

## 9. Lỗi thường gặp và cách xử lý

## 9.1. `ModuleNotFoundError`

Nguyên nhân: chưa kích hoạt venv hoặc chưa cài đủ package.

Cách xử lý:

```bash
# Kích hoạt venv trước
# rồi cài lại
pip install -r requirements.txt
```

## 9.2. Lỗi MySQL connection

Nguyên nhân:

- MySQL chưa chạy
- sai user/password
- chưa import schema

Cách xử lý:

- Start MySQL service trong XAMPP Control Panel / Manager-OSX
- Kiểm tra lại config DB trong `py/Web/drive_auth.py`
- Import lại `database_schema.sql` trong phpMyAdmin

## 9.3. Lỗi `dlib` trên Windows/macOS

`dlib` có thể cần toolchain native.

- Windows: cài Visual Studio Build Tools (C++ build tools)
- macOS: cài Xcode Command Line Tools:

```bash
xcode-select --install
```

Sau đó cài lại package.

## 9.4. Frontend không hiển thị đúng

Nguyên nhân: chưa build frontend hoặc thiếu file trong `react-spa`.

Cách xử lý:

```bash
cd py/Web/frontend
npm install
npm run build
```

## 9.5. Lỗi thiếu model

Nguyên nhân: thiếu file `.pt` hoặc đường dẫn sai.

Cách xử lý:

- Kiểm tra thư mục `py/weights/`
- Kiểm tra các đường dẫn model trong code

## 10. Gợi ý vận hành ổn định trên máy mới

- Luôn dùng `.venv` riêng cho từng máy
- Pin đúng version Python và Node
- Không commit `.env`, `node_modules`, file runtime
- Sau khi pull code mới: chạy lại `pip install -r requirements.txt`
- Nếu frontend thay đổi: chạy lại `npm run build`

## 11. Checklist nhanh (copy/paste)

### macOS

```bash
git checkout danmodels && git pull
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# Sau đó mở phpMyAdmin (http://localhost/phpmyadmin):
# 1) Tạo DB giam_sat (utf8mb4_unicode_ci)
# 2) Import file database_schema.sql
cd py/Web/frontend && npm install && npm run build && cd ../../..
python py/Web/drive_auth.py
```

### Windows (PowerShell)

```powershell
git checkout danmodels
git pull
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
# Sau đó mở phpMyAdmin (http://localhost/phpmyadmin):
# 1) Tạo DB giam_sat (utf8mb4_unicode_ci)
# 2) Import file database_schema.sql
cd py\Web\frontend
npm install
npm run build
cd ..\..\..
python py\Web\drive_auth.py
```

---

Nếu bạn muốn, mình có thể viết thêm 2 script tự động:

- `setup_mac.sh`
- `setup_windows.ps1`

để chỉ cần chạy 1 lệnh là setup gần như toàn bộ.