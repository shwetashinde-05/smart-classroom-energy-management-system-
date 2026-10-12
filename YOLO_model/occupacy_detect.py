from ultralytics import YOLO
import cv2

# Load YOLO model
model = YOLO("yolov8n.pt")

# Start webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if not ret:
        break
    
    # Run detection
    results = model(frame)

    person_detected = False

    # Check detected objects
    for r in results:
        for box in r.boxes:
            class_id = int(box.cls[0])
            object_name = model.names[class_id]

            if object_name == "person":
                person_detected = True

    # Occupancy logic
    if person_detected:
        status = "OCCUPIED"
    else:
        status = "EMPTY"

    # Show detection boxes
    annotated_frame = results[0].plot()

    # Show status on screen
    cv2.putText(
        annotated_frame,
        f"Classroom: {status}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow("Classroom Monitoring", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()