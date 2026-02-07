from flask import Flask, Response, render_template, request, redirect, url_for, session, jsonify
import os
import json
import functools
import time
import cv2
import calendar as pycal
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Import project utilities
from utils.face_detector import detect_face, eyes_on_table
from utils.object_detector import detect_objects
from utils.focus_logic import FocusTracker

# ================= APP SETUP =================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-me")

USERS_PATH = "users.json"
app.config["SESSION_ACTIVE"] = False

camera = cv2.VideoCapture(0)
tracker = FocusTracker()

# ================= USER STORE =================
def _ensure_users_file():
    if not os.path.exists(USERS_PATH):
        with open(USERS_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)

def load_users():
    _ensure_users_file()
    with open(USERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

# ================= AUTH =================
def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    message = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not (name and email and password):
            message = "Please fill all fields."
        else:
            users = load_users()
            if email in users:
                message = "User already exists."
            else:
                users[email] = {
                    "name": name,
                    "password": generate_password_hash(password),
                    "sessions": []
                }
                save_users(users)
                session["user"] = email
                return redirect(url_for("dashboard"))

    return render_template("signup.html", message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    message = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        users = load_users()
        user = users.get(email)

        if user and check_password_hash(user["password"], password):
            session["user"] = email
            return redirect(url_for("dashboard"))
        message = "Invalid credentials."

    return render_template("login.html", message=message)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

# ================= DASHBOARD =================
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# ================= SESSION CONTROL =================
@app.route("/session/start", methods=["POST"])
@login_required
def session_start():
    global tracker
    app.config["SESSION_ACTIVE"] = True
    tracker = FocusTracker()
    app.config["SESSION_STARTED_AT"] = time.time()
    return jsonify(success=True)

@app.route("/session/stop", methods=["POST"])
@login_required
def session_stop():
    app.config["SESSION_ACTIVE"] = False

    total, focused, unfocused, score = tracker.get_stats()
    end_ts = time.time()
    start_ts = app.config.get("SESSION_STARTED_AT", end_ts)

    record = {
        "start_ts": start_ts,
        "end_ts": end_ts,
        "total_seconds": round(total, 2),
        "focused_seconds": round(focused, 2),
        "unfocused_seconds": round(unfocused, 2),
        "score": int(score),
        "completed": True,
        "start_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_ts)),
        "end_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_ts))
    }

    users = load_users()
    email = session["user"]
    users[email].setdefault("sessions", []).append(record)
    users[email]["sessions"] = users[email]["sessions"][-30:]
    save_users(users)

    return jsonify(success=True, last_session=record)

@app.route("/api/status")
def api_status():
    total, focused, unfocused, score = tracker.get_stats()
    return jsonify(
        session_active=app.config["SESSION_ACTIVE"],
        focused=focused,
        unfocused=unfocused,
        score=int(score)
    )

# ================= PROFILE + MONTHLY CALENDAR =================
@app.route("/profile")
@login_required
def profile():
    users = load_users()
    email = session["user"]
    user = users[email]
    sessions = user.get("sessions", [])

    total_sessions = len(sessions)
    total_focused = sum(s["focused_seconds"] for s in sessions)
    avg_score = int(sum(s["score"] for s in sessions) / total_sessions) if total_sessions else 0

    today = datetime.today()
    year, month = today.year, today.month
    month_name = today.strftime("%B %Y")
    month_days = pycal.monthcalendar(year, month)

    day_scores = {}
    for s in sessions:
        dt = datetime.strptime(s["start_str"], "%Y-%m-%d %H:%M:%S")
        if dt.year == year and dt.month == month:
            day_scores[dt.day] = max(day_scores.get(dt.day, 0), s["score"])

    focused_days = set()
    streak_start = set()
    prev_focused = False

    for day in sorted(day_scores):
        focused = day_scores[day] >= 70
        if focused:
            focused_days.add(day)
            if not prev_focused:
                streak_start.add(day)
        prev_focused = focused

    return render_template(
        "profile.html",
        user=user,
        email=email,
        sessions=sessions,
        total_sessions=total_sessions,
        total_focused=total_focused,
        avg_score=avg_score,
        month_name=month_name,
        month_days=month_days,
        focused_days=focused_days,
        streak_start=streak_start
    )

# ================= CAMERA STREAM =================
def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break

        device_detected, study_object_detected, objects = detect_objects(frame)
        face_detected, face_box = detect_face(frame)
        eyes_down = eyes_on_table(face_box, frame.shape[0])

        if app.config["SESSION_ACTIVE"]:
            status = tracker.update(face_detected, device_detected, study_object_detected, eyes_down)
        else:
            status = "INACTIVE"

        if face_detected and face_box:
            x, y, w, h = face_box
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)

        cv2.putText(frame, status, (20,40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0,255,0) if status=="FOCUSED" else (200,200,200), 2)

        ret, buffer = cv2.imencode(".jpg", frame)
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
               buffer.tobytes() + b"\r\n")

@app.route("/video")
def video():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
