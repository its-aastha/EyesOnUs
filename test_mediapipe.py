import mediapipe as mp

print("MediaPipe version:", mp.__version__)

# Correct way (SUPPORTED)
mp_face = mp.solutions.face_detection
detector = mp_face.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.6
)

print("MediaPipe Face Detection loaded successfully")
