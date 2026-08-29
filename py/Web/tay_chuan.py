from flask import Flask, render_template, Response, jsonify, request
import cv2
import numpy as np
import HandTrackingModule as htm
import os
import base64
import threading
import time
import math
import subprocess
import speech_recognition as sr
import queue

app = Flask(__name__)

# Thông số video
wCam, hCam = 640, 480  # Giảm kích thước xuống để tăng hiệu suất

# Cấu hình camera
cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)

# Biến điều khiển
current_page = 0
total_pages = 3  # Số lượng trang HTML
gestureThreshold = int(hCam * 0.90)
buttonPresses = False
buttonCounter = 0
buttonDelay = 30
clicked_button = None

# Biến cho lịch sử thao tác
action_history = []  # Lưu lịch sử các thao tác
current_action_index = -1  # Vị trí hiện tại trong lịch sử

# Biến cho vẽ
annotations = [[]]
annotationsNumber = 0
annotationsStart = False

# Biến cho điều khiển âm thanh và ánh sáng (macOS compatible)
volPer = 0
volBar = 400
brightBar = 400
brightnessPer = 0

def set_macos_volume(level):
    """Set system volume on macOS (0-100)"""
    try:
        subprocess.run(['osascript', '-e', f'set volume output volume {level}'], check=False)
    except Exception as e:
        print(f"Error setting volume: {e}")

def get_macos_volume():
    """Get current system volume on macOS (0-100)"""
    try:
        result = subprocess.run(['osascript', '-e', 'output volume of (get volume settings)'], 
                              capture_output=True, text=True, check=False)
        return int(result.stdout.strip())
    except:
        return 50

def set_macos_brightness(level):
    """Set screen brightness on macOS (0-100) - requires third-party tool or works on some Macs"""
    try:
        # Try using brightness command if available (brew install brightness)
        subprocess.run(['brightness', '-l', str(level / 100.0)], check=False)
    except Exception:
        # Fallback: try osascript (limited support)
        try:
            subprocess.run(['osascript', '-e', f'tell application "System Events" to set display brightness to {level / 100.0}'], check=False)
        except Exception as e:
            print(f"Error setting brightness: {e}")

# Định nghĩa vị trí các button
buttons = [
    {"id": "button1", "x1": 10, "y1": 0, "x2": 200, "y2": 50, "text": "Phone"},
    {"id": "button2", "x1": 10, "y1": 50, "x2": 200, "y2": 100, "text": "Google map"},
    {"id": "button3", "x1": 10, "y1": 100, "x2": 200, "y2": 150, "text": "Youtube"}
]

# Khởi tạo đối tượng hand detector
detector = htm.HandDetector(detectionCon=0.7, maxHands=1)

# Thêm biến cho nhận diện giọng nói
voice_queue = queue.Queue()
recognizer = sr.Recognizer()
is_listening = True

# Thêm biến để kiểm soát việc thoát
is_shutting_down = False

def get_frame():
    success, frame = cap.read()
    if not success:
        return None
    return cv2.flip(frame, 1)

