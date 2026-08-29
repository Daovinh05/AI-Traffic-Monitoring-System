# 🤖 SETUP AI LLAM API KEY

## 📋 Các lựa chọn AI API

### **1. GROQ (Khuyến nghị - MIỄN PHÍ)** ⭐

**Ưu điểm:**
- ✅ Miễn phí 100%
- ✅ Nhanh (70B model)
- ✅ Dễ setup
- ✅ Không cần credit card

**Nhược điểm:**
- ⚠️ Giới hạn request/ngày

---

### **2. OpenAI ChatGPT (Trả phí)**

**Ưu điểm:**
- ✅ Thông minh nhất
- ✅ Ổn định

**Nhược điểm:**
- ❌ Trả phí ($0.002/1K tokens)
- ❌ Cần credit card

---

### **3. Google Gemini (Miễn phí giới hạn)**

**Ưu điểm:**
- ✅ Miễn phí (giới hạn)
- ✅ Của Google

**Nhược điểm:**
- ⚠️ Cần Google account

---

## 🚀 HƯỚNG DẪN SETUP

### **Option 1: GROQ (MIỄN PHÍ) - KHUYẾN NGHỊ**

#### **Bước 1: Đăng ký tài khoản**
1. Truy cập: https://console.groq.com
2. Click "Sign Up"
3. Đăng nhập bằng Google/GitHub
4. Vào "API Keys"
5. Click "Create API Key"
6. Copy key (ví dụ: `gsk_xxxxxxxxxxxxxx`)

#### **Bước 2: Cài thư viện**
```bash
pip install groq
```

#### **Bước 3: Setup API key**

**Cách A: Dùng environment variable (khuyến nghị)**
```bash
# macOS/Linux
export GROQ_API_KEY="gsk_xxxxxxxxxxxxxx"

# Windows PowerShell
$env:GROQ_API_KEY="gsk_xxxxxxxxxxxxxx"

# Windows CMD
set GROQ_API_KEY=gsk_xxxxxxxxxxxxxx
```

**Cách B: Hardcode trong code (không khuyến khích)**
Sửa file `drive.py`:
```python
GROQ_API_KEY = "gsk_xxxxxxxxxxxxxx"  # Dán key của bạn
```

#### **Bước 4: Chạy và test**
```bash
python drive.py
```

Mở browser và chat:
```
👤 Bạn: Xin chào
🤖 AI: Xin chào quý khách! 🚗 Tôi là trợ lý AI của Vietravel...
```

---

### **Option 2: OpenAI ChatGPT**

#### **Bước 1: Đăng ký**
1. Truy cập: https://platform.openai.com
2. Đăng nhập/Đăng ký
3. Vào "API Keys"
4. Click "Create new secret key"
5. Copy key (ví dụ: `sk-xxxxxxxxxxxxxxxx`)

#### **Bước 2: Cài thư viện**
```bash
pip install openai
```

#### **Bước 3: Setup API key**
```bash
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
```

#### **Bước 4: Uncomment code trong drive.py**
Bỏ comment phần OpenAI trong hàm `call_llm_api()`:
```python
# === OPTION 2: OPENAI CHATGPT (TRẢ PHÍ) ===
try:
    from openai import OpenAI
    
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-YOUR_API_KEY')
    client = OpenAI(api_key=OPENAI_API_KEY)
    # ... rest of code
```

---

### **Option 3: Google Gemini**

#### **Bước 1: Đăng ký**
1. Truy cập: https://makersuite.google.com/app/apikey
2. Đăng nhập Google
3. Click "Create API Key"
4. Copy key

#### **Bước 2: Cài thư viện**
```bash
pip install google-generativeai
```

#### **Bước 3: Setup API key**
```bash
export GEMINI_API_KEY="xxxxxxxxxxxxxxxx"
```

#### **Bước 4: Uncomment code**
Bỏ comment phần Gemini trong `call_llm_api()`.

---

## 🧪 TEST AI CHATBOT

### **Test với GROQ:**

```bash
# 1. Cài đặt
pip install groq

# 2. Setup key
export GROQ_API_KEY="gsk_xxxxxxxxxxxxxx"

# 3. Chạy
python drive.py

# 4. Mở browser
http://localhost:5001/traffic_bus
```

