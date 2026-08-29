# AI Đã Sẵn Sàng

## Điều kiện để AI runtime chạy đầy đủ

AI runtime của backend chỉ sẵn sàng khi có đủ:

- Python dependencies đã cài.
- Database MySQL chạy được.
- File model trong `backend/assets/weights/`.
- File video trong `backend/assets/videos/`.
- File âm thanh trong `backend/assets/sounds/`.

Các file quan trọng thường gặp:

- `backend/assets/weights/yolov8n.pt`
- `backend/assets/weights/day_an_toan.pt`
- `backend/assets/weights/bien_bao.pt`
- `backend/assets/weights/lech_lan.pt`
- `backend/assets/weights/vat_can.pt`
- `backend/assets/shape_predictor_68_face_landmarks.dat`

## Cách bật

Set biến môi trường:

```dotenv
AI_ENABLED=true
```

Rồi chạy backend:

```bash
source .venv/bin/activate
python -m backend.app.main
```

## Cách kiểm tra

- Mở `GET /api/ai-status` để xem trạng thái runtime.
- Nếu asset thiếu, backend vẫn có thể lên API nhưng AI worker sẽ không ready.

## Lưu ý thực tế

- Nếu máy không có audio device, dùng `SDL_AUDIODRIVER=dummy`.
- Nếu không muốn bật AI khi dev, đặt `AI_ENABLED=false`.