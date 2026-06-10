# Setup AI API

## Mặc định hiện tại

Project hiện có lớp adapter cho chatbot trong `backend/app/chatbot/` và runtime AI trong `backend/app/ai/runtime.py`.

Nếu chỉ chạy hệ thống nội bộ, bạn có thể để rule-based response hoạt động mà không cần LLM API.

## Khuyến nghị

- **Groq**: phù hợp nhất nếu muốn chatbot LLM nhanh và dễ cấu hình.
- **OpenAI**: dùng nếu bạn muốn model quen thuộc và chấp nhận phí.
- **Gemini**: dùng như một lựa chọn thay thế.

## Biến môi trường

Tối thiểu nên có:

```dotenv
AI_ENABLED=true
GROQ_API_KEY=your_key_here
```

Nếu tự chỉnh runtime để dùng provider khác thì bổ sung thêm key tương ứng.

## Cách test

1. Set API key trong `.env` hoặc `backend/.env`.
2. Chạy backend.
3. Gửi request tới `POST /api/send_chat_message`.
4. Nếu muốn test luật giao thông, gọi `POST /api/groq_law_chat`.

## Lưu ý

- Không hardcode key trực tiếp trong source.
- Nếu key lỗi hoặc hết quota, chatbot nên fallback về response nội bộ.