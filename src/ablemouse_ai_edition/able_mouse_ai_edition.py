import time
import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import socket
import json
import os
import sys

# ============ LOAD CONFIGURATION ============
def load_config():
    """Load configuration from JSON file"""

    def get_config_path():
        # Если запущено как скомпилированный EXE
        if getattr(sys, 'frozen', False):
            # sys.executable — это полный путь к вашему .exe файлу
            base_path = os.path.dirname(sys.executable)
        else:
            # Обычный запуск .py скрипта
            base_path = os.path.dirname(os.path.abspath(__file__))

        return os.path.join(base_path, 'able_mouse_ai_edition_config.json')


    config_path = get_config_path()

    if not os.path.exists(config_path):
        print(f"Config file not found at {config_path}. Using default settings.")
        return get_default_config()

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("Configuration loaded successfully from config.json")
        return config
    except Exception as e:
        print(f"Error loading config.json: {e}. Using default settings.")
        return get_default_config()


def get_default_config():
    """Return default configuration if JSON file is missing"""
    return {
        "communication": {
            "use_menu_system": False,
            "menu_host": "localhost",
            "menu_port": 12345
        },
        "main": {
            "camera": 0,
            "cam_mouse_control": False,
            "display_fps": False,
            "do_not_move_cursor_if_xy_move_within_threshold": False,
            "skip_x_threshold": 0.001,
            "skip_y_threshold": 0.001,
            "nose_center": True,
            "last_action_display_time": 3.0
        },
        "eye_and_mouth": {
            "left_eye_close_time_threshold": 1.5,
            "right_eye_right_click_time_threshold": 1.0,
            "mouth_open_right_click_time_threshold": 1.0,
            "mouth_open_menu_selection_threshold": 0.3,
            "eye_switch_cooldown_duration": 1.0,
            "right_eye_right_click_cooldown_duration": 1.0,
            "mouth_right_click_cooldown_duration": 1.0,
            "mouth_click_cooldown_duration": 0.5,
            "mouth_menu_selection_cooldown_duration": 0.8,
            "eye_close_threshold": 0.005,
            "mouth_open_threshold": 0.004
        },
        "filtering": {
            "filter_method": "smooth",
            "smoothing_alpha": 0.5,
            "move_threshold_pixels": 2,
            "use_movement_threshold": True,
            "use_median_filter": True,
            "median_filter_window": 10
        }
    }


# Load configuration
config = load_config()

# ============ COMMUNICATION SETTINGS ============
USE_MENU_SYSTEM = config["communication"]["use_menu_system"]  # Use False if you want to run AbleMouse AI edition without integration with AbleMouse Beyond Switch server https://github.com/aradzhabov/AbleMouse/
MENU_HOST = config["communication"]["menu_host"]
MENU_PORT = config["communication"]["menu_port"]

# ============ MAIN SETTINGS ============
pyautogui.FAILSAFE = False

camera = config["main"]["camera"]
bln_cam_mouse_control = config["main"]["cam_mouse_control"]
bln_display_fps = config["main"]["display_fps"]
bln_do_not_move_cursor_if_xy_move_within_threshold = config["main"]["do_not_move_cursor_if_xy_move_within_threshold"]
SKIP_X_THRESHOLD = config["main"]["skip_x_threshold"]
SKIP_Y_THRESHOLD = config["main"]["skip_y_threshold"]
bln_nose_center = config["main"]["nose_center"]
LAST_ACTION_DISPLAY_TIME = config["main"]["last_action_display_time"]

