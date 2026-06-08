from ultralytics import YOLO

# Tạo model từ pre-trained YOLOv8n
model = YOLO("yolov8n.pt")

# Huấn luyện mô hình
model.train(
    data="path/to/your/phone_using.v3i.yolov8/data.yaml",  # Đường dẫn đến file data.yaml - VUI LÒNG THAY ĐỔI ĐƯỜNG DẪN NÀY
    epochs=50,
    imgsz=640,
    batch=8  # Điều chỉnh nếu máy yếu
)

# Lưu mô hình đã huấn luyện
model.export(format="torch")  # Xuất mô hình sang định dạng .pt