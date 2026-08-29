# Hướng Dẫn Cài Đặt Và Chạy Dự Án

Tài liệu này mô tả cách clone về và chạy project hiện tại trên máy local.

## 1. Yêu cầu

- Python 3.10+.
- Node.js 18+.
- MySQL đang chạy.
- File schema `database_schema.sql`.

## 2. Clone và tạo môi trường ảo

```bash
git clone <URL_REPO>
cd AI-Traffic-Monitoring-System
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Tạo database

```bash
mysql -uroot -p -e "CREATE DATABASE IF NOT EXISTS giam_sat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -uroot -p giam_sat < database_schema.sql
```

Nếu MySQL của bạn có user/password khác mặc định, hãy cập nhật trong `.env` hoặc `backend/.env`.

## 4. Chạy backend

```bash
source .venv/bin/activate
python -m backend.app.main
```

Backend mặc định chạy ở cổng `5001` và mở trang login ở `http://localhost:5001/login`.

## 5. Chạy frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend mặc định chạy ở `http://localhost:3001`.

## 6. Biến môi trường hay dùng

```dotenv
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=giam_sat
PORT=5001
FRONTEND_URL=http://localhost:3001
AI_ENABLED=false
```

## 7. Nếu AI runtime bị thiếu asset

- Backend vẫn có thể chạy API.
- Phần AI sẽ báo thiếu file model hoặc video/sound.
- Thêm các file cần thiết vào `backend/assets/weights`, `backend/assets/videos`, `backend/assets/sounds` rồi bật lại `AI_ENABLED=true`.

## 8. Mở ứng dụng

- Đăng nhập qua `http://localhost:3001/login`.
- Nếu cần kiểm tra API, xem backend log ở terminal đang chạy Flask.