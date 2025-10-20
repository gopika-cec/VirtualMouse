
# 🖱️ Virtual Mouse

A **gesture-based virtual mouse controller** built with **Python**, **OpenCV**, and **MediaPipe**, enabling users to control mouse movements, clicks, scrolling, volume, and screen brightness using hand gestures captured from a webcam.

---

## 💡 Introduction

The **Virtual Mouse** replaces traditional mouse inputs with **hand gestures** using real-time camera tracking. It leverages **MediaPipe Hands** for landmark detection and **PyAutoGUI** for controlling mouse events, offering a touch-free and interactive computing experience.

The project also includes a **GUI controller** for toggling *Volume* and *Brightness* adjustment modes using simple pinch gestures.

---

## ✨ Features

✅ Control mouse movement with hand gestures  
✅ Left, right, and double-click recognition  
✅ Smooth cursor movement and dragging support  
✅ Scroll using “Thumb Up” gesture  
✅ Adjust **system volume** and **screen brightness** with pinch gestures  
✅ Simple **Tkinter GUI** for mode toggling (Volume / Brightness)  
✅ Works in real time using your webcam  

---

## ⚙️ Installation

### 1️⃣ Clone the repository:

```bash
git clone https://github.com/gopika-cec/VirtualMouse.git
cd VirtualMouse
```

### 2️⃣ Create and activate a virtual environment (optional but recommended):

```bash
python -m venv venv
venv\Scripts\activate    # on Windows
source venv/bin/activate # on macOS/Linux
```

### 3️⃣ Install required dependencies:

```bash
pip install -r requirements.txt
```

If a `requirements.txt` file doesn’t exist, you can manually install:

```bash
pip install opencv-python mediapipe pyautogui numpy comtypes pycaw screen-brightness-control tk
```

---

## ▶️ Usage

Run the main script:

```bash
python virtual_mouse.py
```

A **Tkinter control panel** will open with:

* “Volume Mode” toggle
* “Brightness Mode” toggle
* “Exit” button

Once launched, the webcam feed appears, and gestures are tracked in real-time.

Press **Enter** to exit the camera window.

---

## ✋ Gestures Guide

| Gesture                   | Action                                     |
| ------------------------- | ------------------------------------------ |
| ✌️ V Sign                 | Move cursor                                |
| ☝️ Index Finger           | Left click                                 |
| 🤙 Pinky                  | Right click                                |
| ✊ Fist                    | Click and drag                             |
| 🖐 Palm                   | Release drag                               |
| 👍 Thumb Up               | Scroll up/down                             |
| 🤏 Pinch (Thumb + Index)  | Adjust system volume (Volume Mode)         |
| 🤏 Pinch (Thumb + Middle) | Adjust screen brightness (Brightness Mode) |

---

## 🧩 Dependencies

| Library                     | Purpose                                    |
| --------------------------- | ------------------------------------------ |
| `opencv-python`             | Capture webcam frames & display video feed |
| `mediapipe`                 | Detect and track hand landmarks            |
| `pyautogui`                 | Simulate mouse actions                     |
| `pycaw`                     | Control system volume                      |
| `screen-brightness-control` | Adjust monitor brightness                  |
| `tkinter`                   | Create GUI control panel                   |
| `numpy`                     | Data manipulation and scaling              |
| `comtypes`                  | Interface for Windows audio control        |

---

