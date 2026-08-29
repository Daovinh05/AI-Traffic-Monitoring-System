# 🚀 HƯỚNG DẪN DEPLOY LÊN RENDER.COM

## 📋 TỔNG QUAN

Hướng dẫn từng bước deploy hệ thống AI Traffic Monitoring lên **Render.com** với database **TiDB Cloud** (miễn phí).

---

## ⚙️ YÊU CẦU

- ✅ Tài khoản GitHub
- ✅ Tài khoản Render.com (miễn phí)
- ✅ Tài khoản TiDB Cloud (miễn phí 5GB)
- ✅ Code đã push lên GitHub (branch `render`)

---

## 📝 CÁC BƯỚC DEPLOY

---

### **BƯỚC 1: TẠO DATABASE TRÊN TIDB CLOUD**

#### **1.1. Đăng ký TiDB Cloud**

1. Truy cập: https://tidbcloud.com
2. Click **"Sign Up"** hoặc **"Get Started for Free"**
3. Đăng ký bằng:
   - Google account (nhanh nhất)
   - GitHub account
   - Email

#### **1.2. Tạo Cluster**

1. Sau khi đăng nhập, click **"Create Cluster"**
2. Chọn configuration:
   - **Provider:** AWS
   - **Region:** `Asia Pacific (Singapore)` - gần VN nhất
   - **Plan:** **Serverless** (MIỄN PHÍ)
   - **Cluster Name:** `ai-traffic-db`
3. Click **"Create"**

#### **1.3. Lấy Connection Details**

1. Sau khi cluster tạo xong (~2-3 phút), click vào cluster name
2. Click **"Connect"** button
3. Chọn tab **"General"**
4. Copy các thông tin sau:

```
Host: gateway01.ap-southeast-1.prod.aws.tidbcloud.com
Port: 4000
User: <your-username>.root
Password: <your-password>
```

#### **1.4. Tạo Database `giam_sat`**

1. Trong TiDB Dashboard, click **"SQL Console"**
2. Chạy lệnh:

```sql
CREATE DATABASE giam_sat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. Kiểm tra:

```sql
SHOW DATABASES;
```

#### **1.5. Import Schema**

1. Mở file `database_schema.sql` trong project
2. Copy toàn bộ nội dung
3. Paste vào **SQL Console** của TiDB
4. Click **"Run"** hoặc nhấn `Ctrl+Enter`
5. Kiểm tra tables:

```sql
USE giam_sat;
SHOW TABLES;
```

#### **1.6. Insert Dữ Liệu Mẫu (Nếu Cần)**

Nếu bạn có dữ liệu từ XAMPP:

```bash
# Export từ XAMPP
mysqldump -u root -p giam_sat > giam_sat_backup.sql

# Import vào TiDB (dùng MySQL Workbench hoặc CLI)
mysql -h gateway01.ap-southeast-1.prod.aws.tidbcloud.com -P 4000 -u user -p giam_sat < giam_sat_backup.sql
```

---

### **BƯỚC 2: PUSH CODE LÊN GITHUB**

Code đã có sẵn trên branch `render`. Kiểm tra:

```bash
cd /Users/vinhdv/Documents/Clone/AI-Traffic-Monitoring-System

# Kiểm tra branch hiện tại
git branch

# Nếu chưa ở branch render, chuyển sang:
git checkout render

# Push lên GitHub (nếu chưa)
git push origin render
```

**Kiểm tra trên GitHub:**
- Truy cập: https://github.com/Congvinh2005/AI-Traffic-Monitoring-System/branches
- Đảm bảo branch `render` tồn tại

---

### **BƯỚC 3: DEPLOY LÊN RENDER.COM**

#### **3.1. Đăng ký Render**

1. Truy cập: https://render.com
2. Click **"Sign Up"**
3. Đăng nhập bằng:
   - GitHub account (khuyến nghị)
   - Google account
   - Email

#### **3.2. Tạo Web Service**

1. Sau khi đăng nhập, click **"New +"** → **"Web Service"**
2. **"Connect a repository"** hiện ra
3. Tìm và chọn repository: `AI-Traffic-Monitoring-System`
4. Click **"Connect"**

#### **3.3. Cấu Hình Service**

Điền thông tin sau:

| Field | Giá trị |
|-------|---------|
| **Name** | `ai-traffic-monitoring` |
| **Region** | `Singapore` |
| **Branch** | `render` |
| **Root Directory** | *(để trống)* |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python py/Web/drive_auth.py` |
| **Instance Type** | `Free` |

#### **3.4. Thêm Environment Variables**

Click **"Advanced"** → **"Add Environment Variable"** và thêm:

