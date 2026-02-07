import time
import winsound

class FocusTracker:
    def get_badge(self):
        if self.focused_time >= 3600:
            return "1 Hour No Distraction"
        elif self.get_stats()[3] >= 80:
            return "Focused Learner"
        else:
            return None

    def __init__(self):
        self.unfocused_since = None
        self.last_state = "FOCUSED"
        self.UNFOCUS_TIME_THRESHOLD = 3.0  # seconds

        # ⏱️ Timers
        self.start_time = time.time()
        self.focused_time = 0.0
        self.unfocused_time = 0.0
        self.last_update_time = time.time()

    def update(self, face_detected, device_detected, study_object_detected, eyes_on_table):
        now = time.time()
        delta = now - self.last_update_time
        self.last_update_time = now

        unfocused = False

        if not face_detected:
            unfocused = True
        elif device_detected and not study_object_detected and not eyes_on_table:
            unfocused = True

        # ---------- TIME-BASED CHECK ----------
        if unfocused:
            if self.unfocused_since is None:
                self.unfocused_since = now
                self.unfocused_time += delta
                return "CHECKING..."

            if now - self.unfocused_since >= self.UNFOCUS_TIME_THRESHOLD:
                self.unfocused_time += delta

                if self.last_state != "UNFOCUSED":
                    self._beep()

                self.last_state = "UNFOCUSED"
                return "UNFOCUSED"

            self.unfocused_time += delta
            return "CHECKING..."

        # ---------- FOCUSED ----------
        self.unfocused_since = None
        self.focused_time += delta
        self.last_state = "FOCUSED"
        return "FOCUSED"

    def get_stats(self):
        total_time = self.focused_time + self.unfocused_time
        focus_score = (self.focused_time / total_time * 100) if total_time > 0 else 0
        return total_time, self.focused_time, self.unfocused_time, focus_score

    def _beep(self):
        for _ in range(3):
            winsound.Beep(1000, 200)