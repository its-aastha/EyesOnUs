# EyesOnUS 👀  
## AI-Based Student Focus & Exam Monitoring System

EyesOnUS is an AI-powered web application built **to help students stay focused and prevent cheating during online exams and study sessions**.  
It continuously monitors student behavior using computer vision and records focus data for evaluation and accountability.

---

## 🎯 Project Purpose

This project is designed to:
- Ensure **students remain focused during exams**
- Detect **cheating behavior** such as mobile usage or looking away
- Maintain **study & exam discipline**
- Track **focus performance over time**
- Store session data for **review and analysis**

---

## ⭐ Key Features (IMPORTANT)

### 🧠 Focus Monitoring
- Live webcam monitoring
- Face presence detection
- Eye direction detection (screen vs table)
- Detects loss of focus when face is missing or attention is diverted

### 🚫 Anti-Cheating Detection
- Detects **mobile phones, laptops, and distracting devices**
- Flags distraction during exams
- Triggers alert when cheating behavior continues
- Helps invigilators identify suspicious activity

### ⏱ Session & Exam Tracking
- Tracks:
  - Total session time
  - Focused time
  - Distracted time
- Automatically calculates **Focus Score (%)**
- Session starts and stops are controlled from the dashboard

### 🔥 Streak & Discipline Tracking
- Maintains **study/exam streaks**
- Encourages consistency and discipline
- Helps students build focused habits

### 📅 Dashboard with Calendar
- Calendar view to track sessions by date
- Easily see:
  - Exam days
  - Study days
  - Missed days

### 🗃 Persistent Data Storage
- All user and session data is:
  - **Fetched**
  - **Stored**
  - **Updated**
  in `users.json`
- No database required
- Each user has individual session history

---

## 🗂️ Stored Session Data (users.json)

Each session is saved with full details:

```json
{
  "email@example.com": {
    "name": "Student Name",
    "sessions": [
      {
        "start_str": "2026-02-05 22:01:19",
        "end_str": "2026-02-05 22:01:50",
        "total_seconds": 31.35,
        "focused_seconds": 17.9,
        "unfocused_seconds": 13.44,
        "score": 57
      }
    ]
  }
}