def draw_buttons(img):
    """Hàm vẽ các button lên frame"""
    for button in buttons:
        # Vẽ khung button
        cv2.rectangle(img, (button["x1"], button["y1"]), (button["x2"], button["y2"]), (0, 255, 0), 2)
        # Vẽ text button
        text_size = cv2.getTextSize(button["text"], cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        text_x = button["x1"] + (button["x2"] - button["x1"] - text_size[0]) // 2
        text_y = button["y1"] + (button["y2"] - button["y1"] + text_size[1]) // 2
        cv2.putText(img, button["text"], (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)


prev_middle_pos = None
prev_index_pos = None
rotation_threshold = 30  # Ngưỡng để xác định quay

#xoay ngón tay
def calculate_rotation(prev_pos, current_pos, center):
    """Tính góc quay giữa hai vị trí"""
    if prev_pos is None:
        return 0
    
    # Tính vector từ tâm đến vị trí trước và hiện tại
    prev_vector = (prev_pos[0] - center[0], prev_pos[1] - center[1])
    current_vector = (current_pos[0] - center[0], current_pos[1] - center[1])
    
    # Tính góc giữa hai vector
    dot_product = prev_vector[0] * current_vector[0] + prev_vector[1] * current_vector[1]
    prev_magnitude = math.sqrt(prev_vector[0]**2 + prev_vector[1]**2)
    current_magnitude = math.sqrt(current_vector[0]**2 + current_vector[1]**2)
    
    # Tránh chia cho 0
    if prev_magnitude == 0 or current_magnitude == 0:
        return 0
        
    cos_angle = dot_product / (prev_magnitude * current_magnitude)
    cos_angle = max(-1, min(1, cos_angle))  # Giới hạn trong khoảng [-1, 1]
    angle = math.degrees(math.acos(cos_angle))
    
    # Xác định hướng quay (theo chiều kim đồng hồ hay ngược lại)
    cross_product = prev_vector[0] * current_vector[1] - prev_vector[1] * current_vector[0]
    if cross_product < 0:
        angle = -angle
        
    return angle
        

def listen_for_commands():
    """Hàm lắng nghe lệnh thoại trong một thread riêng"""
    global is_listening
    while is_listening:
        try:
            with sr.Microphone() as source:
                print("Đang lắng nghe...")
                # Điều chỉnh độ nhạy của microphone
                recognizer.dynamic_energy_threshold = True
                recognizer.energy_threshold = 300  # Giảm ngưỡng năng lượng để dễ nhận diện hơn
                recognizer.pause_threshold = 0.8  # Giảm thời gian chờ giữa các từ
                recognizer.adjust_for_ambient_noise(source, duration=1)
                
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    print("Đã ghi âm xong, đang xử lý...")
                    
                    try:
                        text = recognizer.recognize_google(audio, language="vi-VN")
                        print(f"Đã nhận lệnh: {text}")
                        voice_queue.put(text.lower())
                    except sr.UnknownValueError:
                        print("Không nhận diện được giọng nói. Vui lòng nói rõ ràng hơn.")
                    except sr.RequestError as e:
                        print(f"Lỗi kết nối đến dịch vụ nhận diện giọng nói: {e}")
                        print("Vui lòng kiểm tra kết nối internet của bạn.")
                except sr.WaitTimeoutError:
                    print("Hết thời gian chờ. Vui lòng thử lại.")
                except Exception as e:
                    print(f"Lỗi khi ghi âm: {e}")
                    print("Vui lòng kiểm tra microphone của bạn.")
        except Exception as e:
            print(f"Lỗi khi lắng nghe: {e}")
            print("Vui lòng kiểm tra lại thiết bị âm thanh của bạn.")
            time.sleep(1)  # Đợi 1 giây trước khi thử lại

def process_voice_command(command):
    """Xử lý lệnh thoại"""
    global volPer, brightnessPer
    
    # Lệnh điều khiển âm thanh
    if "tăng âm thanh" in command or "tăng âm lượng" in command:
        volPer = min(100, volPer + 10)
        set_macos_volume(volPer)
        return f"Tăng âm thanh lên {volPer}%"
    elif "giảm âm thanh" in command or "giảm âm lượng" in command:
        volPer = max(0, volPer - 10)
        set_macos_volume(volPer)
        return f"Giảm âm thanh xuống {volPer}%"
    elif "âm thanh" in command and "mức" in command:
        try:
            level = int(''.join(filter(str.isdigit, command)))
            volPer = max(0, min(100, level))
            set_macos_volume(volPer)
            return f"Đặt âm thanh ở mức {volPer}%"
        except:
            return "Không hiểu mức âm thanh"
            
    # Lệnh điều khiển ánh sáng
    elif "tăng độ sáng" in command or "tăng ánh sáng" in command:
        brightnessPer = min(100, brightnessPer + 10)
        set_macos_brightness(brightnessPer)
        return f"Tăng độ sáng lên {brightnessPer}%"
    elif "giảm độ sáng" in command or "giảm ánh sáng" in command:
        brightnessPer = max(0, brightnessPer - 10)
        set_macos_brightness(brightnessPer)
        return f"Giảm độ sáng xuống {brightnessPer}%"
    elif "độ sáng" in command and "mức" in command:
        try:
            level = int(''.join(filter(str.isdigit, command)))
            brightnessPer = max(0, min(100, level))
            set_macos_brightness(brightnessPer)
            return f"Đặt độ sáng ở mức {brightnessPer}%"
        except:
            return "Không hiểu mức độ sáng"
    
    return None

def generate_camera_frames():
    global volBar, volPer, brightBar, brightnessPer, is_shutting_down, cap
    pTime = 0
    
    # Bắt đầu thread lắng nghe giọng nói
    voice_thread = threading.Thread(target=listen_for_commands)
    voice_thread.daemon = True
    voice_thread.start()
    
    while not is_shutting_down and cap.isOpened():
        try:
            img = get_frame()
            if img is None:
                 # Nếu không lấy được frame, đợi một chút và thử lại hoặc thoát vòng lặp nếu đang tắt
                 if is_shutting_down:
                     break
                 time.sleep(0.01)
                 continue
                
            height, width, _ = img.shape

            # Xử lý lệnh thoại từ queue
            try:
                while not voice_queue.empty():
                    command = voice_queue.get_nowait()
                    response = process_voice_command(command)
                    if response:
                        # Cập nhật âm thanh
                        if "âm thanh" in response:
                            volBar = np.interp(volPer, [0, 100], [400, 150])
                            set_macos_volume(int(volPer))
                        # Cập nhật độ sáng
                        elif "độ sáng" in response:
                            brightBar = np.interp(brightnessPer, [0, 100], [400, 150])
                            set_macos_brightness(int(brightnessPer))

                        # Hiển thị thông báo
                        cv2.putText(img, response, (50, 100),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            except queue.Empty:
                pass
            
            # Phát hiện tay và vẽ đường kẻ
            try:
                hands, img = detector.findHands(img)
                cv2.line(img, (0, gestureThreshold), (width, gestureThreshold), (0, 255, 0), 5)

                # Vẽ thông tin cử chỉ
                if hands:
                    for hand in hands:
                        fingers = detector.fingersUp(hand)
                        cx, cy = hand['center']
                        lmList = hand['lmList']
                        hand_type = hand['label']  # "Left" hoặc "Right"
                        
                        # Hiển thị trạng thái các ngón tay
                        finger_status = "Ngon tay: "
                        if fingers[0]: finger_status += "Cai "
                        if fingers[1]: finger_status += "Tro "
                        if fingers[2]: finger_status += "Giữa "
                        if fingers[3]: finger_status += "Nhẫn "
                        if fingers[4]: finger_status += "Út "

                        # Xử lý theo loại tay
                        if hand_type == "Left":  # Tay trái - chỉ điều khiển âm thanh và ánh sáng
                            if len(lmList) != 0:
                                try:
                                    # Điều khiển âm thanh bằng ngón trỏ
                                    index_finger_pos = (lmList[8][1], lmList[8][2])
                                    index_center = (lmList[6][1], lmList[6][2])
                                    
                                    # Vẽ đường tròn và điểm cho ngón trỏ
                                    cv2.circle(img, index_center, 30, (0, 255, 0), 2)
                                    cv2.circle(img, index_finger_pos, 5, (0, 0, 255), -1)
                                    
                                    if prev_index_pos is not None:
                                        cv2.line(img, prev_index_pos, index_finger_pos, (255, 0, 0), 2)
                                        rotation = calculate_rotation(prev_index_pos, index_finger_pos, index_center)
                                        
                                        if abs(rotation) > 5:
                                            volume_change = rotation * 0.5
                                            volPer = max(0, min(100, volPer + volume_change))

                                            if volume_change > 0:
                                                cv2.putText(img, f"Tang am thanh: {int(volume_change)}%", (300, 100),
                                                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                                            else:
                                                cv2.putText(img, f"Giam am thanh: {int(abs(volume_change))}%", (300, 100),
                                                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                                            volBar = np.interp(volPer, [0, 100], [400, 150])
                                            set_macos_volume(int(volPer))

                                    prev_index_pos = index_finger_pos

                                    # Điều khiển ánh sáng bằng ngón giữa
                                    middle_finger_pos = (lmList[12][1], lmList[12][2])
                                    middle_center = (lmList[10][1], lmList[10][2])

                                    # Vẽ đường tròn và điểm cho ngón giữa
                                    cv2.circle(img, middle_center, 30, (0, 165, 255), 2)
                                    cv2.circle(img, middle_finger_pos, 5, (255, 192, 203), -1)

                                    if prev_middle_pos is not None:
                                        cv2.line(img, prev_middle_pos, middle_finger_pos, (0, 165, 255), 2)
                                        rotation = calculate_rotation(prev_middle_pos, middle_finger_pos, middle_center)

                                        if abs(rotation) > 5:
                                            brightness_change = rotation * 0.5
                                            brightnessPer = max(0, min(100, brightnessPer + brightness_change))

                                            if brightness_change > 0:
                                                cv2.putText(img, f"Tang do sang: {int(brightness_change)}%", (300, 150),
                                                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
                                            else:
                                                cv2.putText(img, f"Giam do sang: {int(abs(brightness_change))}%", (300, 150),
                                                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)

                                            brightBar = np.interp(brightnessPer, [0, 100], [400, 150])
                                            set_macos_brightness(int(brightnessPer))
                                    
                                    prev_middle_pos = middle_finger_pos

                                except Exception as e:
                                    print(f"Error in volume/brightness control: {e}")
                                    prev_index_pos = None
                                    prev_middle_pos = None

                        elif hand_type == "Right" and cy <= gestureThreshold:  # Tay phải - chỉ xử lý các thao tác với nút và điều hướng
                            # Quay lại thao tác trước đó (ngón cái + ngón trỏ)
                            if fingers == [1, 0, 0, 0, 0]:
                                if current_action_index > 0:
                                    current_action_index -= 1
                                    # Khôi phục trạng thái từ lịch sử
                                    if action_history[current_action_index]:
                                        clicked_button = action_history[current_action_index]
                                    buttonPresses = True
                            
                            # Đi đến thao tác tiếp theo (ngón trỏ + ngón út)
                            if fingers == [0, 0, 0, 0, 1]:
                                if current_action_index < len(action_history) - 1:
                                    current_action_index += 1
                                    # Khôi phục trạng thái từ lịch sử
                                    if action_history[current_action_index]:
                                        clicked_button = action_history[current_action_index]
                                    buttonPresses = True

                            # Click button bằng ngón trỏ và ngón giữa
                            if fingers == [0, 1, 1, 0, 0]:
                                index_finger = lmList[8]
                                for button in buttons:
                                    if (button["x1"] <= index_finger[1] <= button["x2"] and 
                                        button["y1"] <= index_finger[2] <= button["y2"]):
                                        clicked_button = button["id"]
                                        # Thêm vào lịch sử thao tác
                                        action_history = action_history[:current_action_index + 1]
                                        action_history.append(clicked_button)
                                        current_action_index = len(action_history) - 1
                                        buttonPresses = True
                                        break

                            # Mở Button 1 bằng ngón giữa
                            if fingers == [0, 1, 0, 0, 0]:
                                clicked_button = "button1"
                                action_history = action_history[:current_action_index + 1]
                                action_history.append(clicked_button)
                                current_action_index = len(action_history) - 1
                                buttonPresses = True

                            # Mở Button 2 bằng ngón nhẫn
                            if fingers == [0, 0, 1, 0, 0]:
                                clicked_button = "button2"
                                action_history = action_history[:current_action_index + 1]
                                action_history.append(clicked_button)
                                current_action_index = len(action_history) - 1
                                buttonPresses = True

                            # Mở Button 3 bằng ngón nhẫn
                            if fingers == [0, 0, 0, 1, 0]:
                                clicked_button = "button3"
                                action_history = action_history[:current_action_index + 1]
                                action_history.append(clicked_button)
                                current_action_index = len(action_history) - 1
                                buttonPresses = True

                            # Đóng modal khi giơ 4 ngón trỏ, giữa và nhẫn
                            if fingers == [0, 1, 1, 1, 1]:
                                clicked_button = None
                                buttonPresses = True
                                # Thêm vào lịch sử thao tác
                                action_history = action_history[:current_action_index + 1]
                                action_history.append(None)
                                current_action_index = len(action_history) - 1

            except Exception as e:
                print(f"Error in hand detection: {e}")

            # Vẽ thanh âm thanh
            cv2.rectangle(img, (10, 160), (50, 400), (255, 255, 0), 3)
            cv2.rectangle(img, (10, int(volBar)), (50, 400), (255, 255, 0), cv2.FILLED)
            cv2.putText(img, f'Volume {int(volPer)} %', (150, 400), 
                        cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 0), 2)

            # Vẽ thanh ánh sáng
            cv2.rectangle(img, (55, 160), (95, 400), (0, 165, 255), 3)
            cv2.rectangle(img, (55, int(brightBar)), (95, 400), (0, 165, 255), cv2.FILLED)
            cv2.putText(img, f'Light {int(brightnessPer)} %', (380, 400),
                        cv2.FONT_HERSHEY_COMPLEX, 1, (0, 165, 255), 2)

            
            # FPS
            cTime = time.time()
            fps = 1 / (cTime - pTime + 1e-5)
            pTime = cTime
            cv2.putText(img, f'FPS {int(fps)}', (500, 50), 
                        cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
            
            #vẽ button
            draw_buttons(img)

            ret, buffer = cv2.imencode('.jpg', img)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            if not is_shutting_down:  # Chỉ in lỗi nếu không phải đang thoát
                print(f"Error in generate_camera_frames: {e}")
            # Thoát vòng lặp nếu đang tắt để không cố gắng xử lý frame lỗi
            if is_shutting_down:
                break
            continue
            
    # Đảm bảo camera được giải phóng khi vòng lặp kết thúc
    if cap and cap.isOpened():
        cap.release()

def generate_interactive_frames():
    global current_page, buttonPresses, buttonCounter, clicked_button, action_history, current_action_index, is_shutting_down, cap
    
    while not is_shutting_down and cap.isOpened():
        try:
            img = get_frame()
            if img is None:
                 # Nếu không lấy được frame, đợi một chút và thử lại hoặc thoát vòng lặp nếu đang tắt
                 if is_shutting_down:
                     break
                 time.sleep(0.01)
                 continue

            height, width, _ = img.shape

            # Phát hiện tay
            hands, img = detector.findHands(img)
            cv2.line(img, (0, gestureThreshold), (width, gestureThreshold), (0, 255, 0), 5)

            if hands and buttonPresses is False:
                for hand in hands:
                    fingers = detector.fingersUp(hand)
                    cx, cy = hand['center']
                    lmList = hand['lmList']
                    hand_type = hand['label']  # "Left" hoặc "Right"

                    if cy <= gestureThreshold:
                        if hand_type == "Right":  # Chỉ xử lý các thao tác với button và ứng dụng bằng tay phải
                            # Quay lại thao tác trước đó (ngón cái + ngón trỏ)
                            if fingers == [1, 0, 0, 0, 0]:
                                if current_action_index > 0:
                                    current_action_index -= 1
                                    # Khôi phục trạng thái từ lịch sử
                                    if action_history[current_action_index]:
                                        clicked_button = action_history[current_action_index]
                                    buttonPresses = True
                            
                            # Đi đến thao tác tiếp theo (ngón trỏ + ngón út)
                            if fingers == [0, 0, 0, 0, 1]:
                                if current_action_index < len(action_history) - 1:
                                    current_action_index += 1
                                    # Khôi phục trạng thái từ lịch sử
                                    if action_history[current_action_index]:
                                        clicked_button = action_history[current_action_index]
                                    buttonPresses = True

                            # Click button bằng ngón trỏ và ngón giữa
                            if fingers == [0, 1, 1, 0, 0]:
                                index_finger = lmList[8]
                                for button in buttons:
                                    if (button["x1"] <= index_finger[1] <= button["x2"] and 
                                        button["y1"] <= index_finger[2] <= button["y2"]):
                                        clicked_button = button["id"]
                                        # Thêm vào lịch sử thao tác
                                        action_history = action_history[:current_action_index + 1]
                                        action_history.append(clicked_button)
                                        current_action_index = len(action_history) - 1
                                        buttonPresses = True
                                        break

                            # Mở Button 1 bằng ngón giữa
                            if fingers == [0, 1, 0, 0, 0]:
                                clicked_button = "button1"
                                action_history = action_history[:current_action_index + 1]
                                action_history.append(clicked_button)
                                current_action_index = len(action_history) - 1
                                buttonPresses = True

                            # Mở Button 2 bằng ngón nhẫn
                            if fingers == [0, 0, 1, 0, 0]:
                                clicked_button = "button2"
                                action_history = action_history[:current_action_index + 1]
                                action_history.append(clicked_button)
                                current_action_index = len(action_history) - 1
                                buttonPresses = True

                            # Mở Button 3 bằng ngón nhẫn
                            if fingers == [0, 0, 0, 1, 0]:
                                clicked_button = "button3"
                                action_history = action_history[:current_action_index + 1]
                                action_history.append(clicked_button)
                                current_action_index = len(action_history) - 1
                                buttonPresses = True

                            # Đóng modal khi giơ 4 ngón trỏ, giữa và nhẫn
                            if fingers == [0, 1, 1, 1, 1]:
                                clicked_button = None
                                buttonPresses = True
                                # Thêm vào lịch sử thao tác
                                action_history = action_history[:current_action_index + 1]
                                action_history.append(None)
                                current_action_index = len(action_history) - 1

            if buttonPresses:
                buttonCounter += 1
                if buttonCounter > buttonDelay:
                    buttonCounter = 0
                    buttonPresses = False

            # Vẽ các button
            draw_buttons(img)

            ret, buffer = cv2.imencode('.jpg', img)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            if not is_shutting_down: # Chỉ in lỗi nếu không phải đang thoát
                print(f"Error in generate_interactive_frames: {e}")
             # Thoát vòng lặp nếu đang tắt để không cố gắng xử lý frame lỗi
            if is_shutting_down:
                break
            continue
            
     # Đảm bảo camera được giải phóng khi vòng lặp kết thúc
    if cap and cap.isOpened():
        cap.release()

@app.route('/')
def index():
    return render_template('trang_chu.html')


@app.route('/hands')
def settings_hands():
    return render_template('tay_o.html')


@app.route('/lai_xe')
def lai_xe():
    return render_template('lai_xe.html')


@app.route('/camera_feed')
def camera_feed():
    return Response(generate_camera_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/interactive_feed')
def interactive_feed():
    return Response(generate_interactive_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_current_page')
def get_current_page():
    return {'page': current_page, 'clicked_button': clicked_button}

@app.route('/reset_clicked_button', methods=['POST'])
def reset_clicked_button():
    """Đặt lại trạng thái nút đã click"""
    global clicked_button
    clicked_button = None
    return jsonify({'status': 'success'})

@app.route('/exit', methods=['POST'])
def exit_program():
    """Xử lý thoát chương trình"""
    global is_shutting_down
    
    try:
        # Đánh dấu đang trong quá trình thoát
        is_shutting_down = True
        
        # Dừng tất cả các luồng video (nếu có trong hands.py)
        # Dừng ghi video nếu đang ghi (nếu có trong hands.py)
        # Dừng pygame mixer (nếu có trong hands.py)
        
        # Đóng tất cả các camera
        global cap
        if cap and cap.isOpened():
            cap.release()
        
        # Tạo một thread mới để thoát server sau 1 giây
        def shutdown_server():
            time.sleep(1)  # Đợi 1 giây để đảm bảo response được gửi về client
            os._exit(0)
        
        threading.Thread(target=shutdown_server).start()
        
        return jsonify({"status": "success", "message": "Đang thoát chương trình..."})
    except Exception as e:
        print(f"Error in exit_program: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

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
        # Dừng thread lắng nghe khi thoát chương trình
        is_listening = False
