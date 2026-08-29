from ultralytics import YOLO  # Import YOLOv8

# 🟢 Tạo model YOLOv8 từ pre-trained YOLOv8n
model = YOLO("yolov8n.pt")  # Dùng mô hình nền YOLOv8n

# 🟢 Huấn luyện mô hình nhận diện dây đai an toàn
model.train(
    data="path/to/your/seat_belt_detection.yolov8/data.yaml",  # Đường dẫn đến tập dữ liệu - VUI LÒNG THAY ĐỔI ĐƯỜNG DẪN NÀY
    epochs=50,   # Số vòng lặp huấn luyện
    imgsz=640,   # Kích thước ảnh đầu vào
    batch=8,     # Batch size (điều chỉnh nếu cần)
    save=True,   # Tự động lưu mô hình tốt nhất
    project="runs/train",  # Thư mục lưu kết quả
    name="seatbelt_model"  # Tên thư mục lưu kết quả
)

# 🟢 Xuất mô hình sau khi huấn luyện
model.export(format="torch", name="yolov8n_seatbelt.pt")

print("✅ Huấn luyện hoàn tất! Mô hình đã được lưu dưới dạng 'yolov8n_seatbelt.pt'.")