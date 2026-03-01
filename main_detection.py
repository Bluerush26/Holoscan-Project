import cv2
from ultralytics import YOLO
import pyttsx3
import threading
import queue
import time
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
cap = cv2.VideoCapture("videoplayback.mp4")

print("--- Smart Eye Assistant Active ---")
print("Press 'q' to quit.")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    h, w, _ = frame.shape
    results = model(frame, verbose=False, stream=True)

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            label = model.names[int(box.cls[0])]
            conf = float(box.conf[0])

            if conf > 0.9 and label in IMPORTANT_OBJECTS:
                center_x = (x1 + x2) / 2
                obj_height = y2 - y1

                if center_x < w / 3:
                    pos_text = "on your left"
                elif center_x > 2 * (w / 3):
                    pos_text = "on your right"
                else:
                    pos_text = "straight ahead"

                if label != "car":
                    is_close = obj_height > (h * 0.55)
                else:
                    is_close = obj_height > (h * 0.75)
                color = (0, 0, 255) if is_close else (0, 255, 0)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{label}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                if is_close:
                    speak_safe(f"Caution, {label}", pos_text)
                else:
                    speak_safe(label, pos_text)

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