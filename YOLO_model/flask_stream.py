# Final yolo + flask + Backend integration logic
# """
# Smart Classroom AI
# YOLO + Flask + Backend Integration
# """

from flask import Flask, Response
import cv2
from ultralytics import YOLO
import requests
import time

app = Flask(__name__)

# ==========================================
# BACKEND API
# ==========================================
BACKEND_URL = "http://localhost:3000/status"

# ==========================================
# LOAD MODEL
# ==========================================
model = YOLO("yolov8n.pt")
CONF = 0.25

# ==========================================
# OPEN CAMERA
# ==========================================
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("❌ Camera not opened")
    exit()

print("✅ Camera Started")

# ==========================================
# STATE MEMORY
# ==========================================
last_state = None
last_sent_time = 0
SEND_INTERVAL = 5

# ==========================================
# FRAME GENERATOR
# ==========================================
def gen_frames():

    global last_state
    global last_sent_time

    while True:

        success, frame = cap.read()

        if not success:
            print("❌ Frame capture failed")

            # reopen camera automatically
            cap.release()
            time.sleep(1)

            new_cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

            if new_cap.isOpened():
                globals()['cap'] = new_cap
                continue
            else:
                continue

        # ======================================
        # YOLO DETECTION
        # ======================================
        results = model(frame, verbose=False)

        person_detected = False

        for r in results:

            for box in r.boxes:

                conf = float(box.conf[0])
                cls = int(box.cls[0])

                if model.names[cls] == "person" and conf > CONF:

                    person_detected = True

                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # bounding box
                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 100),
                        2
                    )

                    # label
                    label = f"Person {int(conf * 100)}%"

                    cv2.putText(
                        frame,
                        label,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 100),
                        2
                    )

        # ======================================
        # STATUS
        # ======================================
        current_state = "Occupied" if person_detected else "Unoccupied"

        if person_detected:
            color = (0, 255, 100)
        else:
            color = (0, 0, 255)

        cv2.putText(
            frame,
            f"Status: {current_state}",
            (15, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            color,
            2
        )

        cv2.putText(
            frame,
            "Smart Classroom AI",
            (15, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # ======================================
        # SEND TO BACKEND
        # ======================================
        current_time = time.time()

        if (
            current_state != last_state
            and (current_time - last_sent_time > SEND_INTERVAL)
        ):

            payload = {
                "classroom": "A101",
                "status": current_state,
                "timestamp": current_time
            }

            print("Sending:", payload)

            try:
                response = requests.post(
                    BACKEND_URL,
                    json=payload
                )

                print("Backend:", response.text)

                last_state = current_state
                last_sent_time = current_time

            except Exception as e:
                print("Backend Error:", e)

        # ======================================
        # ENCODE FRAME
        # ======================================
        ret, buffer = cv2.imencode(
            '.jpg',
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 70]
        )

        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n'
            + frame_bytes +
            b'\r\n'
        )

# ==========================================
# VIDEO ROUTE
# ==========================================
@app.route('/video_feed')
def video_feed():

    return Response(
        gen_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# ==========================================
# HEALTH ROUTE
# ==========================================
@app.route('/health')
def health():

    return {
        "status": "ok"
    }

# ==========================================
# START SERVER
# ==========================================
if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=5000,
        threaded=True
    )