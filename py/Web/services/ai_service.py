"""
AI Service - Xử lý các API AI (Groq, Chatbot, Law Advisor)
"""
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

# ==================== BIẾN TOÀN CỤC ====================
warnings = {
    "eye": "",
    "yawn": "",
    "head": "",
    "phone": "",
    "seatbelt": "",
    "traffic": "",
    "congestion": "",
    "speed": "",
    "sign": "",
    "hand": "",
    "collision": "",
    "lane": ""
}


def call_groq_law_advisor(question):
    """
    Gọi Groq API để tư vấn luật giao thông
    """
    try:
        GROQ_API_KEY = os.getenv('GROQ_API_KEY')

        if not GROQ_API_KEY:
            print("⚠️ Không tìm thấy GROQ_API_KEY")
            return generate_law_response_fallback(question)

        client = Groq(api_key=GROQ_API_KEY)

        # === DỮ LIỆU LUẬT GIAO THÔNG VIỆT NAM (CẬP NHẬT 2026) ===
        law_database = """
**NGUỒN LUẬT:**
- Luật Giao thông đường bộ 2008
- Nghị định 100/2019/NĐ-CP (xử phạt vi phạm giao thông)
- Nghị định 123/2021/NĐ-CP (sửa đổi, bổ sung)
- Các văn bản hướng dẫn thi hành

**MỨC PHẠT CHÍNH XÁC 2026:**

### 1. PHẠT QUÁ TỐC ĐỘ:
**Ô tô:**
- Quá 5-10 km/h: 800.000đ (Điểm 100/2019/NĐ-CP)
- Quá 10-20 km/h: 3-5 triệu đồng + tước GPLX 1-3 tháng
- Quá 20-35 km/h: 6-8 triệu đồng + tước GPLX 2-4 tháng
- Quá trên 35 km/h: 10-12 triệu đồng + tước GPLX 4-6 tháng

**Xe máy:**
- Quá 5-10 km/h: 400-600 nghìn đồng
- Quá 10-20 km/h: 800 nghìn - 1 triệu đồng
- Quá 20-35 km/h: 4-5 triệu đồng + tước GPLX 1-3 tháng
- Quá trên 35 km/h: 6-8 triệu đồng + tước GPLX 2-4 tháng

### 2. PHẠT NỒNG ĐỘ CỒN (Điều 5, Nghị định 100):
**Ô tô:**
- Mức 1 (chưa vượt quá 50mg/100ml máu hoặc 0.25mg/1lít khí thở): 6-8 triệu đồng + tước GPLX 10-12 tháng
- Mức 2 (vượt quá 50-80mg/100ml máu hoặc 0.25-0.4mg/1lít khí thở): 16-18 triệu đồng + tước GPLX 16-18 tháng
- Mức 3 (vượt quá 80mg/100ml máu hoặc 0.4mg/1lít khí thở): 30-40 triệu đồng + tước GPLX 22-24 tháng

**Xe máy:**
- Mức 1: 2-3 triệu đồng + tước GPLX 10-12 tháng
- Mức 2: 4-5 triệu đồng + tước GPLX 16-18 tháng
- Mức 3: 6-8 triệu đồng + tước GPLX 22-24 tháng

### 3. PHẠT KHÔNG ĐỘI MŨ BẢO HIỂM (Điều 6, Nghị định 100):
- Người điều khiển: 400-600 nghìn đồng
- Người ngồi sau: 400-600 nghìn đồng
- Trẻ em dưới 6 tuổi: Được miễn trừ

### 4. PHẠT VƯỢT ĐÈN ĐỎ (Điều 5, Nghị định 100):
**Ô tô:** 4-6 triệu đồng + tước GPLX 1-3 tháng
**Xe máy:** 800 nghìn - 1 triệu đồng + tước GPLX 1-3 tháng

### 5. PHẠT KHÔNG CÓ GIẤY PHÉP LÁI (Điều 21, Nghị định 100):
**Ô tô:**
- Không mang theo: 100-200 nghìn đồng
- GPLX hết hạn dưới 3 tháng: 1-2 triệu đồng
- GPLX hết hạn trên 3 tháng: 3-5 triệu đồng
- Không có GPLX: 5-7 triệu đồng

**Xe máy:**
- Không mang theo: 100-200 nghìn đồng
- Không có GPLX: 1-2 triệu đồng

### 6. PHẠT SAI LÀN ĐƯỜNG:
**Ô tô:** 3-5 triệu đồng + tước GPLX 1-3 tháng
**Xe máy:** 400-600 nghìn đồng

### 7. PHẠT ĐỖ XE SAI QUY ĐỊNH:
**Ô tô:**
- Đỗ xe không đúng nơi quy định: 200-300 nghìn đồng
- Đỗ xe trên vỉa hè: 800 nghìn - 1 triệu đồng
- Đỗ xe chắn lối ra vào: 4-6 triệu đồng

**Xe máy:**
- Đỗ xe không đúng nơi quy định: 100-200 nghìn đồng
- Đỗ xe trên vỉa hè: 200-300 nghìn đồng

### 8. HÌNH PHẠT BỔ SUNG:
- Tạm giữ phương tiện: 7-10 ngày (với một số vi phạm)
- Tước quyền sử dụng GPLX: 1-24 tháng tùy mức độ
- Trục xuất người nước ngoài vi phạm

**LƯU Ý QUAN TRỌNG:**
- Đèn vàng: Phải dừng trước vạch dừng, trừ khi đã đi quá vạch thì được đi tiếp
- Đèn xanh: Được phép đi, không bị phạt
- Người điều khiển xe phải tuân thủ tín hiệu đèn giao thông
- Nồng độ cồn: KHÔNG được lái xe nếu đã uống rượu bia (mức 0 với ô tô từ 2026)
"""

        # System prompt cho AI tư vấn luật
        system_prompt = f"""
Bạn là **Luật Sư Giao Thông AI** với 20 năm kinh nghiệm, chuyên tư vấn luật giao thông Việt Nam.

**DỮ LIỆU LUẬT CẬP NHẬT 2026:**
{law_database}

**NHIỆM VỤ CỦA BẠN:**
1. Trả lời chính xác dựa trên dữ liệu luật được cung cấp ở trên
2. Trích dẫn điều luật, nghị định cụ thể khi có thể
3. Phân biệt rõ các loại phương tiện (ôtô, xe máy, xe đạp, xe tải)
4. Đề cập đến hình phạt chính và hình phạt bổ sung
5. Sử dụng emoji phù hợp để làm rõ nghĩa
6. Trình bày có cấu trúc, dễ đọc
7. Luôn cập nhật theo quy định mới nhất 2026

**PHONG CÁCH TRẢ LỜI:**
- Thân thiện, nhiệt tình, chu đáo
- Giải thích rõ ràng, dễ hiểu
- Đưa ra ví dụ minh họa khi cần
- Cảnh báo nguy hiểm khi vi phạm nghiêm trọng

**CÁC CÂU HỎI THƯỜNG GẶP:**
- "Vượt đèn đỏ phạt bao nhiêu?" → Dựa vào mục 4
- "Nồng độ cồn phạt thế nào?" → Dựa vào mục 2
- "Không đội mũ bảo hiểm?" → Dựa vào mục 3
- "Quá tốc độ phạt sao?" → Dựa vào mục 1
- "Không có bằng lái?" → Dựa vào mục 5
- "Đèn xanh có bị phạt không?" → Trả lời KHÔNG, đèn xanh được đi
- "Đèn vàng được đi không?" → Dựa vào lưu ý quan trọng

**LUÔN NHẮC NGƯỜI DÙNG:**
- Đội mũ bảo hiểm
- Không uống rượu bia khi lái xe
- Tuân thủ tốc độ quy định
- Giữ khoảng cách an toàn
"""

        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=1000,
            top_p=1.0,
            stream=False
        )

        response = chat_completion.choices[0].message.content
        print(f"🤖 [GROQ LAW] Response: {response[:100]}...")
        return response

    except ImportError:
        print("⚠️ Chưa cài groq. Chạy: pip install groq")
        return generate_law_response_fallback(question)
    except Exception as e:
        print(f"❌ Lỗi Groq API: {e}")
        return generate_law_response_fallback(question)


