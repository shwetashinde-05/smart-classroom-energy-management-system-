# import cv2
# import mediapipe as mp
# from ultralytics import YOLO
# import time
# import numpy as np

# # =========================
# # MODELS SETUP
# # =========================
# model = YOLO("yolov8n.pt")
# CONF = 0.25

# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

# # =========================
# # LANDMARKS
# # =========================
# LEFT_EYE = [362, 385, 387, 263, 373, 380]
# RIGHT_EYE = [33, 160, 158, 133, 153, 144]

# NOSE_TIP = 1
# LEFT_EYE_CORNER = 33
# RIGHT_EYE_CORNER = 263


# # =========================
# # HELPERS
# # =========================
# def get_ear(lm, pts):
#     return (abs(lm[pts[1]].y - lm[pts[5]].y) +
#             abs(lm[pts[2]].y - lm[pts[4]].y)) / (2 * abs(lm[pts[0]].x - lm[pts[3]].x) + 1e-6)


# def head_move(lm):
#     nose = lm[NOSE_TIP]
#     left = lm[LEFT_EYE_CORNER]
#     right = lm[RIGHT_EYE_CORNER]
#     return nose.x - (left.x + right.x) / 2


# # =========================
# # MAIN AI FUNCTION (STEP 1 CORE)
# # =========================
# def analyze_frame(frame, prev_gray=None, blink_state=None):
#     """
#     INPUT: frame
#     OUTPUT: JSON (status, type, timestamp)
#     """

#     if blink_state is None:
#         blink_state = {"blink": 0, "last_blink": time.time()}

#     person = False
#     face = False
#     head_ok = False

#     blink = blink_state["blink"]
#     last_blink = blink_state["last_blink"]

#     # ================= MOTION =================
#     gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#     motion = 0

#     if prev_gray is not None:
#         motion = np.sum(cv2.absdiff(prev_gray, gray))

#     prev_gray = gray

#     # ================= YOLO =================
#     results = model(frame, verbose=False)

#     max_box_area = 0

#     for r in results:
#         for box in r.boxes:
#             conf = float(box.conf[0])
#             cls = int(box.cls[0])

#             if model.names[cls] == "person" and conf > CONF:
#                 person = True

#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 area = (x2 - x1) * (y2 - y1)
#                 max_box_area = max(max_box_area, area)

#     # ================= FACE =================
#     rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     res = face_mesh.process(rgb)

#     if res.multi_face_landmarks:
#         face = True

#         for f in res.multi_face_landmarks:
#             lm = f.landmark

#             ear = (get_ear(lm, LEFT_EYE) + get_ear(lm, RIGHT_EYE)) / 2

#             # blink detection (stable)
#             if ear < 0.2 and (time.time() - last_blink) > 0.4:
#                 blink += 1
#                 last_blink = time.time()

#             yaw = head_move(lm)

#             if abs(yaw) > 0.05:
#                 head_ok = True

#     # ================= FINAL DECISION =================

#     if person:

#         # REAL HUMAN
#         if face and (blink >= 2 or head_ok):
#             status = "Occupied (REAL HUMAN)"
#             type_ = "real"

#         # FAR PERSON
#         elif max_box_area < 50000:
#             status = "Occupied (Far Person)"
#             type_ = "far"

#         # FAKE / IMAGE
#         else:
#             status = "Unoccupied (Fake/Image)"
#             type_ = "fake"

#     else:
#         status = "Unoccupied"
#         type_ = "none"

#     return {
#         "status": status,
#         "type": type_,
#         "timestamp": time.time()
#     }, prev_gray, {"blink": blink, "last_blink": last_blink}


# # =========================
# # TEST LOOP (ONLY FOR CHECKING)
# # =========================
# cap = cv2.VideoCapture(0)

# prev_gray = None
# blink_state = None

# print("AI Engine Running 🚀")

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         break

#     result, prev_gray, blink_state = analyze_frame(frame, prev_gray, blink_state)

#     print(result)   # ONLY JSON OUTPUT (BACKEND READY)

#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()


import requests
import cv2
import mediapipe as mp
from ultralytics import YOLO
import numpy as np
#API url
url = "http://localhost:3000/status"
# =========================
# MODELS SETUP
# =========================
model = YOLO("yolov8n.pt")
CONF = 0.25

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

