import cv2
import mediapipe as mp
import numpy as np
import threading
import time
import math
import os
import urllib.request
from flask import Flask, Response, render_template, jsonify
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    HandLandmarkerResult,
    RunningMode,
    HandLandmarksConnections,
)

app = Flask(__name__)

MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")

def ensure_model():
    if os.path.exists(MODEL_PATH):
        print("[GestureAI] Model found:", MODEL_PATH)
        return
    print("[GestureAI] Downloading hand landmark model (~8 MB)...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("[GestureAI] Model downloaded ->", MODEL_PATH)
    except Exception as e:
        raise RuntimeError(
            f"\n[ERROR] Could not download model: {e}\n"
            f"Download manually from:\n  {MODEL_URL}\n"
            f"Place it next to app.py as:  hand_landmarker.task\n"
        )

state = {
    "gesture":         "None",
    "confidence":      0.0,
    "hand_count":      0,
    "fps":             0.0,
    "fingers_up":      [],
    "gesture_history": [],
}
state_lock = threading.Lock()

HAND_CONNECTIONS = [(c.start, c.end)
                    for c in HandLandmarksConnections.HAND_CONNECTIONS]


def get_finger_states(landmarks, hand_label):
    """Return [Thumb, Index, Middle, Ring, Pinky] True=extended."""
    lm = landmarks

    fingers = []
    if hand_label == "Right":
        fingers.append(lm[4].x < lm[3].x)
    else:
        fingers.append(lm[4].x > lm[3].x)

    for tip_id, pip_id in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        fingers.append(lm[tip_id].y < lm[pip_id].y)

    return fingers


def classify_gesture(fingers, landmarks):
    T, I, M, R, P = fingers
    lm    = landmarks
    count = sum(fingers)

    if count == 0:
        return "Fist", 0.97

    if count == 5:
        return "Open Hand", 0.95

    if T and not I and not M and not R and not P:
        return ("Thumbs Up", 0.96) if lm[4].y < lm[9].y else ("Thumbs Down", 0.94)

    if not T and I and not M and not R and not P:
        return "Pointing", 0.95

    if not T and I and M and not R and not P:
        dx = abs(lm[8].x - lm[12].x)
        if dx < 0.04:
            return "Crossed Fingers", 0.88
        return "Peace", 0.96

    if T and not I and not M and not R and P:
        return "Call Me", 0.95

    if not T and I and M and R and P:
        gap = abs(lm[12].x - lm[16].x)
        if gap > 0.05:
            return "Vulcan", 0.87

    if M and R and P:
        d = math.dist([lm[4].x, lm[4].y], [lm[8].x, lm[8].y])
        if d < 0.06:
            return "OK", 0.90

    names = {1: "Pointing", 2: "Peace", 3: "Three", 4: "Four", 5: "Open Hand"}
    return names.get(count, f"{count} Fingers"), 0.75



def draw_skeleton(frame, landmarks, w, h):
    pts = {i: (int(lm.x * w), int(lm.y * h)) for i, lm in enumerate(landmarks)}
    for s, e in HAND_CONNECTIONS:
        cv2.line(frame, pts[s], pts[e], (0, 255, 180), 4, cv2.LINE_AA)
        cv2.line(frame, pts[s], pts[e], (255, 255, 255), 1, cv2.LINE_AA)
    for i, pt in pts.items():
        r = 7 if i in (4, 8, 12, 16, 20) else 4
        cv2.circle(frame, pt, r + 2, (0, 200, 140), -1)
        cv2.circle(frame, pt, r,     (255, 255, 255), -1)


def draw_hud(frame, gesture, confidence, fps, hand_count):
    h, w = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - 90), (w, h), (10, 10, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    cv2.putText(frame, f"FPS: {fps:.1f}", (14, 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 230, 160), 2, cv2.LINE_AA)

    ht = f"Hands: {hand_count}"
    tw = cv2.getTextSize(ht, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)[0][0]
    cv2.putText(frame, ht, (w - tw - 14, 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 200, 255), 2, cv2.LINE_AA)

    disp = gesture if gesture != "None" else "No Gesture Detected"
    cv2.putText(frame, disp, (14, h - 52),
                cv2.FONT_HERSHEY_DUPLEX, 0.85, (0, 255, 180), 2, cv2.LINE_AA)

    bar_w = int((w - 28) * confidence)
    cv2.rectangle(frame, (14, h - 30), (w - 14, h - 18), (40, 40, 60), -1)
    color = (0, 220, 100) if confidence > 0.8 else (0, 180, 255)
    cv2.rectangle(frame, (14, h - 30), (14 + bar_w, h - 18), color, -1)
    cv2.putText(frame, f"{int(confidence * 100)}%", (w - 48, h - 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1, cv2.LINE_AA)



def generate_frames():
    ensure_model()

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    fps_timer   = time.time()
    frame_count = 0
    current_fps = 0.0
    timestamp   = 0

    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.55,
        min_tracking_confidence=0.55,
    )

    with HandLandmarker.create_from_options(options) as detector:
        while True:
            ret, frame = cap.read()
            if not ret:
                blank = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(blank, "Camera not available", (120, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (80, 80, 80), 2)
                _, buf = cv2.imencode(".jpg", blank)
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
                       buf.tobytes() + b"\r\n")
                time.sleep(0.1)
                continue

            frame = cv2.flip(frame, 1)
            h, w  = frame.shape[:2]

            frame_count += 1
            now = time.time()
            if now - fps_timer >= 1.0:
                current_fps = frame_count / (now - fps_timer)
                frame_count = 0
                fps_timer   = now

            timestamp += 33
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image  = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            result    = detector.detect_for_video(mp_image, timestamp)

            gesture_name = "None"
            confidence   = 0.0
            fingers_up   = []
            hand_count   = len(result.hand_landmarks)

            for idx, (landmarks, handedness_list) in enumerate(
                zip(result.hand_landmarks, result.handedness)
            ):
                hand_label = handedness_list[0].category_name
                draw_skeleton(frame, landmarks, w, h)
                fingers = get_finger_states(landmarks, hand_label)
                g, c    = classify_gesture(fingers, landmarks)
                if idx == 0:
                    gesture_name = g
                    confidence   = c
                    fingers_up   = fingers

            draw_hud(frame, gesture_name, confidence, current_fps, hand_count)

            with state_lock:
                state["gesture"]    = gesture_name
                state["confidence"] = round(confidence, 3)
                state["hand_count"] = hand_count
                state["fps"]        = round(current_fps, 1)
                state["fingers_up"] = fingers_up

                history = state["gesture_history"]
                if gesture_name != "None":
                    if not history or history[-1] != gesture_name:
                        history.append(gesture_name)
                        if len(history) > 8:
                            history.pop(0)

            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" +
                   buf.tobytes() + b"\r\n")

    cap.release()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/status")
def status():
    with state_lock:
        return jsonify(dict(state))


if __name__ == "__main__":
    print("[GestureAI] Starting — open http://localhost:5000")
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