def generate_law_response_fallback(question):
    """
    Fallback khi không có Groq API
    """
    q = question.lower()

    # Kiểm tra câu hỏi có hợp lệ không
    if 'đèn xanh' in q:
        return """**✅ ĐÈN XANH KHÔNG BỊ PHẠT!**

🚦 **Đèn xanh** là tín hiệu được phép đi, không vi phạm.

⚠️ **Lưu ý:**
• Vẫn phải giảm tốc độ khi qua giao lộ
• Quan sát và nhường đường cho người đi bộ
• Không được vượt xe khác trong giao lộ

❌ **Chỉ bị phạt khi:**
• Vượt đèn **ĐỎ** hoặc đèn **VÀNG** (khi chưa qua vạch dừng)
• Gây tai nạn hoặc ùn tắc giao thông"""

    if 'đèn vàng' in q:
        return """**🚦 QUY ĐỊNH VỀ ĐÈN VÀNG**

✅ **Được đi tiếp nếu:**
• Đã đi quá vạch dừng khi đèn chuyển vàng

❌ **Bị phạt nếu:**
• Cố tình tăng tốc để vượt khi đèn vừa chuyển vàng
• Chưa qua vạch dừng mà không dừng lại

**Mức phạt vượt đèn vàng:**
🚗 Ô tô: 4-6 triệu đồng
🏍️ Xe máy: 800 nghìn - 1 triệu đồng
⚠️ Tước GPLX 1-3 tháng"""

    if any(x in q for x in ['tốc độ', 'chạy nhanh', 'vượt tốc']):
        return """**📊 MỨC PHẠT QUÁ TỐC ĐỘ 2026**

🚗 **Ô tô:**
• Quá 5-10 km/h: 800.000đ
• Quá 10-20 km/h: 3-5 triệu đồng
• Quá 20-35 km/h: 6-8 triệu đồng
• Quá trên 35 km/h: 10-12 triệu đồng + treo bằng 2-4 tháng

🏍️ **Xe máy:**
• Quá 5-10 km/h: 400-600 nghìn đồng
• Quá 10-20 km/h: 800 nghìn - 1 triệu đồng
• Quá 20-35 km/h: 4-5 triệu đồng
• Quá trên 35 km/h: 6-8 triệu đồng

⚠️ Có thể bị tạm giữ phương tiện 7-10 ngày"""

    if any(x in q for x in ['nồng độ cồn', 'rượu', 'bia']):
        return """**🍺 MỨC PHẠT NỒNG ĐỘ CỒN 2026**

🚗 **Ô tô:**
• Mức 1: 6-8 triệu đồng
• Mức 2: 16-18 triệu đồng
• Mức 3: 30-40 triệu đồng

🏍️ **Xe máy:**
• Mức 1: 2-3 triệu đồng
• Mức 2: 4-5 triệu đồng
• Mức 3: 6-8 triệu đồng

⚠️ Tước GPLX 10-24 tháng, tạm giữ xe 7 ngày"""

    if any(x in q for x in ['mũ bảo hiểm', 'nón bảo hiểm']):
        return """**⛑️ PHẠT KHÔNG ĐỘI MŨ BẢO HIỂM**

👤 Người điều khiển: 400-600 nghìn đồng
👥 Người ngồi sau: 400-600 nghìn đồng

✅ Miễn trừ: Trẻ em dưới 6 tuổi, người bị bệnh"""

    if 'đèn đỏ' in q or ('vượt' in q and 'đèn' in q):
        return """**🚦 PHẠT VƯỢT ĐÈN ĐỎ**

🚗 Ô tô: 4-6 triệu đồng
🏍️ Xe máy: 800 nghìn - 1 triệu đồng

⚠️ Tước GPLX 1-3 tháng

💡 **Lưu ý:** Đèn đỏ phải dừng trước vạch sơn. 
Vượt đèn đỏ rất nguy hiểm, có thể gây tai nạn chết người!"""

    if any(x in q for x in ['giấy phép lái xe', 'bằng lái', 'không có bằng']):
        return """**📄 PHẠT KHÔNG CÓ GIẤY PHÉP LÁI**

🚗 **Ô tô:**
• Không mang theo: 100-200 nghìn đồng
• Hết hạn: 1-5 triệu đồng
• Không có GPLX: 5-7 triệu đồng

🏍️ **Xe máy:**
• Không mang theo: 100-200 nghìn đồng
• Không có GPLX: 1-2 triệu đồng"""

    if any(x in q for x in ['đăng ký xe', 'làm biển số', 'sang tên']):
        return """**📝 THỦ TỤC ĐĂNG KÝ XE MÁY**

**Hồ sơ gồm:**
1. CCCD/CMND + photo
2. Hóa đơn mua xe (bản gốc)
3. Giấy khai đăng ký xe

**Lệ phí:**
• Hà Nội/TP.HCM: 500.000đ
• Các tỉnh: 80.000đ

⏱️ Thời gian: 2-3 ngày làm việc"""

    return """Cảm ơn bạn đã đặt câu hỏi! 

🤖 Tôi là trợ lý tư vấn luật giao thông. 

**Tôi có thể giúp bạn:**
• Tra cứu mức phạt vi phạm
• Giải đáp tình huống giao thông
• Hướng dẫn thủ tục hành chính

**Ví dụ:**
• "Phạt quá tốc độ bao nhiêu?"
• "Phạt nồng độ cồn 2026?"
• "Thủ tục đăng ký xe máy?"
• "Đèn vàng được đi không?"

💡 Hãy hỏi cụ thể để được tư vấn chính xác!"""