# ============ EYE AND MOUTH CLOSURE TRACKING SETTINGS ============
LEFT_EYE_CLOSE_TIME_THRESHOLD = config["eye_and_mouth"]["left_eye_close_time_threshold"]
RIGHT_EYE_RIGHT_CLICK_TIME_THRESHOLD = config["eye_and_mouth"]["right_eye_right_click_time_threshold"]
MOUTH_OPEN_RIGHT_CLICK_TIME_THRESHOLD = config["eye_and_mouth"]["mouth_open_right_click_time_threshold"]
MOUTH_OPEN_MENU_SELECTION_THRESHOLD = config["eye_and_mouth"]["mouth_open_menu_selection_threshold"]
EYE_SWITCH_COOLDOWN_DURATION = config["eye_and_mouth"]["eye_switch_cooldown_duration"]
RIGHT_EYE_RIGHT_CLICK_COOLDOWN_DURATION = config["eye_and_mouth"]["right_eye_right_click_cooldown_duration"]
MOUTH_RIGHT_CLICK_COOLDOWN_DURATION = config["eye_and_mouth"]["mouth_right_click_cooldown_duration"]
MOUTH_CLICK_COOLDOWN_DURATION = config["eye_and_mouth"]["mouth_click_cooldown_duration"]
MOUTH_MENU_SELECTION_COOLDOWN_DURATION = config["eye_and_mouth"]["mouth_menu_selection_cooldown_duration"]
EYE_CLOSE_THRESHOLD = config["eye_and_mouth"]["eye_close_threshold"]
MOUTH_OPEN_THRESHOLD = config["eye_and_mouth"]["mouth_open_threshold"]

# ============ FILTERING AND JITTER REDUCTION SETTINGS ============
FILTER_METHOD = config["filtering"]["filter_method"]
SMOOTHING_ALPHA = config["filtering"]["smoothing_alpha"]
MOVE_THRESHOLD_PIXELS = config["filtering"]["move_threshold_pixels"]
USE_MOVEMENT_THRESHOLD = config["filtering"]["use_movement_threshold"]
USE_MEDIAN_FILTER = config["filtering"]["use_median_filter"]
MEDIAN_FILTER_WINDOW = config["filtering"]["median_filter_window"]

# ============ PROGRAM WORKING VARIABLES ============
prev_frame_time = 0
new_frame_time = 0
left_eye_closed_start_time = None
right_eye_closed_start_time = None
mouth_open_start_time = None
eye_switch_cooldown = False
eye_switch_cooldown_time = 0
prev_left_eye_closed = False
prev_right_eye_closed = False
prev_mouth_open = False
right_eye_right_click_cooldown = False
right_eye_right_click_cooldown_time = 0
mouth_right_click_cooldown = False
mouth_right_click_cooldown_time = 0
mouth_click_cooldown = False
mouth_click_cooldown_time = 0
mouth_menu_selection_cooldown = False
mouth_menu_selection_cooldown_time = 0
position_history_x = []
position_history_y = []
smoothed_x = None
smoothed_y = None
last_action = ""
last_action_time = 0
menu_socket = None


# ============ SOCKET COMMUNICATION ============
def connect_to_menu():
    """connect to server"""
    global menu_socket
    try:
        menu_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        menu_socket.settimeout(2.0)
        menu_socket.connect((MENU_HOST, MENU_PORT))
        menu_socket.settimeout(5.0)
        print("Connected to AbleMouse Beyond Switch server")
        return True
    except Exception as e:
        print(f"failed to connect to AbleMouse Beyond Switch server: {e}")
        return False


def send_menu_command(command):
    """send command to AbleMouse Beyond Switch server"""
    global menu_socket

    if not menu_socket:
        if not connect_to_menu():
            return False

    try:
        data = json.dumps({"command": command}).encode('utf-8')
        menu_socket.sendall(data)

        try:
            response = menu_socket.recv(1024)
            if response:
                response_data = json.loads(response.decode('utf-8'))
                if response_data.get('status') == 'received':
                    print(f"Command '{command}' is delivered to AbleMouse Beyond Switch server")
                    return True
        except socket.timeout:
            print(f"Command '{command}' sent without confirmation")
            return True
        except:
            print(f"Command '{command}'. Something happened")
            return True

    except Exception as e:
        print(f"Failed to sent to to AbleMouse Beyond Switch server: {e}")
        try:
            menu_socket.close()
        except:
            pass
        menu_socket = None
        return False

    return False


