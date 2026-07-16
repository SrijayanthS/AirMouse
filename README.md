# AirMouse

AirMouse is an AI-powered virtual mouse that lets you control your computer using hand gestures.

## Built With

- Python
- OpenCV
- MediaPipe Tasks API
- PyAutoGUI
- Quartz (macOS)

## Features

- AI hand tracking
- Cursor movement
- Cursor smoothing
- Left click
- Right click
- Native macOS double click
- Scrolling
- Pause / Resume
- Drag & Drop *(Experimental)*

## Getting Started

```bash
git clone https://github.com/SrijayanthS/AirMouse.git
cd AirMouse

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python download_model.py
python app.py
```

## Roadmap

- [x] Hand tracking
- [x] Mouse controls
- [x] Scrolling
- [ ] Custom gestures
- [ ] Standalone desktop app

---

Built by **Srijayanth Saseendran**