def generate_bot_response(message, vehicle_id=None):
    """
    AI Rule-based response (fallback khi không có LLM API)
    """
    message_lower = message.lower().strip()

    # 1. Chào hỏi
    if any(x in message_lower for x in ['xin chào', 'hello', 'hi', 'chào']):
        return 'Xin chào quý khách! 🚗 Tôi là Vietravel Supporter. Tôi có thể giúp gì cho bạn?'

    # 2. Cảm ơn
    if any(x in message_lower for x in ['cảm ơn', 'cam on', 'thanks']):
        return 'Dạ không có gì ạ! Rất vui được hỗ trợ quý khách. 😊'

    # 3. Hỏi về xe
    if any(x in message_lower for x in ['xe ở đâu', 'vị trí xe', 'xe nào', 'tìm xe']):
        import re
        plate_match = re.search(r'(\d{1,2}[A-Z]-\d{3}\.\d{2})', message, re.IGNORECASE)
        if plate_match:
            plate = plate_match.group(0).upper()
            vehicles = [
                {'plate': '29A-111.11', 'driver': 'Nguyễn Văn Đức', 'location': 'Võ Chí Công'},
                {'plate': '29B-222.22', 'driver': 'Trần Văn Hoan', 'location': 'Bến xe Mỹ Đình'},
                {'plate': '30E-333.33', 'driver': 'Lê Thị Đào', 'location': 'Minh Khai'},
            ]
            for v in vehicles:
                if v['plate'] == plate:
                    return f"🚗 Xe {plate} do tài xế {v['driver']} lái, đang ở vị trí: {v['location']}"
            return f"❌ Không tìm thấy xe biển số {plate}"
        return 'Bạn vui lòng cho biết biển số xe, ví dụ: "Xe 29B-222.22 ở đâu?"'

    # 4. Hỏi về vi phạm / cảnh báo
    if any(x in message_lower for x in ['vi phạm', 'cảnh báo', 'lỗi', 'bị phạt']):
        return f'''📊 Thống kê vi phạm hôm nay:
- 📱 Dùng điện thoại: {warnings.get('phone', '') and 1 or 0} lần
- 😴 Ngáp ngủ: {warnings.get('yawn', '') and 1 or 0} lần
- ⚠️ Không dây an toàn: {warnings.get('seatbelt', '') and 1 or 0} lần
- 🚨 Va chạm: {warnings.get('collision', '') and 1 or 0} lần

Bạn muốn xem chi tiết xe nào?'''

    # 5. Hỏi về tài xế
    if any(x in message_lower for x in ['tài xế', 'tài xế nào', 'ai lái']):
        return '''👨‍✈️ Danh sách tài xế đang hoạt động:
1. Nguyễn Văn Đức - 29A-111.11
2. Trần Văn Hoan - 29B-222.22
3. Lê Thị Đào - 30E-333.33

Bạn cần thông tin tài xế nào?'''

    # 6. Yêu cầu hỗ trợ
    if any(x in message_lower for x in ['hỗ trợ', 'giúp', 'help', 'cần giúp']):
        return '''🆘 Tôi có thể giúp bạn:
- 📍 Theo dõi vị trí xe
- ⚠️ Xem cảnh báo vi phạm
- 👤 Thông tin tài xế
- 📊 Thống kê hành trình

Bạn cần gì?'''

    # 7. Hỏi về thời tiết / giao thông
    if any(x in message_lower for x in ['thời tiết', 'giao thông', 'đường xá']):
        return '''🌤️ Thời tiết Hà Nội:
- Nhiệt độ: 25°C
- Trời nắng đẹp
- Giao thông thuận lợi

Chúc bạn lái xe an toàn! 🚗'''

    # 8. Tạm biệt
    if any(x in message_lower for x in ['tạm biệt', 'bye', 'goodbye', 'kết thúc']):
        return 'Cảm ơn bạn đã sử dụng dịch vụ! Chúc bạn một ngày tốt lành! 🌟'

    # === DEFAULT RESPONSE ===
    return '''Cảm ơn bạn đã nhắn tin! 
Tôi đã nhận được yêu cầu và sẽ phản hồi sớm nhất.

Hoặc bạn có thể:
- 🎤 Nói: "Xem cảnh báo"
- 📍 Hỏi: "Xe 29B-222.22 ở đâu?"
- 📊 Hỏi: "Thống kê hôm nay"'''


