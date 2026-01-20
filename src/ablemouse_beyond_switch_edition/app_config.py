from enum import Enum

# Server configuration
SERVER_CONFIG = {
    "host": "localhost",
    "port": 12345
}

# Interface settings
UI_CONFIG = {
    "window_size": "500x800",
    "transparency": 0.85,
    "highlight_interval": 1.0,
    "resizable": True
}

# Style settings
STYLE_CONFIG = {
    "colors": {
        "highlight": '#3498db',
        "normal": '#ecf0f1',
        "text": '#2c3e50',
        "bg_main": '#34495e',
        "bg_cursor": '#2c3e50',
        "bg_actions": '#2d3a4a',
        "title_main": 'white',
        "title_cursor": '#e74c3c',
        "title_actions": '#9b59b6'
    }
}

# Audio files configuration
AUDIO_DIR = "audio"
NUM_DIR = f"{AUDIO_DIR}/num"
REQUESTS = f"{AUDIO_DIR}/requests"

AUDIO_CONFIG = {
    # base
    "grid": f"{AUDIO_DIR}/show grid.mp3",
    "numbers": f"{AUDIO_DIR}/show numbers.mp3",
    "show_keyboard": f"{AUDIO_DIR}/show keyboard.mp3",

    "stop": f"{AUDIO_DIR}/stop.mp3",
    "notepad": f"{AUDIO_DIR}/open_notepad.mp3",

    # mouse
    "move_mouse_right": f"{AUDIO_DIR}/move mouse right.mp3",
    "move_mouse_left": f"{AUDIO_DIR}/move mouse left.mp3",
    "move_mouse_up": f"{AUDIO_DIR}/move mouse up.mp3",
    "move_mouse_down": f"{AUDIO_DIR}/move mouse down.mp3",
    "move_slower": f"{AUDIO_DIR}/move slower.mp3",
    "move_faster": f"{AUDIO_DIR}/move faster.mp3",
    "left_click": f"{AUDIO_DIR}/left click.mp3",
    "right_click": f"{AUDIO_DIR}/right click.mp3",
# move mouse bottom left.mp3
# move mouse bottom right.mp3
# move mouse top left.mp3
# move mouse top right.mp3
# move mouse top left ↖ topleft, tl, ↖, nw, 1
# move mouse top right ↗ topright, tr, ↗, ne, 3
# move mouse bottom left ↙ bottomleft, bl, ↙, sw, 7
# move mouse bottom right ↘ bottomright, br, ↘, se, 9

    # scroll
    "start_scrolling_down": f"{AUDIO_DIR}/start scrolling down.mp3",
    "start_scrolling_up": f"{AUDIO_DIR}/start scrolling up.mp3",
    "scroll_up": f"{AUDIO_DIR}/scroll up.mp3",
    "scroll_down": f"{AUDIO_DIR}/scroll down.mp3",
    "scroll_left": f"{AUDIO_DIR}/scroll left.mp3",
    "scroll_right": f"{AUDIO_DIR}/scroll right.mp3",
    "scroll_to_left_edge": f"{AUDIO_DIR}/scroll to left edge.mp3",
    "scroll_to_right_edge": f"{AUDIO_DIR}/scroll to right edge.mp3",
    "scroll_to_top": f"{AUDIO_DIR}/scroll to top.mp3",
    "scroll_to_bottom": f"{AUDIO_DIR}/scroll to bottom.mp3",

    # Requests - Food items
    "water": f"{REQUESTS}/water.mp3",
    "bread": f"{REQUESTS}/bread.mp3",
    "milk": f"{REQUESTS}/milk.mp3",
    "tea": f"{REQUESTS}/tea.mp3",
    "coffee": f"{REQUESTS}/coffee.mp3",
    "juice": f"{REQUESTS}/juice.mp3",
    "fruit": f"{REQUESTS}/fruit.mp3",
    "sandwich": f"{REQUESTS}/sandwich.mp3",
    "soup": f"{REQUESTS}/soup.mp3",
    "meat": f"{REQUESTS}/meat.mp3",
    "fish": f"{REQUESTS}/fish.mp3",
    "vegetables": f"{REQUESTS}/vegetables.mp3",
    "dessert": f"{REQUESTS}/dessert.mp3",
    "snack": f"{REQUESTS}/snack.mp3",

    # Requests - Actions
    "toilet": f"{REQUESTS}/toilet.mp3",
    "hungry": f"{REQUESTS}/hungry.mp3",
    "thirsty": f"{REQUESTS}/thirsty.mp3",

    # num
    **{str(i): f"{NUM_DIR}/{i}.mp3" for i in range(0, 151)}
}

class _UI(str, Enum):
    """Text constants for the menu"""
    #ToDo - put here server text's values
    APP_TITLE = "👀"
    TRANSPARENCY = "Transparency"
    SERVER_STATUS = "Server Status: RUNNING"
    PORT = "Port"
    def __str__(self) -> str:
        return self.value
