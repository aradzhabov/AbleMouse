import time
import cv2
import mediapipe as mp
import pyautogui
import numpy as np

# ============ MAIN SETTINGS ============
pyautogui.FAILSAFE = False  # Disable edge safety

# ToDo-note !!On Mac OS there might be a nuance... if the option in the Accessibility menu is enabled,
# then you need to select the external web camera for head control there, and then cv2.VideoCapture(0) will start
# reading from the external camera, and if no external camera is connected, then from the built-in one
camera = 0  # 0 built-in camera, 1,2 - could be another number - this is an external camera

# Enable/disable cursor control via camera
bln_cam_mouse_control = False

# FPS display control
bln_display_fps = False

# Settings for skipping minor movements
bln_do_not_move_cursor_if_xy_move_within_threshold = False
SKIP_X_THRESHOLD = 0.001  # 0.0025
SKIP_Y_THRESHOLD = 0.001  # 0.0025

# Centering by nose
bln_nose_center = True

# Parameters for displaying the last action
LAST_ACTION_DISPLAY_TIME = 3.0  # Time to display the last action (in seconds)

# ============ EYE AND MOUTH CLOSURE TRACKING SETTINGS ============
# Time in seconds for which eyes need to be closed to switch camera control mode
LEFT_EYE_CLOSE_TIME_THRESHOLD = 1.5  # sec

# Time in seconds for which the right eye needs to be closed for double click
RIGHT_EYE_RIGHT_CLICK_TIME_THRESHOLD = 1.0  # sec

# Time in seconds for which the mouth needs to be open for right click
MOUTH_OPEN_RIGHT_CLICK_TIME_THRESHOLD = 1.0  # sec

# Cooldowns after actions in sec.
EYE_SWITCH_COOLDOWN_DURATION = 1.0
RIGHT_EYE_RIGHT_CLICK_COOLDOWN_DURATION = 1.0
MOUTH_RIGHT_CLICK_COOLDOWN_DURATION = 1.0
MOUTH_CLICK_COOLDOWN_DURATION = 0.5 # also helps to not click many times when mouse is open

# Thresholds for determining closed eyes
EYE_CLOSE_THRESHOLD = 0.005 #0.004

# Threshold for determining open mouth
MOUTH_OPEN_THRESHOLD = 0.002

# ============ FILTERING AND JITTER REDUCTION SETTINGS ============
FILTER_METHOD = 'smooth'  # 'smooth' or 'ToDO kalman'

# Exponential smoothing parameters (if 'smooth' method is selected)
SMOOTHING_ALPHA = 0.5  # Smoothing coefficient (0.0 - full smoothing, 1.0 - no smoothing)

# Movement threshold parameters
MOVE_THRESHOLD_PIXELS = 2  # Minimum movement in pixels to update cursor position
USE_MOVEMENT_THRESHOLD = True  # Enable/disable movement threshold

# Median filter parameters
USE_MEDIAN_FILTER = True
MEDIAN_FILTER_WINDOW = 10  # Window size for median filter

# ============ END OF MAIN SETTINGS ============

# ============ PROGRAM WORKING VARIABLES ============
#       used to record the time when we processed last frame
prev_frame_time = 0
#       used to record the time at which we processed current frame
new_frame_time = 0

# Time when left eyes were closed
left_eye_closed_start_time = None

# Time when right eye was closed
right_eye_closed_start_time = None

# Time when mouth was open
mouth_open_start_time = None

# Flag to prevent multiple switches while holding eyes closed
eye_switch_cooldown = False
eye_switch_cooldown_time = 0

# Flag to track eye and mouth state in the previous frame
prev_left_eye_closed = False
prev_right_eye_closed = False
prev_mouth_open = False

# Flag to prevent repeated double click while holding eye closed
right_eye_right_click_cooldown = False
right_eye_right_click_cooldown_time = 0

# Flag to prevent repeated right click while holding mouth open
mouth_right_click_cooldown = False
mouth_right_click_cooldown_time = 0

# Flag to prevent repeated regular click while holding mouth open
mouth_click_cooldown = False
mouth_click_cooldown_time = 0

