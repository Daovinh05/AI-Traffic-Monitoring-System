import cv2
import mediapipe as mp

class HandDetector:
    def __init__(self, mode=False, maxHands=2, detectionCon=0.7, trackCon=0.7):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon
        )
        self.mpDraw = mp.solutions.drawing_utils

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        all_hands = []
        h, w, c = img.shape
        if self.results.multi_hand_landmarks:
            for handType, handLms in zip(self.results.multi_handedness, self.results.multi_hand_landmarks):
                # lấy loại tay: Left or Right
                label = handType.classification[0].label

                # tính tọa độ hộp bao
                x_list = []
                y_list = []
                for lm in handLms.landmark:
                    x_list.append(int(lm.x * w))
                    y_list.append(int(lm.y * h))
                xmin, xmax = min(x_list), max(x_list)
                ymin, ymax = min(y_list), max(y_list)
                bbox = xmin, ymin, xmax, ymax

                # thêm center
                cx, cy = (xmin + xmax) // 2, (ymin + ymax) // 2

                # tạo danh sách lmList (tọa độ từng điểm landmark)
                lm_list = []
                for id, lm in enumerate(handLms.landmark):
                    px, py = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, px, py])

                # thêm vào từ điển
                all_hands.append({
                    "label": label,
                    "bbox": bbox,
                    "landmarks": handLms,
                    "center": (cx, cy),
                    "lmList": lm_list
                })

                if draw:
                    # vẽ landmarks
                    self.mpDraw.draw_landmarks(
                        img,
                        handLms,
                        self.mpHands.HAND_CONNECTIONS,
                        landmark_drawing_spec=self.mpDraw.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                        connection_drawing_spec=self.mpDraw.DrawingSpec(color=(0, 255, 0), thickness=2)
                    )
                    # vẽ khung chữ nhật
                    cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20), (255, 0, 255), 2)
                    # vẽ nhãn
                    cv2.putText(img, label, (xmin - 30, ymin - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 255), 2)

        return all_hands, img
    
    def fingersUp(self, hand):
        lmList = hand["landmarks"].landmark
        fingers = []

        # Ngón cái
        if hand["label"] == "Right":
            fingers.append(1 if lmList[4].x < lmList[3].x else 0)
        else:
            fingers.append(1 if lmList[4].x > lmList[3].x else 0)

        # 4 ngón còn lại
        tips = [8, 12, 16, 20]
        for tip in tips:
            fingers.append(1 if lmList[tip].y < lmList[tip - 2].y else 0)

        return fingers

    def findPosition(self, img, handNo=0, draw=True):
        lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 0), cv2.FILLED)
        return lmList
