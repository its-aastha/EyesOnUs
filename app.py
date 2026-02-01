from flask import Flask, Response, render_template, request, redirect, url_for, session, jsonify
import os
import json
import functools
import time
import cv2
from werkzeug.security import generate_password_hash, check_password_hash

# Import project utilities
from utils.face_detector import detect_face, eyes_on_table
from utils.object_detector import detect_objects
from utils.focus_logic import FocusTracker

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-me")

# Simple file-backed users store (demo)
USERS_PATH = "users.json"

# App-wide session flag (whether detection is active)
app.config["SESSION_ACTIVE"] = False

# Camera & focus tracker
camera = cv2.VideoCapture(0)
tracker = FocusTracker()


# ----------------- Authentication helpers -----------------

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


def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login", next=request.path))
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
                message = "User already exists. Please log in."
            else:
                users[email] = {
                    "name": name,
                    "password": generate_password_hash(password)
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
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)
        message = "Invalid credentials."

    return render_template("login.html", message=message)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/session/start", methods=["POST"])
@login_required
def session_start():
    global tracker
    app.config["SESSION_ACTIVE"] = True
    tracker = FocusTracker()  # reset stats
    # record when session started for more accurate summaries
    app.config["SESSION_STARTED_AT"] = getattr(tracker, "start_time", time.time())
    return jsonify({"success": True})


@app.route("/session/stop", methods=["POST"])
@login_required
def session_stop():
    # stop detection and persist the session summary for the current user
    app.config["SESSION_ACTIVE"] = False

    total, focused, unfocused, score = tracker.get_stats()
    end_ts = time.time()
    start_ts = end_ts - total if total and total > 0 else app.config.get("SESSION_STARTED_AT", end_ts)

    session_record = {
        "start_ts": start_ts,
        "end_ts": end_ts,
        "total_seconds": round(total, 2),
        "focused_seconds": round(focused, 2),
        "unfocused_seconds": round(unfocused, 2),
        "score": int(score),
        "start_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_ts)),
        "end_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_ts))
    }

    # attach to user's history (file-backed store)
    try:
        users = load_users()
        user_email = session.get("user")
        if user_email and user_email in users:
            users[user_email].setdefault("sessions", [])
            users[user_email]["sessions"].append(session_record)
            # keep only last 20 sessions to avoid unbounded growth in demo store
            users[user_email]["sessions"] = users[user_email]["sessions"][-20:]
            save_users(users)
    except Exception:
        # don't fail stopping session if persistence fails; still return the record
        pass

    return jsonify({"success": True, "last_session": session_record})


@app.route("/api/status")
def api_status():
    total, focused, unfocused, score = tracker.get_stats()

    last_session = None
    try:
        users = load_users()
        user_email = session.get("user")
        if user_email and user_email in users:
            last_session = (users[user_email].get("sessions") or [])[-1] if users[user_email].get("sessions") else None
    except Exception:
        last_session = None

    return jsonify({
        "session_active": bool(app.config.get("SESSION_ACTIVE")),
        "total": total,
        "focused": focused,
        "unfocused": unfocused,
        "score": int(score),
        "user": session.get("user"),
        "last_session": last_session
    })


def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break

        # ---------- OBJECT DETECTION ----------
        device_detected, study_object_detected, objects = detect_objects(frame)

        # ---------- FACE DETECTION ----------
        face_detected, face_box = detect_face(frame)

        # ---------- EYE DIRECTION ----------
        frame_height = frame.shape[0]
        eyes_down = eyes_on_table(face_box, frame_height)

        # ---------- FOCUS LOGIC ----------
        if app.config.get("SESSION_ACTIVE"):
            status = tracker.update(
                face_detected,
                device_detected,
                study_object_detected,
                eyes_down
            )
        else:
            status = "INACTIVE"

        # ---------- DRAW FACE ----------
        if face_detected and face_box:
            x, y, w, h = face_box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # ---------- STATUS TEXT ----------
        color = (0, 255, 0) if status == "FOCUSED" else (0, 0, 255)
        if status == "INACTIVE":
            color = (200, 200, 200)

        cv2.putText(frame, status, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        # ---------- DEBUG OBJECTS ----------
        cv2.putText(frame, f"Objects: {', '.join(objects)}",
                    (20, 180), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (255, 255, 255), 2)

        # ---------- STATS ----------
        total, focused, unfocused, score = tracker.get_stats()

        def fmt(t):
            return f"{int(t//60):02d}:{int(t%60):02d}"

        cv2.putText(frame, f"Focused: {fmt(focused)}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

        cv2.putText(frame, f"Distracted: {fmt(unfocused)}", (20, 110),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

        cv2.putText(frame, f"Score: {int(score)}%", (20, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

        if status == "INACTIVE":
            cv2.putText(frame, "Session inactive — press Start",
                        (20, frame.shape[0] - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (200,200,200), 2)

        # ---------- STREAM ----------
        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" +
               frame + b"\r\n")
@app.route("/video")
def video():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)