# =========================
# LANDMARKS
# =========================
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

NOSE_TIP = 1
LEFT_EYE_CORNER = 33
RIGHT_EYE_CORNER = 263


# =========================
# HELPERS
# =========================
def get_ear(lm, pts):
    return (abs(lm[pts[1]].y - lm[pts[5]].y) +
            abs(lm[pts[2]].y - lm[pts[4]].y)) / (2 * abs(lm[pts[0]].x - lm[pts[3]].x) + 1e-6)


def head_move(lm):
    nose = lm[NOSE_TIP]
    left = lm[LEFT_EYE_CORNER]
    right = lm[RIGHT_EYE_CORNER]
    return nose.x - (left.x + right.x) / 2


# =========================
# MAIN AI FUNCTION (STEP 1 CORE)
# =========================
def analyze_frame(frame, prev_gray=None, blink_state=None):
    """
    INPUT: frame
    OUTPUT: JSON (status, type, timestamp)
    """

    if blink_state is None:
        blink_state = {"blink": 0, "last_blink": time.time()}

    person = False
    face = False
    head_ok = False

    blink = blink_state["blink"]
    last_blink = blink_state["last_blink"]

    # ================= MOTION =================
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    motion = 0

    if prev_gray is not None:
        motion = np.sum(cv2.absdiff(prev_gray, gray))

    prev_gray = gray

    # ================= YOLO =================
    results = model(frame, verbose=False)

    max_box_area = 0

    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            cls = int(box.cls[0])

            if model.names[cls] == "person" and conf > CONF:
                person = True

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                area = (x2 - x1) * (y2 - y1)
                max_box_area = max(max_box_area, area)

    # ================= FACE =================
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = face_mesh.process(rgb)

    if res.multi_face_landmarks:
        face = True

        for f in res.multi_face_landmarks:
            lm = f.landmark

            ear = (get_ear(lm, LEFT_EYE) + get_ear(lm, RIGHT_EYE)) / 2

            # blink detection (stable)
            if ear < 0.2 and (time.time() - last_blink) > 0.4:
                blink += 1
                last_blink = time.time()

            yaw = head_move(lm)

            if abs(yaw) > 0.05:
                head_ok = True

    # ================= FINAL DECISION =================

    if person:

        # REAL HUMAN
        if face and (blink >= 2 or head_ok):
            status = "Occupied (REAL HUMAN)"
            type_ = "real"

        # FAR PERSON
        elif max_box_area < 50000:
            status = "Occupied (Far Person)"
            type_ = "far"

        # FAKE / IMAGE
        else:
            status = "Unoccupied (Fake/Image)"
            type_ = "fake"

    else:
        status = "Unoccupied"
        type_ = "none"

    return {
        "status": status,
        "type": type_,
        "timestamp": time.time()
    }, prev_gray, {"blink": blink, "last_blink": last_blink}


from collections import deque
import time

# =========================
# TEST LOOP (FINAL VERSION)
# =========================
cap = cv2.VideoCapture(0)

prev_gray = None
blink_state = None

# 🔥 STATE MEMORY
last_sent_time = 0
SEND_INTERVAL = 5  # seconds
last_sent_state = None

print("AI Engine Running 🚀")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    result, prev_gray, blink_state = analyze_frame(
        frame,
        prev_gray,
        blink_state
    )

    # =========================
    # CONVERT TO FINAL STATE
    # =========================
    if result["type"] in ["real", "far"]:
        current_state = "Occupied"
    else:
        current_state = "Unoccupied"

    # =========================
    # SEND ONLY WHEN STATE CHANGES
    # =========================
    current_time = time.time()

    if current_state != last_sent_state and (current_time - last_sent_time > SEND_INTERVAL):

     final_output = {
        "classroom": "A101",
        "status": current_state,
        "timestamp": current_time
     }

     print("Sending to backend:", final_output)

     try:
        response = requests.post(url, json=final_output)
        print("Server Response:", response.text)
     except Exception as e:
        print("Error:", e)

     last_sent_state = current_state
     last_sent_time = current_time

    # press q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
