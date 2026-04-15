#  GestureAI — Hand Gesture Recognition

A real-time hand gesture recognition web app built with **OpenCV**, **MediaPipe**, and **Flask**.

---

##  Features

- Real-time hand landmark detection via webcam
- Recognises 10 gestures: Peace, Thumbs Up/Down, Fist, Open Hand, Pointing, Call Me, Crossed Fingers, Vulcan, OK
- Live confidence score per gesture
- Finger-state visualiser (per digit)
- Gesture history log
- FPS counter
- Sleek cyberpunk dark-mode UI

---

##  Project Structure

gesture_app/
├── app.py                  # Flask backend + OpenCV + MediaPipe logic
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # Frontend UI (HTML/CSS/JS)
└── README.md

---

##  Setup & Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
python app.py
```

### 3. Open in browser

```
http://localhost:5000
```

Make sure your webcam is connected and accessible.

---

##  Supported Gestures

| Gesture       | Description                          |
|---------------|--------------------------------------|
| ✌️ Peace       | Index + Middle fingers extended       |
| 👍 Thumbs Up  | Thumb up, all fingers closed          |
| 👎 Thumbs Down| Thumb down, all fingers closed        |
| ✊ Fist       | All fingers closed                    |
| 🖐 Open Hand  | All 5 fingers extended                |
| ☝️ Pointing   | Index finger only extended            |
| 🤙 Call Me    | Thumb + Pinky extended                |
| 🤞 Crossed    | Index + Middle close together         |
| 🖖 Vulcan     | All fingers up with gap in middle     |
| 👌 OK         | Thumb + Index touching, others up     |

---

##  Technical Architecture

```
Webcam → OpenCV capture → MediaPipe Hands
       → Landmark extraction (21 points)
       → Finger state classification
       → Gesture name + confidence
       → Frame annotation (HUD overlay)
       → MJPEG stream → Flask /video_feed
       → JSON status → Flask /status
       → Browser UI polls /status every 200ms
```

---

##  Tech Stack

- **Backend**: Python, Flask, OpenCV, MediaPipe, NumPy
- **Frontend**: Vanilla HTML/CSS/JS, Google Fonts (Syne + Space Mono)
- **Streaming**: MJPEG multipart stream over HTTP

---

##  Notes

- Works best with good lighting and a clear background
- Supports up to 2 hands simultaneously
- Only the first detected hand is used for gesture classification
- Camera index defaults to `0`; change `cv2.VideoCapture(0)` if needed
