# utils/object_detector.py
from ultralytics import YOLO

# Load YOLOv8 model (auto-downloads)
model = YOLO("yolov8n.pt")

DISTRACTING_OBJECTS = ["cell phone", "mobile phone", "laptop"]
STUDY_OBJECTS = ["book", "notebook"]

def detect_objects(frame):
    results = model(frame, verbose=False)

    device_detected = False
    study_object_detected = False
    detected_names = []

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            detected_names.append(label)

            if label in DISTRACTING_OBJECTS:
                device_detected = True

            if label in STUDY_OBJECTS:
                study_object_detected = True

    return device_detected, study_object_detected, detected_names