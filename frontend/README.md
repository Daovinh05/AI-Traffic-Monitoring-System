# Frontend

## Cấu trúc thư mục

```text
frontend/
|___ src/
|    |___ app/                      Next.js App Router và các URL của hệ thống
|    |    |___ login/               Trang đăng nhập
|    |    |___ admin/
|    |    |    |___ dashboard/      Route tương thích cho dashboard quản trị
|    |    |___ dashboard/
|    |    |    |___ route.ts        Proxy HTML dashboard từ Flask backend
|    |    |___ user/
|    |    |    |___ dashboard/      Trang tổng quan dành cho tài xế
|    |    |    |___ drive/          Trang lái xe và giám sát AI
|    |    |    |___ history/        Lịch sử cảnh báo và video
|    |    |    |___ chatbot/        Chatbot và tư vấn luật giao thông
|    |    |___ layout.tsx           Layout gốc của ứng dụng
|    |    |___ globals.css          CSS dùng chung toàn frontend
|    |___ components/               Component React dùng lại giữa các trang
|    |___ constants/                URL backend và hằng số cấu hình
|    |___ features/                 Vị trí mở rộng module theo từng tính năng
|    |___ hooks/                    React hooks dùng chung
|    |___ services/                 Client gọi API và xử lý dữ liệu frontend
|    |___ types/                    Kiểu dữ liệu TypeScript
|    |___ utils/                    Hàm tiện ích phía frontend
|___ legacy-templates/
|    |___ Dashboard.html            Giao diện dashboard quản trị gốc
|    |___ trang_chu.html            Giao diện trang chủ tài xế
|    |___ lai_xe.html               Giao diện giám sát khi lái xe
|    |___ lich_su.html              Giao diện lịch sử cảnh báo
|    |___ tu_van.html               Giao diện chatbot tư vấn
|___ public/
|    |___ legacy/                   Ảnh và static assets của giao diện cũ
|___ next.config.ts                 Rewrite API, stream và tài nguyên về backend
|___ package.json                   Dependencies và npm scripts
|___ Dockerfile                     Cấu hình image frontend khi cần chạy Docker
```

## Các route

Next.js App Router UI:

- `/login`
- `/admin/dashboard`
- `/user/dashboard`
- `/user/drive`
- `/user/history`
- `/user/chatbot`

Các page gọi Flask API qua rewrite trong `next.config.ts`. Video stream,
recording và sound cũng được proxy về backend.

## Chạy local

```bash
npm ci
npm run dev
npm run build
```