| Key | Value | Ghi chú |
|-----|-------|---------|
| `MYSQL_HOST` | `gateway01.ap-southeast-1.prod.aws.tidbcloud.com` | Từ TiDB |
| `MYSQL_PORT` | `4000` | TiDB dùng port 4000 |
| `MYSQL_USER` | `3XuyjmdVP1iQdpe.root` | Từ TiDB |
| `MYSQL_PASSWORD` | `PuFY9tQFwsnU8P5u` | Từ TiDB |
| `MYSQL_DB` | `giam_sat` | Database đã tạo |
| `SECRET_KEY` | *(để Render generate)* | Click "generateValue" |
| `FLASK_DEBUG` | `False` | Production mode |
| `FLASK_ENV` | `production` | |
| `SESSION_TIMEOUT` | `24` | Session 24 giờ |
| `CORS_ORIGINS` | `*` | Cho phép tất cả |
| `GROQ_API_KEY` | *(nhập key của bạn)* | AI Chatbot |

**Lưu ý quan trọng:**
- ✅ `MYSQL_PASSWORD` - Điền password từ TiDB Cloud
- ✅ `SECRET_KEY` - Render sẽ tự generate
- ✅ `GROQ_API_KEY` - Để chatbot AI hoạt động

#### **3.5. Deploy**

1. Review lại tất cả thông tin
2. Click **"Create Web Service"**
3. Render sẽ tự động:
   - Build image từ code
   - Cài đặt dependencies
   - Deploy service
4. Quá trình này mất **5-10 phút**

---

### **BƯỚC 4: KIỂM TRA DEPLOY**

#### **4.1. Xem Logs**

1. Trong Render Dashboard, click vào service của bạn
2. Click tab **"Logs"**
3. Xem logs để đảm bảo không có lỗi

**Logs thành công:**
```
AI TRAFFIC MONITORING SYSTEM - WITH AUTHENTICATION
==========================================================================
📋 TÀI KHOẢN:
  👮 Admin: username=admin, password=admin123
  👤 User:  username=user, password=user123
==========================================================================
🌐 URL: http://localhost:5001/login
==========================================================================
💡 Nhấn Ctrl+C để dừng server
==========================================================================
```

#### **4.2. Test Health Check**

Truy cập:
```
https://ai-traffic-monitoring.onrender.com/api/health
```

**Kết quả thành công:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-03-20T..."
}
```

#### **4.3. Test Dashboard**

Truy cập:
```
https://ai-traffic-monitoring.onrender.com/login
```

Đăng nhập với:
- **Username:** `admin`
- **Password:** `admin123`

**Test các tính năng:**
1. ✅ Đăng nhập thành công
2. ✅ Xem dashboard
3. ✅ Xem camera/traffic
4. ✅ Chat với chatbot
5. ✅ Xem thống kê vi phạm

---

### **BƯỚC 5: GIỮ SERVER LUÔN ONLINE (MIỄN PHÍ)**

Render free tier sẽ **sleep sau 15 phút** không hoạt động. Để giữ server luôn online:

#### **Dùng UptimeRobot (Miễn phí)**

1. **Đăng ký:** https://uptimerobot.com
2. **Add New Monitor:**
   - **Monitor Type:** HTTP(s)
   - **Friendly Name:** `AI Traffic Monitoring`
   - **URL:** `https://ai-traffic-monitoring.onrender.com/api/health`
   - **Monitoring Interval:** 5 minutes
3. **Click "Create Monitor"**

**Kết quả:**
- ✅ Server không bao giờ sleep
- ✅ Ping mỗi 5 phút
- ✅ Hoàn toàn miễn phí

---

## 🔧 XỬ LÝ SỰ CỐ

### **Lỗi 1: "Build Failed"**

**Triệu chứng:**
```
Build failed: Could not install requirements
```

**Nguyên nhân:**
- Thiếu file `requirements.txt`
- Lỗi cài đặt dependencies (dlib, opencv)

**Cách sửa:**
```bash
# 1. Kiểm tra requirements.txt có đầy đủ
cat requirements.txt

# 2. Test build local
pip install -r requirements.txt

# 3. Nếu lỗi dlib, cài cmake trước:
brew install cmake  # macOS
sudo apt install cmake  # Linux

# 4. Commit và push lại
git add .
git commit -m "Fix requirements"
git push origin render
```

---

### **Lỗi 2: "MySQL Connection Failed"**

**Triệu chứng:**
```
DB Error: (2003, "Can't connect to MySQL server")
```

**Nguyên nhân:**
- Sai credentials
- TiDB chưa cho phép kết nối từ xa
- Firewall block

**Cách sửa:**

1. **Kiểm tra credentials trong Render:**
   - Vào Render Dashboard → Environment
   - Kiểm tra `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`

2. **Test kết nối local:**
   ```bash
   mysql -h gateway01.ap-southeast-1.prod.aws.tidbcloud.com -P 4000 -u 3XuyjmdVP1iQdpe.root -p
   ```

3. **Trong TiDB Console:**
   ```sql
   SHOW GRANTS FOR '3XuyjmdVP1iQdpe.root';
   -- Đảm bảo user có quyền truy cập
   ```

---

### **Lỗi 3: "Module Not Found"**

**Triệu chứng:**
```
ModuleNotFoundError: No module named 'flask'
```

**Nguyên nhân:**
- `requirements.txt` không có package đó
- Lỗi pip install trong build process

**Cách sửa:**

1. Thêm package vào `requirements.txt`:
   ```
   flask==2.0.1
   ```

