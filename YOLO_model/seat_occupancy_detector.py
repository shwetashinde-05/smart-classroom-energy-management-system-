import cv2
import mediapipe as mp
from ultralytics import YOLO
import time

# 1. Setup YOLOv8 and Mediapipe
model = YOLO('yolov8n.pt')

# Correct MediaPipe setup
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

# Eye Landmark Indices
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

def get_aspect_ratio(landmarks, points):
    # Vertical distances
    p2_p6 = abs(landmarks[points[1]].y - landmarks[points[5]].y)
    p3_p5 = abs(landmarks[points[2]].y - landmarks[points[4]].y)
    # Horizontal distance
    p1_p4 = abs(landmarks[points[0]].x - landmarks[points[3]].x)

    if p1_p4 == 0:   # prevent division error
        return 0

    return (p2_p6 + p3_p5) / (2.0 * p1_p4)

# Initialize Video
cap = cv2.VideoCapture(0)
has_blinked = False
status = "Unoccupied"

print("System Starting... Looking for real humans.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # A. YOLO Person Detection
    results = model(frame, verbose=False)
    person_detected = False

    for r in results:
        for box in r.boxes:
            if model.names[int(box.cls[0])] == 'person':
                person_detected = True
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

    # B. Mediapipe Liveness (Blink Detection)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_results = face_mesh.process(rgb_frame)

    if face_results.multi_face_landmarks:
        for face_landmarks in face_results.multi_face_landmarks:
            left_ear = get_aspect_ratio(face_landmarks.landmark, LEFT_EYE)
            right_ear = get_aspect_ratio(face_landmarks.landmark, RIGHT_EYE)
            ear = (left_ear + right_ear) / 2.0

            # Blink detection
            if ear < 0.20:
                has_blinked = True

            # OPTIONAL: draw face mesh
            mp_drawing.draw_landmarks(
                frame,
                face_landmarks,
                mp_face_mesh.FACEMESH_TESSELATION
            )

    # C. Final Logic
    if person_detected and has_blinked:
        status = "Occupied (Real Person)"
        color = (0, 255, 0)

    elif person_detected and not has_blinked:
        status = "Checking Liveness... (Please Blink)"
        color = (0, 165, 255)

    else:
        status = "Unoccupied"
        color = (0, 0, 255)
        has_blinked = False  # reset

    # UI Overlay
    cv2.putText(frame, f"Status: {status}", (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    cv2.imshow("Smart Classroom Liveness Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

