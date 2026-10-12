# final code 
import cv2
import mediapipe as mp
from ultralytics import YOLO
import time
import numpy as np

# =========================
# YOLO
# =========================
model = YOLO("yolov8n.pt")
CONF = 0.25

# =========================
# MediaPipe
# =========================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

NOSE_TIP = 1
LEFT_EYE_CORNER = 33
RIGHT_EYE_CORNER = 263


def get_ear(lm, pts):
    return (abs(lm[pts[1]].y - lm[pts[5]].y) +
            abs(lm[pts[2]].y - lm[pts[4]].y)) / (2 * abs(lm[pts[0]].x - lm[pts[3]].x) + 1e-6)


def head_move(lm):
    nose = lm[NOSE_TIP]
    left = lm[LEFT_EYE_CORNER]
    right = lm[RIGHT_EYE_CORNER]
    return nose.x - (left.x + right.x) / 2


cap = cv2.VideoCapture(0)

blink = 0
last_blink = time.time()

prev_gray = None

print("System Running 🚀")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape

    person = False
    face = False

    # ================= MOTION =================
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    motion = 0

    if prev_gray is not None:
        motion = np.sum(cv2.absdiff(prev_gray, gray))

    prev_gray = gray

    # ================= YOLO =================
    results = model(frame, verbose=False)

    max_box_area = 0  # IMPORTANT FIX

    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            cls = int(box.cls[0])

            if model.names[cls] == "person" and conf > CONF:
                person = True

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                area = (x2 - x1) * (y2 - y1)
                max_box_area = max(max_box_area, area)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

    # ================= FACE =================
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = face_mesh.process(rgb)

    head_ok = False

    if res.multi_face_landmarks:
        face = True

        for f in res.multi_face_landmarks:
            lm = f.landmark

            ear = (get_ear(lm, LEFT_EYE) + get_ear(lm, RIGHT_EYE)) / 2

            # blink detection after every 0.3 sec to avoid multiple counts
            if ear < 0.2:
                if time.time() - last_blink > 0.3:
                    blink += 1
                    last_blink = time.time()

            yaw = head_move(lm)

            if abs(yaw) > 0.05:
                head_ok = True

    # ================= LOGIC FIX =================

    if person:

        # 🔥 CASE 1: REAL HUMAN
        if face and (blink >= 2 or head_ok):
            status = "Occupied (REAL HUMAN ✅)"
            color = (0, 255, 0)

        # 🔥 CASE 2: FAR PERSON
        elif max_box_area < 50000 and motion > 200000:
            status = "Occupied (Far Person)"
            color = (255, 0, 255)

        # 🔥 CASE 3: FAKE IMAGE
        else:
            status = "Unoccupied (Fake / Image ❌)"
            color = (0, 0, 255)

    else:
        status = "Unoccupied"
        color = (0, 0, 255)

        blink = 0
        head_ok = False

    cv2.putText(frame, status, (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    cv2.imshow("Smart System FIXED", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()