def disconnect_from_menu():
    global menu_socket
    if menu_socket:
        try:
            menu_socket.close()
            menu_socket = None
            print("disconnected from AbleMouse Beyond Switch server")
        except:
            pass


# ============ FILTERING FUNCTIONS ============
def apply_median_filter(x, y, history_x, history_y, window_size):
    """Applies median filter to current coordinates"""
    history_x.append(x)
    history_y.append(y)

    if len(history_x) > window_size:
        history_x.pop(0)
        history_y.pop(0)

    if len(history_x) == window_size:
        sorted_x = sorted(history_x.copy())
        sorted_y = sorted(history_y.copy())
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


# ============ MAIN PROGRAM ============
if USE_MENU_SYSTEM:
    if not connect_to_menu():
        print("Run without integration with AbleMouse Beyond Switch server")
        USE_MENU_SYSTEM = False

cap = cv2.VideoCapture(camera)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

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

while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    frame = cv2.flip(frame, 1)

    if bln_display_fps:
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time
        fps = int(fps)
        fps = str(fps)
        cv2.putText(frame, fps, (7, 70), cv2.FONT_HERSHEY_SIMPLEX, 3, (100, 255, 0), 3, cv2.LINE_AA)

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    output = face_mesh.process(rgb_frame)
    landmark_points = output.multi_face_landmarks
    frame_h, frame_w, _ = frame.shape

    if landmark_points:
        bln_left_eye_closed = False
        bln_right_eye_closed = False
        bln_mouth_open = False

        landmarks = landmark_points[0].landmark

        right = [landmarks[386], landmarks[374]]
        for landmark in right:
            x = int(landmark.x * frame_w)
            y = int(landmark.y * frame_h)
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

        lip_upper = landmarks[13]
        x = int(lip_upper.x * frame_w)
        y = int(lip_upper.y * frame_h)
        cv2.circle(frame, (x, y), 3, (0, 0, 255))

        lip_down = landmarks[14]
        x = int(lip_down.x * frame_w)
        y = int(lip_down.y * frame_h)
        cv2.circle(frame, (x, y), 3, (0, 0, 255))

        lip_distance_diff = lip_down.y - lip_upper.y
        if lip_distance_diff > MOUTH_OPEN_THRESHOLD:
            bln_mouth_open = True

        current_time = time.time()
        left_eye_closed = bln_left_eye_closed
        right_eye_closed = bln_right_eye_closed
        mouth_open = bln_mouth_open

        if eye_switch_cooldown and (current_time - eye_switch_cooldown_time) > EYE_SWITCH_COOLDOWN_DURATION:
            eye_switch_cooldown = False

        if right_eye_right_click_cooldown and (
                current_time - right_eye_right_click_cooldown_time) > RIGHT_EYE_RIGHT_CLICK_COOLDOWN_DURATION:
            right_eye_right_click_cooldown = False

        if mouth_right_click_cooldown and (
                current_time - mouth_right_click_cooldown_time) > MOUTH_RIGHT_CLICK_COOLDOWN_DURATION:
            mouth_right_click_cooldown = False

        if mouth_click_cooldown and (current_time - mouth_click_cooldown_time) > MOUTH_CLICK_COOLDOWN_DURATION:
            mouth_click_cooldown = False

        if mouth_menu_selection_cooldown and (
                current_time - mouth_menu_selection_cooldown_time) > MOUTH_MENU_SELECTION_COOLDOWN_DURATION:
            mouth_menu_selection_cooldown = False

        # Left eye logic
        if left_eye_closed:
            if not prev_left_eye_closed and not eye_switch_cooldown:
                left_eye_closed_start_time = current_time

            if left_eye_closed_start_time is not None and not eye_switch_cooldown:
                elapsed_time = current_time - left_eye_closed_start_time
                progress_width = int((elapsed_time / LEFT_EYE_CLOSE_TIME_THRESHOLD) * 200)
                cv2.rectangle(frame, (10, 50), (10 + progress_width, 70), (0, 255, 0), -1)
                cv2.rectangle(frame, (10, 50), (210, 70), (255, 255, 255), 1)
                cv2.putText(frame, "MOUSE CONTROL ON/OFF PROGRESS ...", (220, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (0, 255, 255), 2)

                if elapsed_time >= LEFT_EYE_CLOSE_TIME_THRESHOLD:
                    bln_cam_mouse_control = not bln_cam_mouse_control
                    left_eye_closed_start_time = None
                    eye_switch_cooldown = True
                    eye_switch_cooldown_time = current_time
                    status = "ENABLED" if bln_cam_mouse_control else "DISABLED"
                    action_text = f"Mouse control {status}"
                    set_last_action(action_text)
                    cv2.putText(frame, f"Mouse control {status}!", (frame_w // 2 - 100, 50), cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0, 255, 0) if bln_cam_mouse_control else (0, 0, 255), 2)
                    print(f"Mouse control {status}")
        else:
            left_eye_closed_start_time = None

        # Right eye logic
        if right_eye_closed:
            if not prev_right_eye_closed and not right_eye_right_click_cooldown:
                right_eye_closed_start_time = current_time

            if right_eye_closed_start_time is not None and not right_eye_right_click_cooldown:
                elapsed_time = current_time - right_eye_closed_start_time
                progress_width = int((elapsed_time / RIGHT_EYE_RIGHT_CLICK_TIME_THRESHOLD) * 200)
                cv2.rectangle(frame, (10, 120), (10 + progress_width, 140), (255, 0, 0), -1)
                cv2.rectangle(frame, (10, 120), (210, 140), (255, 255, 255), 1)
                cv2.putText(frame, f"RIGHT CLICK PROGRESS ...", (220, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0),
                            2)

                if elapsed_time >= RIGHT_EYE_RIGHT_CLICK_TIME_THRESHOLD:
                    if bln_cam_mouse_control:
                        pyautogui.rightClick()
                        action_text = "Right click (right eye)"
                        set_last_action(action_text)
                        print("Right click performed (right eye)")
                        pyautogui.sleep(0.5)
                    right_eye_closed_start_time = None
                    right_eye_right_click_cooldown = True
                    right_eye_right_click_cooldown_time = current_time
        else:
            right_eye_closed_start_time = None

        # Mouth logic
        if mouth_open:
            if not prev_mouth_open:
                mouth_open_start_time = current_time

                if USE_MENU_SYSTEM and not mouth_menu_selection_cooldown and not mouth_click_cooldown:
                    if send_menu_command("select_current_item"):
                        action_text = "Menu selection (mouth open)"
                        set_last_action(action_text)
                        cv2.putText(frame, "Menu selection sent!", (frame_w // 2 - 100, 200), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.7, (0, 255, 255), 2)
                        mouth_menu_selection_cooldown = True
                        mouth_menu_selection_cooldown_time = current_time
                    else:
                        print("Could not send command to AbleMouse Beyond Switch server")
                elif bln_cam_mouse_control and not mouth_click_cooldown and not USE_MENU_SYSTEM:
                    pyautogui.click()
                    action_text = "Left click"
                    set_last_action(action_text)
                    print("Click performed at mouth open start")
                    mouth_click_cooldown = True
                    mouth_click_cooldown_time = current_time

            if not USE_MENU_SYSTEM and mouth_open_start_time is not None and not mouth_right_click_cooldown:
                elapsed_time = current_time - mouth_open_start_time
                progress_width = int((elapsed_time / MOUTH_OPEN_RIGHT_CLICK_TIME_THRESHOLD) * 200)
                cv2.rectangle(frame, (10, 190), (10 + progress_width, 210), (255, 255, 0), -1)
                cv2.rectangle(frame, (10, 190), (210, 210), (255, 255, 255), 1)
                cv2.putText(frame, "RIGHT CLICK PROGRESS ...", (220, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0),
                            2)

                if elapsed_time >= MOUTH_OPEN_RIGHT_CLICK_TIME_THRESHOLD:
                    if bln_cam_mouse_control:
                        pyautogui.rightClick()
                        action_text = "Right click (mouth open hold)"
                        set_last_action(action_text)
                        print("Right click performed (mouth open hold)")
                        pyautogui.sleep(0.5)
                    mouth_open_start_time = None
                    mouth_right_click_cooldown = True
                    mouth_right_click_cooldown_time = current_time
        else:
            mouth_open_start_time = None

        prev_left_eye_closed = left_eye_closed
        prev_right_eye_closed = right_eye_closed
        prev_mouth_open = mouth_open

        nose_landmark = landmarks[94]

        if bln_do_not_move_cursor_if_xy_move_within_threshold:
            skip = False
            if (abs(nose_landmark.x - previous_x_threshold) < SKIP_X_THRESHOLD) and \
                    (abs(nose_landmark.y - previous_y_threshold) < SKIP_Y_THRESHOLD):
                skip = True
            previous_x_threshold = nose_landmark.x
            previous_y_threshold = nose_landmark.y
            if skip:
                continue

        x = int(nose_landmark.x * frame_w)
        y = int(nose_landmark.y * frame_h)
        cv2.circle(frame, (x, y), 7, (0, 255, 0))

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

        # Apply filters
        raw_screen_x, raw_screen_y = screen_x, screen_y

        if USE_MEDIAN_FILTER:
            screen_x, screen_y = apply_median_filter(screen_x, screen_y,
                                                     position_history_x,
                                                     position_history_y,
                                                     MEDIAN_FILTER_WINDOW)

        if FILTER_METHOD == 'smooth':
            screen_x, screen_y = apply_exponential_smoothing(screen_x, screen_y,
                                                             smoothed_x, smoothed_y,
                                                             SMOOTHING_ALPHA)
            smoothed_x, smoothed_y = screen_x, screen_y

        if should_update_cursor(screen_x, screen_y, previous_x, previous_y, MOVE_THRESHOLD_PIXELS):
            final_x, final_y = screen_x, screen_y
        else:
            final_x, final_y = previous_x, previous_y

        if bln_cam_mouse_control:
            pyautogui.moveTo(final_x, final_y, _pause=False)

        previous_x = final_x
        previous_y = final_y

        cv2.circle(frame, (int(frame_w / 2), int(frame_h / 2)), 31, (0, 128, 0), 5)

        control_status = "MOUSE CONTROL: ON" if bln_cam_mouse_control else "MOUSE CONTROL: OFF"
        status_color = (0, 255, 0) if bln_cam_mouse_control else (0, 0, 255)
        cv2.putText(frame, control_status, (frame_w - 250, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        if USE_MENU_SYSTEM:
            menu_status = "MENU SYSTEM: CONNECTED" if menu_socket else "MENU SYSTEM: DISCONNECTED"
            menu_status_color = (0, 255, 0) if menu_socket else (0, 0, 255)
            cv2.putText(frame, menu_status, (frame_w - 300, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, menu_status_color, 2)

        current_time = time.time()
        if last_action and (current_time - last_action_time) < LAST_ACTION_DISPLAY_TIME:
            cv2.putText(frame, f"Last action: {last_action}", (frame_w - 500, frame_h - 60), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0, 255, 255), 2)

    cv2.imshow('Gagarin Data Labs -> AbleMouse AI edition', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

if USE_MENU_SYSTEM:
    disconnect_from_menu()

cv2.destroyAllWindows()
cap.release()