def call_llm_api(message, vehicle_id=None):
    """
    Gọi API từ mô hình AI thực thụ (LLM)
    Hỗ trợ: OpenAI, Google Gemini, Groq (miễn phí)
    """
    try:
        GROQ_API_KEY = os.getenv('GROQ_API_KEY')

        if not GROQ_API_KEY:
            print("⚠️ Không tìm thấy GROQ_API_KEY trong .env file")
            return None

        client = Groq(api_key=GROQ_API_KEY)

        # === DATA THỰC TẾ TỪ HỆ THỐNG ===
        vehicles_data = [
            {'plate': '29A-111.11', 'driver': 'Nguyễn Văn Đức', 'location': 'Võ Chí Công', 'status': 'Đang chạy', 'speed': 45},
            {'plate': '29B-222.22', 'driver': 'Trần Văn Hoan', 'location': 'Bến xe Mỹ Đình', 'status': 'Đang dừng', 'speed': 0},
            {'plate': '30E-333.33', 'driver': 'Lê Thị Đào', 'location': 'Minh Khai', 'status': 'Đang chạy', 'speed': 30},
            {'plate': '29H-444.44', 'driver': 'Phạm Văn Dũng', 'location': 'Ngã tư Sở', 'status': 'Đang chạy', 'speed': 50},
            {'plate': '15B-555.55', 'driver': 'Hoàng Văn Việt', 'location': 'Cao tốc 5B', 'status': 'Đang chạy', 'speed': 40},
            {'plate': '30G-666.66', 'driver': 'Vũ Thị Hồng', 'location': 'Phủ Tây Hồ', 'status': 'Đang chạy', 'speed': 40},
            {'plate': '29LD-777.77', 'driver': 'Công ty Travel', 'location': 'Cầu Chương Dương', 'status': 'Đang chạy', 'speed': 60},
        ]

        vehicles_info = "\n".join([
            f"- {v['plate']}: Tài xế {v['driver']}, vị trí {v['location']}, trạng thái {v['status']}, tốc độ {v['speed']} km/h"
            for v in vehicles_data
        ])

        context = f"""
Bạn là trợ lý ảo AI của Vietravel, hỗ trợ giám sát giao thông và an toàn lái xe.

=== THÔNG TIN XE THỰC TẾ (DATA TỪ HỆ THỐNG) ===
Danh sách xe đang giám sát:
{vehicles_info}

=== CẢNH BÁO AI ĐANG HOẠT ĐỘNG ===
- Nhắm mắt: {warnings.get('eye', 'Không có') or 'Không có'}
- Ngáp ngủ: {warnings.get('yawn', 'Không có') or 'Không có'}
- Mất tập trung: {warnings.get('head', 'Không có') or 'Không có'}
- Dùng điện thoại: {warnings.get('phone', 'Không có') or 'Không có'}
- Không dây an toàn: {warnings.get('seatbelt', 'Không có') or 'Không có'}
- Không cầm vô lăng: {warnings.get('hand', 'Không có') or 'Không có'}
- Va chạm: {warnings.get('collision', 'Không có') or 'Không có'}
- Lệch làn: {warnings.get('lane', 'Không có') or 'Không có'}

=== HƯỚNG DẪN TRẢ LỜI ===
- Khi được hỏi về xe (ví dụ: "xe 29A-111.11 ở đâu"), TRA CỨU trong danh sách xe trên
- Trả lời bằng tiếng Việt, thân thiện, ngắn gọn
- Sử dụng emoji phù hợp
- Ưu tiên an toàn giao thông
- Nếu không tìm thấy biển số, nói "Không tìm thấy xe trong hệ thống"

=== USER MESSAGE ===
{message}

=== TRẢ LỜI ===
"""

        chat_completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Bạn là trợ lý giao thông Vietravel. Trả lời bằng tiếng Việt, thân thiện. LUÔN TRA CỨU DANH SÁCH XE KHI ĐƯỢC HỎI VỀ VỊ TRÍ."
                },
                {
                    "role": "user",
                    "content": context
                }
            ],
            temperature=0.7,
            max_tokens=500,
            top_p=1.0,
            stream=False,
            stop=None
        )

        response = chat_completion.choices[0].message.content
        print(f"🤖 [GROQ AI] Response: {response[:100]}...")
        return response

    except ImportError:
        print("⚠️ Chưa cài groq. Chạy: pip install groq")
        return None
    except Exception as e:
        print(f"❌ Lỗi Groq API: {e}")
        return None


def process_ai_chat_message(message, vehicle_id=None):
    """
    Xử lý tin nhắn chatbot với AI thực thụ
    Fallback về rule-based nếu API thất bại
    """
    # 1. Thử gọi LLM API
    llm_response = call_llm_api(message, vehicle_id)

    if llm_response:
        # Thành công với AI
        return llm_response

    # 2. Fallback về rule-based
    print("⚠️ Fallback về rule-based AI")
    return generate_bot_response(message, vehicle_id)
