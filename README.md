# AirMouse

AirMouse is an AI-powered virtual mouse that lets you control your computer cursor using hand gestures.

Built with:
- Python
- OpenCV
- MediaPipe

## Features

- AI hand tracking
- 21 hand landmarks
- Real-time webcam detection

## Getting Started

Clone the repository:

```bash
git clone https://github.com/SrijayanthS/AirMouse.git
cd AirMouse
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Download the hand tracking model:

```bash
python download_model.py
```

Run AirMouse:

```bash
python app.py
```

## Roadmap

- [x] Camera integration
- [x] AI hand tracking
- [x] Cursor movement
- [x] Cursor smoothing
- [x] Left click
- [x] Right click
- [x] Drag and drop
- [x] Scrolling
- [ ] Custom gestures

---

Built by **Srijayanth Saseendran**
