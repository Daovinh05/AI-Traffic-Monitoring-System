# 🤖 AI CHATBOT - HƯỚNG DẪN SỬ DỤNG

## 📋 Tính năng AI trong Chatbot

### 1. **AI Tự động gửi cảnh báo** ✅
Khi AI phát hiện vi phạm → Tự động gửi tin vào chatbot:
```
🔔 📱 Tài xế đang DÙNG ĐIỆN THOẠI!
⏰ 14:30:25 - 03/12/2024
```

### 2. **AI Trả lời tin nhắn tự động** ✅
User nhắn gì → AI trả lời thông minh:

| User nhắn | AI trả lời |
|-----------|-----------|
| "Xin chào" | "Xin chào quý khách! 🚗 Tôi là Vietravel Supporter..." |
| "Xe 29B-222.22 ở đâu?" | "🚗 Xe 29B-222.22 do tài xế Trần Văn Hoan lái, đang ở Bến xe Mỹ Đình" |
| "Vi phạm hôm nay" | "📊 Thống kê vi phạm: 📱 3 lần, 😴 5 lần, ⚠️ 2 lần..." |
| "Tài xế nào đang lái?" | "👨‍✈️ Danh sách tài xế: 1. Nguyễn Văn Đức..." |
| "Thời tiết thế nào?" | "🌤️ Hà Nội 25°C, nắng đẹp, giao thông thuận lợi" |
| "Cảm ơn" | "Dạ không có gì ạ! Rất vui được hỗ trợ 😊" |

---

## 🎯 Cách AI hoạt động

### **Level 1: Rule-based AI** (✅ Đang dùng)
```python
def generate_bot_response(message):
    if "xin chào" in message:
        return "Xin chào quý khách! 🚗"
    elif "xe ở đâu" in message:
        # Tìm xe trong database
        return "🚗 Xe đang ở..."
    # ... 8 rules khác
```

**Ưu điểm:**
- ✅ Nhanh, chính xác
- ✅ Không cần internet
- ✅ Dễ tùy chỉnh

**Nhược điểm:**
- ❌ Chỉ trả lời theo rule định sẵn
- ❌ Không hiểu ngữ cảnh phức tạp

---

### **Level 2: LLM AI (ChatGPT/Gemini)** (🔧 Tùy chọn)
```python
import openai

def process_ai_chat_message(message):
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=[
            {'role': 'system', 'content': 'Bạn là trợ lý giao thông Vietravel'},
            {'role': 'user', 'content': message}
        ]
    )
    return response.choices[0].message.content
```

**Ưu điểm:**
- ✅ Hiểu ngữ cảnh tự nhiên
- ✅ Trả lời thông minh như người
- ✅ Xử lý câu hỏi phức tạp

**Nhược điểm:**
- ❌ Cần API key (trả phí)
- ❌ Cần internet
- ❌ Chậm hơn rule-based

---

## 🚀 Test AI Chatbot

### **Bước 1: Chạy backend**
```bash
cd /Users/vinhdv/Documents/Clone/AI-Traffic-Monitoring-System/py/Web
python drive.py
```

### **Bước 2: Mở chatbot**
```
http://localhost:5001/traffic_bus
```

### **Bước 3: Nhắn tin test**

Click vào nút chat 💬 và nhắn:

```
👤 Bạn: Xin chào
🤖 Bot: Xin chào quý khách! 🚗 Tôi là Vietravel Supporter...

👤 Bạn: Xe 29B-222.22 ở đâu?
🤖 Bot: 🚗 Xe 29B-222.22 do tài xế Trần Văn Hoan lái...

👤 Bạn: Vi phạm hôm nay thế nào?
🤖 Bot: 📊 Thống kê vi phạm hôm nay:
        - 📱 Dùng điện thoại: 3 lần
        - 😴 Ngáp ngủ: 5 lần
        - ⚠️ Không dây an toàn: 2 lần

👤 Bạn: Cảm ơn
🤖 Bot: Dạ không có gì ạ! Rất vui được hỗ trợ quý khách 😊
```

---

## 🔧 Tùy chỉnh AI

### **Thêm rule mới:**

Sửa file `drive.py`, hàm `generate_bot_response()`:

```python
# 9. Hỏi về bản đồ / đường đi
if any(x in message_lower for x in ['bản đồ', 'đường nào', 'lối nào']):
    return '''🗺️ Bản đồ tuyến đường:
- Tuyến 1: Nội Bài -> Võ Chí Công -> Đào Tấn
- Tuyến 2: BX Mỹ Đình -> Phạm Hùng -> BX Yên Nghĩa
- Tuyến 3: Hải Phòng -> BX Nước Ngầm

Bạn cần tuyến nào?'''
```

### **Dùng ChatGPT:**

1. Cài OpenAI:
```bash
pip install openai
```

2. Sửa file `drive.py`:
```python
def process_ai_chat_message(message, vehicle_id=None):
    import openai
    openai.api_key = 'sk-YOUR_API_KEY'
    
    context = f"""
    Bạn là trợ lý ảo của Vietravel, hỗ trợ giám sát giao thông.
    
    Cảnh báo AI hiện tại:
    - Eye: {warnings.get('eye', '')}
    - Phone: {warnings.get('phone', '')}
    - Seatbelt: {warnings.get('seatbelt', '')}
    
    User message: {message}
    
    Trả lời ngắn gọn, thân thiện, bằng tiếng Việt:
    """
    
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'system', 'content': 'Bạn là trợ lý giao thông Vietravel'},
            {'role': 'user', 'content': context}
        ]
    )
    return response.choices[0].message.content
```

3. Restart backend:
```bash
python drive.py
```

---

## 📊 So sánh các phương án

| Phương án | Tốc độ | Thông minh | Chi phí | Độ khó |
|-----------|--------|-----------|---------|--------|
| Rule-based | ⚡⚡⚡ | ⭐⭐ | Miễn phí | Dễ |
| ChatGPT 3.5 | ⚡⚡ | ⭐⭐⭐⭐ | $0.002/1K tokens | Trung bình |
| ChatGPT 4 | ⚡ | ⭐⭐⭐⭐⭐ | $0.03/1K tokens | Trung bình |
| Gemini Pro | ⚡⚡ | ⭐⭐⭐⭐ | Miễn phí (giới hạn) | Trung bình |
| VLLM (local) | ⚡⚡⚡ | ⭐⭐⭐⭐ | Free (cần GPU) | Khó |

---

## 🎯 Khuyến nghị

### **Dùng Rule-based khi:**
- ✅ Cần tốc độ cao
- ✅ Không có internet
- ✅ Ngân sách thấp
- ✅ Câu hỏi đơn giản, lặp lại

### **Dùng ChatGPT khi:**
- ✅ Cần xử lý ngữ cảnh phức tạp
- ✅ Có ngân sách
- ✅ Có internet
- ✅ Trải nghiệm người dùng cao cấp

---

## 📈 Nâng cao (Future)

### **1. AI học từ lịch sử:**
```python
# Lưu tin nhắn vào database
# AI học pattern từ tin nhắn cũ
# Tự động cải thiện phản hồi
```

### **2. AI phân tích cảm xúc:**
```python
# User giận dữ → Ưu tiên xử lý nhanh
# User vui vẻ → Gợi ý dịch vụ khác
```

### **3. AI đa ngôn ngữ:**
```python
# Tự động detect ngôn ngữ
# Trả lời bằng tiếng Việt/Anh/Pháp...
```

### **4. AI voice chat:**
```python
# User nói → AI nghe → AI trả lời → AI nói
# Tích hợp Google Speech-to-Text + Text-to-Speech
```

---

## ✅ Checklist test AI

- [ ] Nhắn "Xin chào" → Bot chào lại
- [ ] Nhắn "Xe 29B-222.22 ở đâu" → Bot trả lời vị trí
- [ ] Nhắn "Vi phạm" → Bot thống kê
- [ ] Nhắn "Cảm ơn" → Bot trả lời lịch sự
- [ ] Đưa điện thoại vào camera → Bot tự động cảnh báo
- [ ] Nói "Xem cảnh báo" → Bot mở AI Alerts Panel

---

**Chúc bạn thành công! 🎉**

> **AI Power:** Rule-based + Optional ChatGPT  
> **Language:** Tiếng Việt 🇻🇳  
> **Response Time:** < 1 giây
