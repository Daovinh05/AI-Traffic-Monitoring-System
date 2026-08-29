from flask import Flask, render_template, Response
import cv2
from ultralytics import YOLO
import os

app = Flask(__name__)

# Tải mô hình YOLOv8
# LƯU Ý: Để có kết quả tốt nhất, hãy thay thế 'best.pt' 
# bằng một mô hình đã được huấn luyện chuyên để nhận diện biển số xe.
model_path = "py/weights/yolov8n.pt"
try:
    model = YOLO(model_path)
except Exception as e:
    print(f"Lỗi khi tải mô hình: {e}")
    # Sử dụng một mô hình mặc định nếu có lỗi
    model = YOLO('yolov8n.pt')


def generate_frames():
    """
    Hàm này đọc video, xử lý từng khung hình để nhận diện biển số xe
    và trả về dưới dạng một luồng MJPEG.
    """
    # Đường dẫn đến video đầu vào. Thay đổi nếu bạn muốn sử dụng video khác hoặc webcam (0).
    video_path = "py/video_input/ha_noi.mp4"
    if not os.path.exists(video_path):
        print(f"Lỗi: Không tìm thấy tệp video tại '{video_path}'")
        return

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Lỗi: Không thể mở tệp video.")
        return

    while True:
        success, frame = cap.read()
        if not success:
            # Quay lại đầu video nếu kết thúc
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        # Thực hiện nhận diện đối tượng trên khung hình
        results = model(frame)

        # Vẽ các bounding box và nhãn lên khung hình
        annotated_frame = results[0].plot()

        # Mã hóa khung hình thành JPEG
        ret, buffer = cv2.imencode('.jpg', annotated_frame)
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()

        # Trả về khung hình dưới dạng http multipart response
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    """Trang chủ, hiển thị video nhận diện."""
    return render_template('bien_so.html')

@app.route('/video_feed')
def video_feed():
    """Đường dẫn cung cấp luồng video."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
if __name__ == '__main__':
    import webbrowser
    from threading import Timer
    
    # Cấu hình cổng - có thể thay đổi nếu cổng bị chiếm
    PORT = 5001  # Đổi sang cổng 5001 (hoặc 8080, 3000, 8000...)
    
    browser_opened = False
    
    def open_browser():
        global browser_opened
        if not browser_opened:
            webbrowser.open(f'http://127.0.0.1:{PORT}/')
            browser_opened = True
    
    # Đợi 1.5 giây để Flask khởi động xong rồi mới mở trình duyệt
    Timer(1.5, open_browser).start()
    
    try:
        # Chạy ứng dụng Flask với use_reloader=False để tránh mở nhiều trình duyệt
        print(f"Starting server on port {PORT}...")
        app.run(debug=True, host='0.0.0.0', port=PORT, use_reloader=False)
    finally:
        pass
