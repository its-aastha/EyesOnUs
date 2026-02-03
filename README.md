# EyesOnUS 👀  
**AI-Powered Focus Monitoring System**

EyesOnUS is a real-time focus detection web application designed to help students stay attentive during study sessions.  
It uses computer vision and deep learning to analyze face presence, eye direction, and object distractions through a live webcam feed.

---

## 🚀 Features

-  User Authentication (Signup / Login)
-  Live Webcam Streaming
-  Face Detection
-  Eye Direction Tracking (Eyes on screen / table)
-  Device & Object Detection (Mobile, books, etc.)
-  Focus vs Distraction Logic
- ⏱ Session Tracking (Focused & Unfocused time)
-  Focus Score Calculation
-  Session History stored per user
-  Web Dashboard (Flask + HTML/CSS)

---

## 🧠 How It Works

1. User logs in and starts a study session  
2. Webcam feed is analyzed in real time  
3. System checks:
   - Face presence  
   - Eye direction  
   - Device / object distraction  
4. Focus status is updated continuously  
5. On session stop, a detailed summary is saved  

---

## 🛠️ Tech Stack
1. Backend: Python, Flask
2. Computer Vision: OpenCV, MediaPipe
3. Deep Learning: YOLOv8 (Ultralytics), Torch
4. Frontend: HTML, CSS
5. Authentication: Werkzeug (Password Hashing)

---
## 🗂️ Project Structure

```text
EyesOnUS/
│
├── app.py                     # Main Flask application
├── users.json                 # User & session data (file-based DB)
├── requirements.txt           # Python dependencies
├── README.md
│
├── static/
│   ├── style.css              # UI styling
│   └── beep.wav               # Alert sound
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   └── dashboard.html
│
├── utils/
│   ├── face_detector.py       # Face & eye detection logic
│   ├── object_detector.py     # YOLO object detection
│   ├── focus_logic.py         # Focus tracking & scoring
│   └── camera_test.py
│
├── deploy.prototxt             # Face detection model config
├── res10_300x300_ssd_iter_140000.caffemodel
├── yolov8n.pt                  # YOLOv8 model
└── test_mediapipe.py