# Variables for storing position history
position_history_x = []
position_history_y = []

# Variables for smoothed positions
smoothed_x = None
smoothed_y = None

# ============ VARIABLE FOR STORING LAST ACTION ============
last_action = ""
last_action_time = 0

# ============ END OF PROGRAM WORKING VARIABLES ============

cap = cv2.VideoCapture(camera)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

# ToDo on mac if you don't set the following values,
# then frame_w=1920 frame_h=1080,
# but if you set 320x240, then for some reason frame_w=640 frame_h=480
# cap.set(cv2.CAP_PROP_FRAME_WIDTH,320)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT,240)


face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
screen_w, screen_h = pyautogui.size()
x_screen_center = screen_w / 2
y_screen_center = screen_h / 2

lx = 0.4
rx = 0.57
lrx = (lx + rx) / 2
screen_w_lambdax = screen_w / abs(lx - rx)
halfx = screen_w / 2

uy = 0.65
ly = 0.79
ulx = (uy + ly) / 2
screen_h_lambday = screen_h / abs(uy - ly)
halfy = screen_h / 2

previous_x = 0
previous_y = 0

previous_x_threshold = 0
previous_y_threshold = 0


# ============ FILTERING FUNCTIONS ============
def apply_median_filter(x, y, history_x, history_y, window_size):
    """Applies median filter to current coordinates"""
    history_x.append(x)
    history_y.append(y)

    if len(history_x) > window_size:
        history_x.pop(0)
        history_y.pop(0)

    if len(history_x) == window_size:
        # Create copies for sorting
        sorted_x = sorted(history_x.copy())
        sorted_y = sorted(history_y.copy())

        # Return median values
        median_x = sorted_x[window_size // 2]
        median_y = sorted_y[window_size // 2]
        return median_x, median_y

    return x, y


def apply_exponential_smoothing(current_x, current_y, smoothed_x, smoothed_y, alpha):
    """Applies exponential smoothing"""
    if smoothed_x is None or smoothed_y is None:
        return current_x, current_y

    new_x = alpha * current_x + (1 - alpha) * smoothed_x
    new_y = alpha * current_y + (1 - alpha) * smoothed_y
    return new_x, new_y


def should_update_cursor(current_x, current_y, prev_x, prev_y, threshold):
    """Checks if movement is sufficient to update cursor"""
    if not USE_MOVEMENT_THRESHOLD:
        return True

    distance = np.sqrt((current_x - prev_x) ** 2 + (current_y - prev_y) ** 2)
    return distance > threshold


def set_last_action(action):
    """Sets the last performed action and time"""
    global last_action, last_action_time
    last_action = action
    last_action_time = time.time()


# ============ END OF FILTERING FUNCTIONS ============

while True:
    ret, frame = cap.read()
    # if frame is read correctly ret is True
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # flip is needed just to handle mirroring
    frame = cv2.flip(frame, 1)

    if bln_display_fps:
        # Calculating the fps
        new_frame_time = time.time()
        # fps will be number of frame processed in given time frame
        # since their will be most of time error of 0.001 second
        # we will be subtracting it to get more accurate result
        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time
        # converting the fps into integer
        fps = int(fps)
        # converting the fps to string so that we can display it on frame
        # by using putText function
        fps = str(fps)
        # putting the FPS count on the frame
        cv2.putText(frame, fps, (7, 70), cv2.FONT_HERSHEY_SIMPLEX, 3, (100, 255, 0), 3, cv2.LINE_AA)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    output = face_mesh.process(rgb_frame)
    # if there were multiple faces, the first one would be here landmark_points[0], second landmark_points[1] ...
    landmark_points = output.multi_face_landmarks
    # width and height are needed to correctly set the point in pixels because landmark.x/y are relative units,
    # but since the width (video from camera) of the screen can be different, to draw the point correctly you need to consider frame_h, frame_w
    frame_h, frame_w, _ = frame.shape
    # print(f"frame_w={frame_w} frame_h={frame_h}")

    if landmark_points:
        bln_left_eye_closed = False
        bln_right_eye_closed = False
        bln_mouth_open = False

        landmarks = landmark_points[0].landmark

        right = [landmarks[386], landmarks[374]]
        for landmark in right:
            x = int(landmark.x * frame_w)
            y = int(landmark.y * frame_h)
            # if we didn't do in enumerate(landmarks[474:478]), we would see all points on the face
            cv2.circle(frame, (x, y), 3, (0, 255, 0))
            if (right[1].y - right[0].y) < EYE_CLOSE_THRESHOLD:
                bln_right_eye_closed = True

        left = [landmarks[145], landmarks[159]]
        for landmark in left:
            x = int(landmark.x * frame_w)
            y = int(landmark.y * frame_h)
            cv2.circle(frame, (x, y), 3, (255, 0, 0))
            if (left[0].y - left[1].y) < EYE_CLOSE_THRESHOLD:
                bln_left_eye_closed = True

        # ============ MOUTH OPENING PROCESSING ============
        thickness = 0  # -1 to fill the circle
        lip_upper = landmarks[13]
        x = int(lip_upper.x * frame_w)
        y = int(lip_upper.y * frame_h)
        cv2.circle(frame, (x, y), 3, (0, 0, 255), thickness)  # 00255=red

        lip_down = landmarks[14]
        x = int(lip_down.x * frame_w)
        y = int(lip_down.y * frame_h)
        cv2.circle(frame, (x, y), 3, (0, 0, 255), thickness)

        lip_distance_diff = lip_down.y - lip_upper.y
        # print(f"lip_distance_diff:{lip_distance_diff}")
        if lip_distance_diff > MOUTH_OPEN_THRESHOLD:
            bln_mouth_open = True

        # ============ LEFT EYE CLOSURE PROCESSING  ============
        current_time = time.time()
        left_eye_closed = bln_left_eye_closed
        right_eye_closed = bln_right_eye_closed
        mouth_open = bln_mouth_open

        # Check mode switch cooldown
        if eye_switch_cooldown and (current_time - eye_switch_cooldown_time) > EYE_SWITCH_COOLDOWN_DURATION:
            eye_switch_cooldown = False

        # Check double click cooldown
        if right_eye_right_click_cooldown and (
                current_time - right_eye_right_click_cooldown_time) > RIGHT_EYE_RIGHT_CLICK_COOLDOWN_DURATION:
            right_eye_right_click_cooldown = False

        # Check mouth right click cooldown
        if mouth_right_click_cooldown and (
                current_time - mouth_right_click_cooldown_time) > MOUTH_RIGHT_CLICK_COOLDOWN_DURATION:
            mouth_right_click_cooldown = False

        # Check mouth regular click cooldown
        if mouth_click_cooldown and (
                current_time - mouth_click_cooldown_time) > MOUTH_CLICK_COOLDOWN_DURATION:
            mouth_click_cooldown = False

        # Logic for left eye (mode switching)
        if left_eye_closed:
            # If left eye just closed, start timing
            if not prev_left_eye_closed and not eye_switch_cooldown:
                left_eye_closed_start_time = current_time

            # If left eye has been closed for some time, show progress
            if left_eye_closed_start_time is not None and not eye_switch_cooldown:
                elapsed_time = current_time - left_eye_closed_start_time

                # Display progress
                progress_width = int((elapsed_time / LEFT_EYE_CLOSE_TIME_THRESHOLD) * 200)
                cv2.rectangle(frame, (10, 50), (10 + progress_width, 70), (0, 255, 0), -1)
                cv2.rectangle(frame, (10, 50), (210, 70), (255, 255, 255), 1)
                cv2.putText(frame, "MOUSE CONTROL ON/OFF PROGRESS ...",
                            (220, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                # Check if threshold is reached
                if elapsed_time >= LEFT_EYE_CLOSE_TIME_THRESHOLD:
                    # Toggle cursor control mode
                    bln_cam_mouse_control = not bln_cam_mouse_control
                    left_eye_closed_start_time = None
                    eye_switch_cooldown = True
                    eye_switch_cooldown_time = current_time

                    # Set last action
                    status = "ENABLED" if bln_cam_mouse_control else "DISABLED"
                    action_text = f"Mouse control {status}"
                    set_last_action(action_text)

                    # Show switch notification
                    cv2.putText(frame, f"Mouse control {status}!", (frame_w // 2 - 100, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if bln_cam_mouse_control else (0, 0, 255), 2)

                    print(f"Mouse control {status}")
        else:
            # Left eye open - reset timer
            left_eye_closed_start_time = None

        # ============ RIGHT EYE CLOSURE PROCESSING ============
        if right_eye_closed:
            # If right eye just closed, start timing
            if not prev_right_eye_closed and not right_eye_right_click_cooldown:
                right_eye_closed_start_time = current_time

            # If right eye has been closed for some time, show progress
            if right_eye_closed_start_time is not None and not right_eye_right_click_cooldown:
                elapsed_time = current_time - right_eye_closed_start_time

                # Display progress
                progress_width = int((elapsed_time / RIGHT_EYE_RIGHT_CLICK_TIME_THRESHOLD) * 200)
                cv2.rectangle(frame, (10, 120), (10 + progress_width, 140), (255, 0, 0), -1)
                cv2.rectangle(frame, (10, 120), (210, 140), (255, 255, 255), 1)
                cv2.putText(frame, f"RIGHT CLICK PROGRESS ...",
                            (220, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

                # Check if threshold is reached
                if elapsed_time >= RIGHT_EYE_RIGHT_CLICK_TIME_THRESHOLD:
                    # Perform right click
                    if bln_cam_mouse_control:
                        pyautogui.rightClick()
                        action_text = "Right click (right eye)"
                        set_last_action(action_text)
                        print("Right click\n performed (right eye)")
                        # Pause after right click so menu doesn't disappear
                        pyautogui.sleep(0.5)

                    # Reset timer and set cooldown
                    right_eye_closed_start_time = None
                    right_eye_right_click_cooldown = True
                    right_eye_right_click_cooldown_time = current_time
        else:
            # Right eye open - reset timer
            right_eye_closed_start_time = None

        # ============ MOUTH OPENING PROCESSING FOR REGULAR AND RIGHT CLICK ============
        if mouth_open:
            # If mouth just opened, start timing
            if not prev_mouth_open:
                mouth_open_start_time = current_time
                cv2.putText(frame, "Mouth open - timing started", (10, 170),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

                # AT THE MOMENT OF MOUTH OPENING - check if we can make a regular click
                if bln_cam_mouse_control and not mouth_click_cooldown:
                    # Make left click only at the start of mouth opening
                    pyautogui.click()
                    action_text = "Left click"
                    set_last_action(action_text)
                    print("Click performed at mouth open start")
                    mouth_click_cooldown = True
                    mouth_click_cooldown_time = current_time

            # If mouth has been open for some time, show progress for right click
            if mouth_open_start_time is not None and not mouth_right_click_cooldown:
                elapsed_time = current_time - mouth_open_start_time

                # Display progress for right click
                progress_width = int((elapsed_time / MOUTH_OPEN_RIGHT_CLICK_TIME_THRESHOLD) * 200)
                cv2.rectangle(frame, (10, 190), (10 + progress_width, 210), (255, 255, 0), -1)
                cv2.rectangle(frame, (10, 190), (210, 210), (255, 255, 255), 1)
                cv2.putText(frame, "RIGHT CLICK PROGRESS ...", (220, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

                # Check if threshold for right click is reached
                if elapsed_time >= MOUTH_OPEN_RIGHT_CLICK_TIME_THRESHOLD:
                    # Perform right click
                    if bln_cam_mouse_control:
                        pyautogui.rightClick()
                        action_text = "Right click (mouth open hold)"
                        set_last_action(action_text)
                        print("Right click performed (mouth open hold)")
                        # Pause after right click so menu doesn't disappear
                        pyautogui.sleep(0.5)

                    # Reset timer and set cooldown
                    mouth_open_start_time = None
                    mouth_right_click_cooldown = True
                    mouth_right_click_cooldown_time = current_time
        else:
            # Mouth closed - reset timer for right click
            mouth_open_start_time = None

        # Save eye and mouth state for next frame
        prev_left_eye_closed = left_eye_closed
        prev_right_eye_closed = right_eye_closed
        prev_mouth_open = mouth_open
        # ============ END OF EYE CLOSURE AND MOUTH OPENING PROCESSING ============

        nose_landmark = landmarks[94]  # 5#1#19 - nose
        # print(nose_landmark)

        if bln_do_not_move_cursor_if_xy_move_within_threshold:
            skip = False
            if (abs(nose_landmark.x - previous_x_threshold) < SKIP_X_THRESHOLD) & \
                    (abs(nose_landmark.y - previous_y_threshold) < SKIP_Y_THRESHOLD):
                skip = True
            previous_x_threshold = nose_landmark.x
            previous_y_threshold = nose_landmark.y
            if skip:
                # print("skip")
                continue

        x = int(nose_landmark.x * frame_w)
        y = int(nose_landmark.y * frame_h)
        cv2.circle(frame, (x, y), 7, (0, 255, 0))
        # don't forget that there is the width of the camera video frame and the width of the computer screen,
        # to not limit mouse movement only within the camera frame, we need logic that considers
        # screen width and height

        screen_x = (nose_landmark.x - 0.5) * screen_w_lambdax + halfx
        if bln_nose_center:
            screen_y = (nose_landmark.y - 0.5) * screen_h_lambday + halfy
        else:
            screen_y = (nose_landmark.y - 0.7) * screen_h_lambday + halfy

        if screen_x > screen_w:
            screen_x = screen_w - 5
        if screen_x < 0:
            screen_x = 5
        if screen_y > screen_h:
            screen_y = screen_h - 5
        if screen_y < 0:
            screen_y = 5

        # ============ APPLYING FILTERS FOR JITTER REDUCTION ============
        raw_screen_x, raw_screen_y = screen_x, screen_y

        # 1. Apply median filter
        if USE_MEDIAN_FILTER:
            screen_x, screen_y = apply_median_filter(screen_x, screen_y,
                                                     position_history_x,
                                                     position_history_y,
                                                     MEDIAN_FILTER_WINDOW)

        # 2. Apply selected smoothing method
        if FILTER_METHOD == 'smooth':
            screen_x, screen_y = apply_exponential_smoothing(screen_x, screen_y,
                                                             smoothed_x, smoothed_y,
                                                             SMOOTHING_ALPHA)
            smoothed_x, smoothed_y = screen_x, screen_y

        # 3. Check movement threshold
        if should_update_cursor(screen_x, screen_y, previous_x, previous_y, MOVE_THRESHOLD_PIXELS):
            final_x, final_y = screen_x, screen_y
        else:
            final_x, final_y = previous_x, previous_y
        # ============ END OF FILTER APPLICATION ============

        if bln_cam_mouse_control:
            # ToDo-note !!_pause=False Significantly (at least x3 times) increases operation speed
            # _pause You need to set the global variable pyautogui.PAUSE:float - delay in seconds between operations (e.g. 0.01) or completely disable the delay pyautogui.moveTo(x,y,_pause=False).
            # or you can do without _pause
            pyautogui.moveTo(final_x, final_y, _pause=False)

        # Update previous positions
        previous_x = final_x
        previous_y = final_y

        # Just a debug circle showing the center of the camera frame
        cv2.circle(frame, (int(frame_w / 2), int(frame_h / 2)), 31, (0, 128, 0), 5)

        # Display cursor control status
        control_status = "MOUSE CONTROL: ON" if bln_cam_mouse_control else "MOUSE CONTROL: OFF"
        status_color = (0, 255, 0) if bln_cam_mouse_control else (0, 0, 255)
        cv2.putText(frame, control_status, (frame_w - 250, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        # Display last performed action
        current_time = time.time()
        if last_action and (current_time - last_action_time) < LAST_ACTION_DISPLAY_TIME:
            # Display last action below the Mouse control label
            cv2.putText(frame, f"Last action: {last_action}", (frame_w - 500, frame_h - 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow('Gagarin Data Labs -> AbleMouse AI edition', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
cap.release()