import cv2

net = cv2.dnn.readNetFromCaffe(
    "deploy.prototxt",
    "res10_300x300_ssd_iter_140000.caffemodel"
)

def detect_face(frame):
    h, w = frame.shape[:2]

    blob = cv2.dnn.blobFromImage(
        cv2.resize(frame, (300, 300)),
        1.0,
        (300, 300),
        (104.0, 177.0, 123.0)
    )

    net.setInput(blob)
    detections = net.forward()

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]

        if confidence > 0.6:
            box = detections[0, 0, i, 3:7] * [w, h, w, h]
            x1, y1, x2, y2 = box.astype("int")

            face_w = x2 - x1
            face_h = y2 - y1
            face_area = face_w * face_h
            frame_area = w * h

            # Reject body / false detections
            if face_area < frame_area * 0.02:
                continue
            if face_area > frame_area * 0.6:
                continue

            return True, (x1, y1, face_w, face_h)

    return False, None


def eyes_on_table(face_box, frame_height):
    """
    Returns True if user is likely looking down at table
    """
    if face_box is None:
        return False

    x, y, w, h = face_box
    face_center_y = y + h / 2

    # Face lower in frame → eyes down
    if face_center_y > frame_height * 0.55:
        return True

    return False