### **Test commands:**

```
👤 Bạn: Hôm nay thời tiết thế nào?
🤖 AI: 🌤️ Thời tiết Hà Nội hôm nay đẹp, nhiệt độ 25°C...

👤 Bạn: Xe 29B-222.22 vi phạm gì?
🤖 AI: 📊 Xe 29B-222.22 có 2 vi phạm: 1 lần dùng điện thoại...

👤 Bạn: Làm sao để lái xe an toàn?
🤖 AI: 🚗 Để lái xe an toàn, bạn cần:
1. Không dùng điện thoại
2. Đeo dây an toàn
3. Tập trung quan sát
4. Giữ khoảng cách an toàn...

👤 Bạn: Kể chuyện cười về giao thông
🤖 AI: 😄 Chuyện vui giao thông:
Một anh cảnh sát hỏi tài xế: "Anh có biết tại sao tôi dừng anh không?"
Tài xế: "Dạ chắc tại em chạy nhanh quá?"
Cảnh sát: "Không, tại em quên bật đèn pha!"
```

---

## 📊 SO SÁNH CHI PHÍ

| Provider | Model | Giá | Miễn phí | Tốc độ |
|----------|-------|-----|----------|-------|
| **Groq** | Llama-3.1-70B | $0 | ✅ 100% | ⚡⚡⚡ |
| **OpenAI** | GPT-3.5-turbo | $0.002/1K tokens | ❌ | ⚡⚡ |
| **OpenAI** | GPT-4 | $0.03/1K tokens | ❌ | ⚡ |
| **Gemini** | Gemini-Pro | $0 (giới hạn) | ✅ | ⚡⚡ |

---

## 🔧 XỬ LÝ SỰ CỐ

### Lỗi: "ImportError: No module named 'groq'"
```bash
pip install groq
```

### Lỗi: "API key not found"
```bash
# Check key
echo $GROQ_API_KEY

# Set lại
export GROQ_API_KEY="gsk_xxxxx"
```

### Lỗi: "Rate limit exceeded"
- Groq free tier giới hạn request/phút
- Chờ 1 phút rồi thử lại
- Hoặc nâng cấp lên paid tier

### Lỗi: "Fallback về rule-based AI"
- API key không đúng
- Hết limit
- Mất internet
→ Kiểm tra log để biết chi tiết

---

## 🎯 KHUYẾN NGHỊ

### **Cho development:**
- ✅ Dùng **Groq** (miễn phí, nhanh)
- ✅ Test với ít request

### **Cho production:**
- ✅ Dùng **OpenAI GPT-4** (thông minh, ổn định)
- ✅ Hoặc **Groq paid tier** (rẻ hơn)

### **Cho demo:**
- ✅ Dùng **rule-based** (không cần API key)
- ✅ Hoặc **Groq free tier**

---

## 📈 NÂNG CAO

### **Dùng nhiều API (fallback):**
```python
def call_llm_api(message):
    # Thử Groq trước
    response = call_groq(message)
    if response:
        return response
    
    # Fallback sang OpenAI
    response = call_openai(message)
    if response:
        return response
    
    # Fallback sang Gemini
    response = call_gemini(message)
    if response:
        return response
    
    # Cuối cùng fallback về rule-based
    return generate_bot_response(message)
```

### **Cache câu trả lời:**
```python
cache = {}

def call_llm_api(message):
    if message in cache:
        return cache[message]
    
    response = groq_chat(message)
    cache[message] = response
    return response
```

---

## ✅ CHECKLIST

- [ ] Đăng ký Groq account
- [ ] Lấy API key
- [ ] Cài `pip install groq`
- [ ] Set environment variable
- [ ] Chạy `python drive.py`
- [ ] Test chat với AI
- [ ] AI trả lời thông minh (không phải if-else)

---

**Chúc thành công! 🎉**

> **API:** Groq (Llama-3.1-70B)  
> **Chi phí:** Miễn phí  
> **Tốc độ:** < 1 giây  
> **Ngôn ngữ:** Tiếng Việt 🇻🇳
