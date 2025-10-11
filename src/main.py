import cv2
import mediapipe as mp
import pyautogui
import math
import time
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbc
import numpy as np

# --------- Globals / helpers ----------
gesture_counter = {}
feedback_text = ""
feedback_time = 0
last_gesture = None

def distance(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def getposition(lm, w, h, prev_x, prev_y, smoothening, deadzone=5):
    screen_w, screen_h = pyautogui.size()
    x, y = lm[8]
    frame_x_min, frame_x_max = int(w * 0.2), int(w * 0.8)
    frame_y_min, frame_y_max = int(h * 0.2), int(h * 0.8)

    x = min(max(x, frame_x_min), frame_x_max)
    y = min(max(y, frame_y_min), frame_y_max)

    screen_x = screen_w - ((x - frame_x_min) / (frame_x_max - frame_x_min) * screen_w)
    screen_y = (y - frame_y_min) / (frame_y_max - frame_y_min) * screen_h

    c_x = prev_x + (screen_x - prev_x) / smoothening
    c_y = prev_y + (screen_y - prev_y) / smoothening

    if abs(c_x - prev_x) < deadzone and abs(c_y - prev_y) < deadzone:
        return prev_x, prev_y

    return (c_x, c_y)

# --------- Main ----------
def main():
    global feedback_text, feedback_time, last_gesture

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: could not open the camera")
        return

    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands

    pyautogui.FAILSAFE = False
    prev_x, prev_y = 0, 0
    smoothening = 3

    scroll_start_y = None
    pinch_active = False
    dragging = False

    # volume/brightness support
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    min_vol, max_vol, _ = volume.GetVolumeRange()

    # ----- New pinch variables -----
    volume_pinch_active = False
    brightness_pinch_active = False
    volume_start_y = 0
    brightness_start_y = 0
    volume_level_start = volume.GetMasterVolumeLevel()
    try:
        brightness_level_start = sbc.get_brightness(display=0)[0]
    except:
        brightness_level_start = 50

    with mp_hands.Hands(
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    ) as hands:

        while True:
            ok, frame = cap.read()
            if not ok:
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame.flags.writeable = False
            results = hands.process(rgb_frame)
            rgb_frame.flags.writeable = True

            on_screen_texts = []

            if results.multi_hand_landmarks:
                for hand_index, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    h, w, _ = frame.shape
                    lm = [(int(l.x * w), int(l.y * h)) for l in hand_landmarks.landmark]

                    # detect fingers
                    fingers = []
                    handedness = results.multi_handedness[hand_index].classification[0].label
                    if handedness == 'Right':
                        thumb_extend = lm[4][0] < lm[3][0]
                    else:
                        thumb_extend = lm[4][0] > lm[3][0]
                    fingers.append(1 if thumb_extend else 0)

                    tips = [8, 12, 16, 20]
                    lower_joints = [6, 10, 14, 18]
                    for tip, joint in zip(tips, lower_joints):
                        fingers.append(1 if lm[tip][1] < lm[joint][1] else 0)

                    gesture = "UNKNOWN"
                    if fingers == [0, 0, 0, 0, 0]:
                        gesture = "FIST"
                    elif fingers == [1, 1, 1, 1, 1]:
                        gesture = "PALM"
                    elif fingers == [0, 1, 0, 0, 0] and sum(fingers) == 1:
                        gesture = "INDEX"
                    elif fingers == [0, 1, 1, 0, 0]:
                        gesture = "V SIGN"
                    elif fingers == [0, 0, 0, 0, 1]:
                        gesture = "PINKY"
                    elif fingers == [1, 0, 0, 0, 0]:
                        gesture = "THUMB UP"

                    # Click gestures
                    if gesture == "INDEX" and gesture != last_gesture:
                        pyautogui.leftClick()
                        feedback_text = "Left Click"
                        feedback_time = time.time()

                    if gesture == "PINKY" and gesture != last_gesture:
                        pyautogui.rightClick()
                        feedback_text = "Right Click"
                        feedback_time = time.time()

                    # V SIGN for moving mouse
                    if gesture == "V SIGN":
                        curr_x, curr_y = getposition(lm, w, h, prev_x, prev_y, smoothening)
                        pyautogui.moveTo(curr_x, curr_y, duration=0)
                        prev_x, prev_y = curr_x, curr_y

                        if distance(lm[8], lm[12]) < 40:
                            if not pinch_active:
                                pyautogui.doubleClick()
                                pinch_active = True
                                feedback_text = "Double Click"
                                feedback_time = time.time()
                        else:
                            pinch_active = False

                    # Dragging with fist
                    elif gesture == "FIST":
                        if not dragging:
                            pyautogui.mouseDown()
                            dragging = True
                            feedback_text = "Dragging"
                            feedback_time = time.time()
                        curr_x, curr_y = getposition(lm, w, h, prev_x, prev_y, smoothening, deadzone=0)
                        pyautogui.moveTo(curr_x, curr_y, duration=0)
                        prev_x, prev_y = curr_x, curr_y

                    elif gesture == "PALM" and dragging:
                        pyautogui.mouseUp()
                        dragging = False
                        feedback_text = "Dropped"
                        feedback_time = time.time()

                    # Scroll with thumb up
                    if gesture == "THUMB UP" and not dragging:
                        if scroll_start_y is None:
                            scroll_start_y = lm[8][1]
                        dy = scroll_start_y - lm[8][1]
                        if abs(dy) > 5:
                            pyautogui.scroll(dy * 2)
                            scroll_start_y = lm[8][1]
                    else:
                        if gesture != "THUMB UP":
                            scroll_start_y = None

                    # ----------- VOLUME (Pinch activate + Move Y) -------------
                    vol_pinch_dist = distance(lm[4], lm[8])
                    if vol_pinch_dist < 40:
                        if not volume_pinch_active:
                            volume_pinch_active = True
                            volume_start_y = (lm[4][1] + lm[8][1]) / 2
                            volume_level_start = volume.GetMasterVolumeLevel()
                        else:
                            current_y = (lm[4][1] + lm[8][1]) / 2
                            delta = volume_start_y - current_y
                            delta_scaled = np.interp(delta, [-200, 200], [-10, 10])
                            new_level = np.clip(volume_level_start + delta_scaled, min_vol, max_vol)
                            volume.SetMasterVolumeLevel(new_level, None)
                            vol_percent = int(np.interp(new_level, [min_vol, max_vol], [0, 100]))
                            on_screen_texts.append((f"Volume: {vol_percent}%", (50, 120), (255, 0, 0)))
                    else:
                        volume_pinch_active = False

                    # ----------- BRIGHTNESS (Pinch activate + Move Y) -------------
                    bright_pinch_dist = distance(lm[4], lm[12])
                    if bright_pinch_dist < 40:
                        if not brightness_pinch_active:
                            brightness_pinch_active = True
                            brightness_start_y = (lm[4][1] + lm[12][1]) / 2
                            try:
                                brightness_level_start = sbc.get_brightness(display=0)[0]
                            except:
                                brightness_level_start = 50
                        else:
                            current_y = (lm[4][1] + lm[12][1]) / 2
                            delta = brightness_start_y - current_y
                            delta_scaled = np.interp(delta, [-200, 200], [-100, 100])
                            new_bright = np.clip(brightness_level_start + delta_scaled, 0, 100)
                            try:
                                sbc.set_brightness(int(new_bright))
                            except Exception:
                                pass
                            on_screen_texts.append((f"Brightness: {int(new_bright)}%", (50, 160), (0, 255, 255)))
                    else:
                        brightness_pinch_active = False

                    last_gesture = gesture

            else:
                prev_x, prev_y = pyautogui.position()
                if dragging:
                    pyautogui.mouseUp()
                    dragging = False

            # ROI box
            h, w, _ = frame.shape
            frame_x_min, frame_x_max = int(w * 0.2), int(w * 0.8)
            frame_y_min, frame_y_max = int(h * 0.2), int(h * 0.8)
            cv2.rectangle(frame, (frame_x_min, frame_y_min), (frame_x_max, frame_y_max), (0, 255, 0), 2)

            # Flip for mirror view
            frame = cv2.flip(frame, 1)

            # Feedback text
            if feedback_text and time.time() - feedback_time < 2.0:
                cv2.putText(frame, feedback_text, (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2,
                            cv2.LINE_AA)

            for txt, pos, color in on_screen_texts:
                cv2.putText(frame, txt, pos, cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)

            cv2.imshow("Gesture Controller", frame)

            if cv2.waitKey(2) & 0xFF == 13:  # press Enter to exit
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
