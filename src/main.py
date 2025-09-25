import cv2
import mediapipe as mp
import pyautogui
import math
import time
#import datetime


gesture_counter={}
feedback_text=""
feedback_time = 0
last_gesture = None


def show_feedback(frame):
    global feedback_text, feedback_time
    if feedback_text and time.time() - feedback_time < 5:
        cv2.putText(frame, feedback_text, (50,50),cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,(0,255,0),3,cv2.LINE_AA)
        


def distance(p1,p2):
    print(math.hypot(p2[0]-p1[0], p2[1]-p1[1]))
    return math.hypot(p2[0]-p1[0], p2[1]-p1[1])


def getposition(lm,w,h,prev_x,prev_y,smoothening,deadzone = 5):
    screen_w, screen_h = pyautogui.size()
    x, y = lm[8]
    frame_x_min, frame_x_max = int(w*0.2), int(w*0.8)
    frame_y_min, frame_y_max = int(h*0.2), int(h*0.8)

    # Clamp values inside ROI
    x = min(max(x, frame_x_min), frame_x_max)
    y = min(max(y, frame_y_min), frame_y_max)

    screen_x = screen_w - ((x - frame_x_min) / (frame_x_max - frame_x_min) * screen_w)
    screen_y = (y - frame_y_min) / (frame_y_max - frame_y_min) * screen_h

    c_x = prev_x + (screen_x-prev_x)/ smoothening
    c_y = prev_y +(screen_y- prev_y)/smoothening

    if abs(c_x - prev_x)< deadzone  and abs(c_y-prev_y) < deadzone:
        return prev_x, prev_y

    return(c_x,c_y)

                          

def main():
    
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("ERROR: could not open the camera")
        return
    

    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands

    pyautogui.FAILSAFE= False
    prev_x, prev_y =0,0
    smoothening = 3


    scroll_start_y = None
    pinch_active = False
    scrolling = False
    dragging = False

    with mp_hands.Hands (
        max_num_hands = 2,
        min_detection_confidence = 0.7,
        min_tracking_confidence =0.5 ) as hands:

        while True:
            ok, frame = cap.read()
            if not ok: 
                continue

            

            rgb_frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

            rgb_frame.flags.writeable = False
            results = hands.process(rgb_frame)
            rgb_frame.flags.writeable = True

            if results.multi_hand_landmarks:
                for hand_index, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    mp_drawing.draw_landmarks(frame,hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    h,w , _ = frame.shape
                    lm = [(int(l.x*w), int(l.y *h)) for l in hand_landmarks.landmark]

                    fingers =[]

                    handedness = results.multi_handedness[hand_index].classification[0].label #left or right
                    if handedness =='Right':
                        thumb_extend = lm[4][0] < lm[3][0]
                    else:
                        thumb_extend = lm[4][0] > lm[3][0]
                    
                    fingers.append(1 if thumb_extend else 0)
                    
                    tips =[8,12,16,20]
                    lower_joints =[6,10,14,18]
                    for tip, joint in zip(tips,lower_joints):
                        fingers.append(1 if lm[tip][1] < lm[joint][1] else 0) #y value 0 at top
                        
                    #print(f"Fingers: {fingers}")

                    gesture = "UNKNOWN"
                    if fingers ==[0,0,0,0,0]:
                        gesture= "FIST"
                    elif fingers ==[1,1,1,1,1]:
                        gesture = "PALM"
                    elif fingers ==[0,1,0,0,0] and sum(fingers) ==1:
                        gesture= "INDEX"
                    elif fingers ==[0,1,1,0,0]:
                        gesture = "V SIGN"
                    elif fingers ==[0,0,0,0,1]:
                        gesture = "PINKY"
                    elif fingers ==[1,0,0,0,0]:
                        gesture = "THUMB UP"
                    elif fingers ==[0,1,1,1,0]:
                        gesture = "THREEUP"
                     
                    show_feedback(frame)

                    # ?  MAIN ACTIONS -------------------------------------------

                    if gesture == "V SIGN":
                        curr_x, curr_y = getposition(lm,w,h,prev_x,prev_y,smoothening)
                        pyautogui.moveTo(curr_x,curr_y,duration=0)
                        prev_x, prev_y = curr_x,curr_y

                        if distance(lm[8],lm[12]) < 24:
                            if not pinch_active:
                                pyautogui.doubleClick()
                                pinch_active= True
                        else:
                            pinch_active = False
                    
                    elif gesture == "INDEX" and gesture != last_gesture:
                        pyautogui.leftClick()
                    
                    elif gesture == "PINKY" and gesture != last_gesture:
                        pyautogui.rightClick()
                    

                    elif gesture == "FIST":
                       

                        if not dragging:
                            pyautogui.mouseDown()
                            dragging= True

                        curr_x,curr_y = getposition(lm,w,h,prev_x,prev_y,smoothening,deadzone=0)
                        pyautogui.moveTo(curr_x,curr_y,duration=0)
                        prev_x,prev_y=curr_x,curr_y
                        
                    elif gesture == "PALM" and dragging:
                        pyautogui.mouseUp()
                        dragging = False


                    #? ---- SCROLL -----
                    elif gesture == "THUMB UP":
                        if scroll_start_y is None:
                            scroll_start_y = lm[8][1]
                        dy = scroll_start_y - lm[8][1]
                        if abs(dy) > 5:
                            pyautogui.scroll(dy*2)
                            scroll_start_y = lm[8][1]
                    
                    else:
                        scroll_start_y = None
                    

                    # ? ---- DRAGGING and drop ---------

                    last_gesture = gesture
                    print(f"Gesture: {gesture}, Fingers: {fingers} {dragging}")
                    

            else: 
                prev_x,prev_y = pyautogui.position()


            frame = cv2.flip(frame,1)
            cv2.imshow("Gesture Controller",frame)

            if cv2.waitKey(2) & 0xFF == 13:
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