2. Push lại:
   ```bash
   git add requirements.txt
   git commit -m "Add missing package"
   git push origin render
   ```

---

### **Lỗi 4: "Port Already In Use"**

**Triệu chứng:**
```
OSError: [Errno 48] Address already in use
```

**Nguyên nhân:**
- Port 5001 đã được dùng
- Render yêu cầu port từ environment variable

**Cách sửa:**

Đảm bảo code đọc PORT từ environment:

```python
PORT = int(os.environ.get('PORT', 5001))
```

File `drive_auth.py` đã được sửa để hỗ trợ điều này.

---

### **Lỗi 5: "Service Sleep"**

**Triệu chứng:**
- Server không phản hồi sau 15 phút
- Lần đầu truy cập mất 30-60s để wake up

**Cách sửa:**

Dùng **UptimeRobot** (xem Bước 5) hoặc nâng cấp lên Render Starter ($7/tháng).

---

## 💰 CHI PHÍ DỰ KIẾN

### **Miễn Phí (Free Tier)**

| Service | Chi phí | Giới hạn |
|---------|---------|----------|
| Render Web Service | $0 | 750 giờ/tháng, 512MB RAM |
| TiDB Cloud | $0 | 5GB storage, 50M requests/tháng |
| UptimeRobot | $0 | 50 monitors, 5 phút interval |
| **Tổng** | **$0/tháng** | |

### **Nâng Cấp (Nếu Cần)**

| Service | Plan | Giá | Lợi ích |
|---------|------|-----|---------|
| Render | Starter | $7/tháng | Không sleep, 512MB RAM |
| Render | Standard | $25/tháng | 2GB RAM, priority support |
| TiDB | Pro | $0.18/GB/tháng | Nhiều storage hơn |

---

## 📊 MONITORING

### **Trong Render Dashboard:**

1. **Metrics:**
   - CPU usage
   - Memory usage
   - Request count
   - Response time

2. **Logs:**
   - Real-time logs
   - Error logs
   - Deploy logs

3. **Deploys:**
   - Lịch sử deploy
   - Status (success/failed)
   - Deploy time

### **Setup Alerts:**

1. Vào **Settings** → **Notifications**
2. Thêm email nhận thông báo:
   - Deploy failed
   - Service down
   - High resource usage

---

## 🔒 BẢO MẬT

### **Best Practices:**

1. ✅ **Không commit secrets:**
   - `.env` đã có trong `.gitignore`
   - Dùng Environment Variables trên Render

2. ✅ **Đổi SECRET_KEY trong production:**
   ```bash
   python -c "import os; print(os.urandom(24).hex())"
   ```

3. ✅ **Tắt FLASK_DEBUG:**
   ```
   FLASK_DEBUG=False
   ```

4. ✅ **Dùng HTTPS:**
   - Render tự động cấp SSL certificate
   - URL: `https://your-app.onrender.com`

5. ✅ **Giới hạn CORS (nếu cần):**
   ```
   CORS_ORIGINS=https://your-domain.com
   ```

---

## 📝 CHECKLIST HOÀN TẤT

- [ ] Tạo TiDB Cloud cluster
- [ ] Tạo database `giam_sat`
- [ ] Import `database_schema.sql`
- [ ] Push code lên GitHub (branch `render`)
- [ ] Đăng ký Render.com
- [ ] Tạo Web Service
- [ ] Điền Environment Variables
- [ ] Deploy thành công
- [ ] Test `/api/health`
- [ ] Test login dashboard
- [ ] Setup UptimeRobot
- [ ] Đổi mật khẩu admin (nếu cần)

---

## 🎉 HOÀN TẤT!

Sau khi deploy thành công:

1. ✅ Dashboard chạy trên: `https://ai-traffic-monitoring.onrender.com`
2. ✅ API endpoints hoạt động
3. ✅ Database kết nối TiDB Cloud
4. ✅ AI monitoring hoạt động
5. ✅ Chatbot AI hoạt động (với Groq API)

**URL quan trọng:**

| Dịch vụ | URL |
|---------|-----|
| Dashboard | `https://ai-traffic-monitoring.onrender.com/login` |
| Health Check | `https://ai-traffic-monitoring.onrender.com/api/health` |
| API Routes | `https://ai-traffic-monitoring.onrender.com/api/routes` |
| TiDB Console | https://tidbcloud.com/console |
| Render Dashboard | https://dashboard.render.com |

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề:

1. **Kiểm tra logs** trong Render Dashboard
2. **Test local** với `.env.tidb` trước khi deploy
3. **Đảm bảo MySQL kết nối được** từ internet
4. **Contact:** daovinhgm2005@gmail.com

---

## 🔄 UPDATE CODE SAU NÀY

Khi cần update code:

```bash
# 1. Commit changes
git add .
git commit -m "Update feature XYZ"

# 2. Push lên branch render
git push origin render

# 3. Render tự động deploy lại
# Vào Dashboard để xem deploy logs
```

---

**Chúc bạn deploy thành công! 🚀**

> **Lưu ý:** Server free tier có thể sleep sau 15 phút không hoạt động. Dùng UptimeRobot để giữ server luôn online.
