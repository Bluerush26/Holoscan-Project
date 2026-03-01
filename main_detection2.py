import cv2
from ultralytics import YOLO
import pyttsx3
import threading
import queue
import time
import math
from collections import deque
from settings_gui import open_settings

# --- 0. OPEN SETTINGS GUI FIRST ---
IMPORTANT_OBJECTS = open_settings()
print(f"[CONFIG] Detecting {len(IMPORTANT_OBJECTS)} labels: {IMPORTANT_OBJECTS}")

# --- 1. ROBUST VOICE SYSTEM (FRESH ENGINE PATTERN) ---
voice_queue = queue.Queue()
last_spoken = {}
COOLDOWN_SECONDS = 4.0

def voice_worker():
    """Background thread that re-initializes the engine for every sentence."""
    while True:
        text = voice_queue.get()
        if text is None:
            break

        try:
            print(f"[VOICE] Initializing engine for: {text}")
            engine = pyttsx3.init()
            engine.setProperty('rate', 160)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            del engine
            print(f"[VOICE] Speech complete.")
        except Exception as e:
            print(f"Voice Worker Error: {e}")

        voice_queue.task_done()
        time.sleep(0.2)

threading.Thread(target=voice_worker, daemon=True).start()


def speak_safe(label, position):
    """Adds a message to the queue with cooldown and backlog protection."""
    current_time = time.time()

    if label not in last_spoken or (current_time - last_spoken[label] > COOLDOWN_SECONDS):
        message = f"{label} {position}"

        if voice_queue.qsize() < 2:
            print(f"[QUEUE] Adding: {message}")
            voice_queue.put(message)
            last_spoken[label] = current_time


# --- 2. VISION & DETECTION SETUP ---
model = YOLO("yolo11n.pt")
cap = cv2.VideoCapture("tester.mp4")

# --- OBJECT APPROACH TRACKER ---
# Tracks bounding box height over time per object to detect approaching motion.
# Each tracked object: {"center": (cx, cy), "heights": deque([h1, h2, ...]), "last_seen": frame_num}
object_tracks = {}   # key: "label_0", "label_1", etc.
HISTORY_LENGTH = 20  # number of frames to remember per object
MATCH_DISTANCE = 120 # max pixel distance to consider "same object" between frames
GROWTH_THRESHOLD = 1.20  # 20% growth from early to recent = approaching
STALE_FRAMES = 30    # remove tracks not seen for this many frames
frame_count = 0


def match_or_create_track(label, cx, cy, height):
    """Match a detection to an existing track by label + proximity, or create a new one."""
    best_key = None
    best_dist = float('inf')

    # Search existing tracks with the same label
    for key, track in object_tracks.items():
        if not key.startswith(label + "_"):
            continue
        tx, ty = track["center"]
        dist = math.hypot(cx - tx, cy - ty)
        if dist < best_dist:
            best_dist = dist
            best_key = key

    if best_key and best_dist < MATCH_DISTANCE:
        # Update existing track
        track = object_tracks[best_key]
        track["center"] = (cx, cy)
        track["heights"].append(height)
        track["last_seen"] = frame_count
        return best_key
    else:
        # Create new track
        idx = sum(1 for k in object_tracks if k.startswith(label + "_"))
        new_key = f"{label}_{idx}"
        object_tracks[new_key] = {
            "center": (cx, cy),
            "heights": deque([height], maxlen=HISTORY_LENGTH),
            "last_seen": frame_count,
        }
        return new_key


def is_approaching(track_key):
    """Check if an object's bounding box is growing over its history."""
    heights = object_tracks[track_key]["heights"]

    # Need enough data points to compare
    if len(heights) < 8:
        return False

    # Compare average of the first third vs the last third of the history
    split = len(heights) // 3
    early_avg = sum(list(heights)[:split]) / split
    recent_avg = sum(list(heights)[-split:]) / split

    if early_avg == 0:
        return False

    growth_ratio = recent_avg / early_avg
    return growth_ratio >= GROWTH_THRESHOLD


def cleanup_stale_tracks():
    """Remove tracks that haven't been seen recently."""
    stale = [k for k, v in object_tracks.items() if frame_count - v["last_seen"] > STALE_FRAMES]
    for k in stale:
        del object_tracks[k]


print("--- Smart Eye Assistant Active ---")
print("Press 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    frame_count += 1
    h, w, _ = frame.shape
    results = model(frame, verbose=False, stream=True)

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            label = model.names[int(box.cls[0])]
            conf = float(box.conf[0])

            if conf > 0.85 and label in IMPORTANT_OBJECTS:
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                obj_height = y2 - y1

                # Spatial logic
                if center_x < w / 3:
                    pos_text = "on your left"
                elif center_x > 2 * (w / 3):
                    pos_text = "on your right"
                else:
                    pos_text = "straight ahead"

                # Track this object and check if approaching
                track_key = match_or_create_track(label, center_x, center_y, obj_height)
                approaching = is_approaching(track_key)

                # Color: red if approaching, green if stable/receding
                color = (0, 0, 255) if approaching else (0, 255, 0)

                # Visuals
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                status = "APPROACHING" if approaching else label
                cv2.putText(frame, f"{label} [{status}]", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                # Only warn if the object is getting closer
                if approaching:
                    speak_safe(f"{label} close", pos_text)

    # Clean up objects that left the frame
    cleanup_stale_tracks()

    # --- 3. UI OVERLAY ---
    cv2.line(frame, (int(w / 3), 0), (int(w / 3), h), (200, 200, 200), 1)
    cv2.line(frame, (int(2 * w / 3), 0), (int(2 * w / 3), h), (200, 200, 200), 1)

    cv2.putText(frame, "LEFT", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "CENTER", (int(w / 3) + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "RIGHT", (int(2 * w / 3) + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Smart Eye Assistant", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()