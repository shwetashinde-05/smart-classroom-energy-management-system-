#simplified the system to improve real-time performance and reliability. Person detection alone is sufficient for occupancy-based energy control.
import requests
import cv2
from ultralytics import YOLO
import numpy as np
import time


# API url
url = "http://localhost:3000/status"

# =========================
# MODEL SETUP
# =========================
model = YOLO("yolov8n.pt")
CONF = 0.25

# =========================
# MAIN AI FUNCTION (SIMPLIFIED)
# =========================
def analyze_frame(frame, prev_gray=None):
    """
    INPUT: frame
    OUTPUT: JSON (status, type, timestamp)
    """

    person = False

    # ================= MOTION (kept as it is)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    if prev_gray is not None:
        motion = np.sum(cv2.absdiff(prev_gray, gray))

    prev_gray = gray

    # ================= YOLO (ONLY PERSON DETECTION)
    results = model(frame, verbose=False)

    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            cls = int(box.cls[0])

            if model.names[cls] == "person" and conf > CONF:
                person = True

    # ================= FINAL DECISION (SIMPLIFIED)
    if person:
        status = "Occupied"
        type_ = "real"
    else:
        status = "Unoccupied"
        type_ = "none"

    return {
        "status": status,
        "type": type_,
        "timestamp": time.time()
    }, prev_gray


# =========================
# TEST LOOP (UNCHANGED)
# =========================
# rtsp_url = "rtsp://admin:password@192.168.1.108:554/stream1"
# cap = cv2.VideoCapture(rtsp_url)
cap = cv2.VideoCapture(0) #use webcam for testing
# Optional: improve stability
# cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

prev_gray = None

# 🔥 STATE MEMORY
last_sent_time = 0
SEND_INTERVAL = 5  # seconds
last_sent_state = None

print("AI Engine Running 🚀")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    result, prev_gray = analyze_frame(
        frame,
        prev_gray
    )

    # =========================
    # CONVERT TO FINAL STATE
    # =========================
    if result["type"] == "real":
        current_state = "Occupied" 
    else:
        current_state = "Unoccupied"  # now truly empty    
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