# Plan 1: Restructure bài báo

## Mục tiêu
Tập trung vào phương pháp mô hình AI, lược bỏ phần hệ thống web khỏi methodology, đưa xuống results.

---

## Cấu trúc mới

### 1. Giới thiệu *(giữ nguyên)*

### 2. Các nghiên cứu liên quan *(giữ nguyên)*

### 3. Phương pháp nghiên cứu *(chỉ AI/computer vision)*

| Mục | Nội dung |
|-----|----------|
| **3.1** | **Phát hiện nhắm mắt và buồn ngủ** — EAR formula (Eq.~1), dlib 68 landmarks, threshold 0.30/2s |
| **3.2** | **Phát hiện ngáp** — MAR formula (Eq.~2), top/bottom lip landmarks, threshold 25px/15 frames |
| **3.3** | **Ước lượng tư thế đầu** — solvePnP (Eq.~3), 3D face model, 6 landmarks, Euler angles, yaw>40°/pitch>35° |
| **3.4** | **Phát hiện sử dụng điện thoại** — YOLOv8n fine-tune trên COCO+8.500 ảnh cabin, freezing layers, backbone CSPDarknet, mAP@50=0.975 |
| **3.5** | **Phát hiện dây an toàn** — YOLOv8 custom, 1.200 ảnh cabin, transfer learning, mAP@50=0.753 |
| **3.6** | **Theo dõi tay lái** — MediaPipe Hands (21 landmarks) + Pose (33 landmarks), FistScore (Eq.~4), threshold ≥3 |

**Thay đổi:**
- ❌ Xoá 3.1 Kiến trúc tổng thể (3-tier, Flask, WebSocket, MQTT, lazy loading algorithm)
- ❌ Xoá 3.3 Pipeline xử lý AI → chuyển xuống 4.2
- ❌ Xoá 3.4 Tổng hợp cảnh báo → chuyển xuống 4.2
- ❌ Xoá 3.5 Phân quyền và bảo mật (RBAC)
- ❌ Xoá 3.6 Tích hợp chatbot AI
- ⬆️ Nâng cấp 3.2.1–3.2.6 từ `\subsubsection` → `\subsection`
- 📊 Chuyển Bảng YOLO training + Hình seatbelt detection sang 4.1

### 4. Kết quả và thảo luận *(gộp results + discussion cũ)*

| Mục | Nội dung | Nguồn |
|-----|----------|-------|
| **4.1** | **Hiệu suất mô hình** — mAP@50, precision, recall, confusion matrix, training curves, Bảng YOLO training, Hình training curves + confusion matrix + seatbelt detection | Từ 4.2 cũ + Bảng/Hình từ 3.2.4–3.2.5 |
| **4.2** | **Xây dựng hệ thống web thông báo chỉ huy, và ngược lại** — kiến trúc 3 tầng (tóm lược), pipeline, alert multi-channel (WebSocket/MQTT/pygame), two-way communication (web→system: bật/tắt module, gửi lệnh; system→web: cảnh báo, stream), dashboard real-time | Từ 3.1 + 3.3 + 3.4 cũ (rút gọn) |
| **4.3** | **Đánh giá độ ổn định hệ thống** — Bảng inference time, Bảng CPU vs GPU, timing instrumentation, FPS stability, thảo luận hạn chế | Từ 4.1 + 4.2 + Discussion cũ |

**Thay đổi:**
- ⬆️ Gộp Discussion (mục 5 cũ) vào cuối 4.3
- 📊 Bảng inference + Bảng CPU/GPU giữ nguyên trong 4.3
- 📊 Bảng threshold + Bảng priority giữ nguyên trong 4.2

### 5. Kết luận *(rút gọn)*

| Mục | Nội dung |
|-----|----------|
| **5.1** | **Kết luận** — tóm tắt đóng góp, kết quả chính |
| **5.2** | **Hướng phát triển** — Edge AI, YOLOv10/v11, multi-threading, mở rộng dữ liệu |
| | **Lời cảm ơn** *(giữ nguyên)* |
| | **Tài liệu tham khảo** *(giữ nguyên)* |

---

## Tác vụ thực hiện

1. [x] Tạo plan1.md
2. [ ] Sửa Section 3 title + restructure
3. [ ] Chuyển Bảng/Hình từ 3 → 4.1
4. [ ] Restructure Section 4 → 4.1/4.2/4.3
5. [ ] Merge Discussion → cuối 4.3
6. [ ] Rút gọn Section 5 (Kết luận)
7. [ ] Compile kiểm tra lỗi
