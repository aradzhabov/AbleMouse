"""
Menu configuration for the graphical user interface.
"""

from enum import Enum

# ==================== TEXT CONSTANTS ====================
class _T(str, Enum):
    """Text constants for the menu"""
    # Common elements
    BACK = "↩ Back"
    ACTION = "◎ Action …"
    STOP = "⏹ Stop"
    SPEED = "🏎 Speed …"

    # Mouse actions
    LEFT_CLICK = "🖱⬅ Left Click"
    RIGHT_CLICK = "🖱➡ Right Click"
    FASTER = "⏩ Faster"
    SLOWER = "⏪ Slower"

    # Scrolling
    START_SCROLLING_DOWN = "start scrolling down"
    START_SCROLLING_UP = "start scrolling up"
    SCROLL_DOWN = "scroll down"
    SCROLL_UP = "scroll up"
    SCROLL_LEFT = "scroll left"
    SCROLL_RIGHT = "scroll right"
    SCROLL_TO_LEFT_EDGE = "scroll to left edge"
    SCROLL_TO_RIGHT_EDGE = "scroll to right edge"
    SCROLL_TO_TOP = "scroll to top"
    SCROLL_TO_BOTTOM = "scroll to bottom"

    # Menu titles
    OTHER = "Other …"
    MOUSE = "🖱 Mouse"
    SCROLL = "📜⇅ Scroll"
    SCROLL_OTHER = "Scroll other"
    ACTIONS_MENU = "◎ Action …"
    GRID_MENU = "▦ Grid"
    MOUSE_SPEED = "🏎 Speed …"
    NUMBERS = "🔢 Numbers"

    # Main menu
    SHOW_GRID = "▦ Grid"
    SHOW_NUMBERS = "🔢 Numbers"
    SHOW_KEYBOARD = "⌨ Keyboard"
    EXIT = "🚪 Exit"

    # Directions
    RIGHT = "→"
    LEFT = "←"
    UP = "↑"
    DOWN = "↓"

    # Navigation
    GO_TO_MAIN_MENU = "🏠 Home"
    NUMBERS_TREE = "↩ 🔢 Numbers"

    # Titles
    NUMBERS_TITLE = "🔢 Numbers"
    MAIN_MENU_TITLE = "github.com/aradzhabov/AbleMouse"

    # example of what you can create for the specific person
    REQUESTS_TITLE = "🙏 Requests"
    FOOD_TITLE = "🍎 Food"
    ACTIONS_TITLE = "🎭 Actions"

    # Requests menu
    REQUESTS = "🙏 Requests"

    FOOD = "🍎 Food"
    ACTIONS_REQUESTS = "🎭 Actions"

    TOILET = "🚽 I need toilet"
    HUNGRY = "🍽 I'm hungry"
    THIRSTY = "💧 I'm thirsty"

    # Food items
    WATER = "💧 Water"
    BREAD = "🍞 Bread"
    MILK = "🥛 Milk"
    TEA = "☕ Tea"
    COFFEE = "☕ Coffee"
    JUICE = "🧃 Juice"
    FRUIT = "🍎 Fruit"
    SANDWICH = "🥪 Sandwich"
    SOUP = "🍲 Soup"
    MEAT = "🍖 Meat"
    FISH = "🐟 Fish"
    VEGETABLES = "🥦 Vegetables"
    DESSERT = "🍰 Dessert"
    SNACK = "🍪 Snack"


    def __str__(self) -> str:
        return self.value

# ==================== MENU CONSTANTS ====================
# Base constants
BACK = {"text": _T.BACK, "action": "go_back"}
ACTION = {"text": _T.ACTION, "action": "open_menu", "menu": "actions"}
STOP = {"text": _T.STOP, "action": "play_audio", "audio": "stop"}
SPEED = {"text": _T.SPEED, "action": "open_menu", "menu": "mouse_speed"}

ACTION_WITH_SPEED_OPTION = {
    "text": _T.ACTION,
    "action": "open_menu",
    "menu": "actions_with_speed_option"
}


def create_menu(title: str, items: list, title_style: str = "Title.TLabel") -> dict:
    """Creates a menu with the given parameters"""
    return {
        "title": title,
        "title_style": title_style,
        "items": items
    }


def create_audio_item(text: str, audio: str) -> dict:
    """Creates a menu item for playing audio"""
    return {"text": text, "action": "play_audio", "audio": audio}


def create_menu_item(text: str, menu: str) -> dict:
    """Creates a menu item for opening another menu"""
    return {"text": text, "action": "open_menu", "menu": menu}


def create_scroll_menus() -> dict:
    """Creates menus for controlling scrolling"""

    scroll_menu_items = [
        create_audio_item(_T.START_SCROLLING_DOWN, "start_scrolling_down"),
        create_audio_item(_T.START_SCROLLING_UP, "start_scrolling_up"),
        STOP,
        create_menu_item(_T.OTHER, "scroll_other"),
        BACK
    ]

    scroll_other_items = [
        create_audio_item(_T.SCROLL_DOWN, "scroll_down"),
        create_audio_item(_T.SCROLL_UP, "scroll_up"),
        create_audio_item(_T.SCROLL_TO_TOP, "scroll_to_top"),
        create_audio_item(_T.SCROLL_TO_BOTTOM, "scroll_to_bottom"),
        create_audio_item(_T.SCROLL_LEFT, "scroll_left"),
        create_audio_item(_T.SCROLL_RIGHT, "scroll_right"),
        create_audio_item(_T.SCROLL_TO_LEFT_EDGE, "scroll_to_left_edge"),
        create_audio_item(_T.SCROLL_TO_RIGHT_EDGE, "scroll_to_right_edge"),
        STOP,
        BACK
    ]

    return {
        "scroll": create_menu(_T.SCROLL, scroll_menu_items),
        "scroll_other": create_menu(_T.SCROLL_OTHER, scroll_other_items)
    }


def create_directional_mouse_menus() -> dict:
    """Creates menus for all directions of mouse movement"""
    directions = ["right", "left", "up", "down"]
    menus = {}

    # Create the main mouse menu
    mouse_items = [
        create_menu_item(_T.RIGHT, "mouse_right"),
        create_menu_item(_T.LEFT, "mouse_left"),
        create_menu_item(_T.UP, "mouse_up"),
        create_menu_item(_T.DOWN, "mouse_down"),
        BACK
    ]
    menus["mouse"] = create_menu(_T.MOUSE, mouse_items)

    # Create a menu for each direction
    for direction in directions:
        menus[f"mouse_{direction}"] = create_menu(
            direction,
            [STOP, ACTION_WITH_SPEED_OPTION, BACK]
        )

    return menus


def create_number_submenu(start: int, end: int) -> dict:
    """Creates a submenu with a range of numbers"""
    number_items = [
        *[create_audio_item(str(i), str(i)) for i in range(start, end + 1)],
        ACTION,
        BACK
    ]
    return create_menu("", number_items)


def create_number_menu_system(start_num: int, end_num: int,
                              level1_count: int, level2_count: int,
                              level3_count: int) -> dict:
    """
    Creates a complete number menu system with customizable ranges
    """

    all_menus = {}
    total_numbers = end_num - start_num + 1

    # 1. Create first level menus
    main_menu_items = []

    # Range size for the first level
    level1_range_size = total_numbers // level1_count
    if total_numbers % level1_count != 0:
        level1_range_size += 1

    for i in range(level1_count):
        range_start = start_num + i * level1_range_size
        range_end = min(range_start + level1_range_size - 1, end_num)

        if range_start > end_num:
            break

        range_name = f"range_{range_start}_{range_end}"
        main_menu_items.append(create_menu_item(f"{range_start}-{range_end}", range_name))

        # 2. Create second level menus for this range
        second_level_items = []
        sub_range_size = (range_end - range_start + 1) // level2_count
        if (range_end - range_start + 1) % level2_count != 0:
            sub_range_size += 1

        for j in range(level2_count):
            sub_start = range_start + j * sub_range_size
            sub_end = min(sub_start + sub_range_size - 1, range_end)

            if sub_start > range_end:
                break

            sub_range_name = f"subrange_{sub_start}_{sub_end}"
            second_level_items.append(create_menu_item(f"{sub_start}-{sub_end}", sub_range_name))

            # 3. Create third level menus for this sub-range
            third_level_items = []
            third_range_size = (sub_end - sub_start + 1) // level3_count
            if (sub_end - sub_start + 1) % level3_count != 0:
                third_range_size += 1

            for k in range(level3_count):
                third_start = sub_start + k * third_range_size
                third_end = min(third_start + third_range_size - 1, sub_end)

                if third_start > sub_end:
                    break

                third_range_name = f"numbers_{third_start}_{third_end}"

                # Create the final menu with numbers
                all_menus[third_range_name] = create_number_submenu(third_start, third_end)

                third_level_items.append(create_menu_item(f"{third_start}-{third_end}", third_range_name))

            # Add BACK to the third level menu
            third_level_items.append(BACK)

            third_level_items.append({
                "text": _T.NUMBERS_TREE,
                "action": "go_back_levels",
                "levels": 2
            })

            third_level_items.append({
                "text": _T.GO_TO_MAIN_MENU,
                "action": "go_to_main_menu"
            })


            # Save the third level menu
            all_menus[sub_range_name] = create_menu("", third_level_items)

        # Add BACK to the second level menu
        second_level_items.append(BACK)

        # Save the second level menu
        all_menus[range_name] = create_menu("", second_level_items)

    # Add BACK to the main menu
    main_menu_items.append(BACK)

    # Add the main menu
    all_menus["numbers"] = create_menu(_T.NUMBERS_TITLE, main_menu_items)

    return all_menus


def create_actions_menus() -> dict:
    """Creates action menus"""
    basic_actions = [
        create_audio_item(_T.LEFT_CLICK, "left_click"),
        create_audio_item(_T.RIGHT_CLICK, "right_click"),
        BACK
    ]

    actions_with_speed = [
        create_audio_item(_T.LEFT_CLICK, "left_click"),
        create_audio_item(_T.RIGHT_CLICK, "right_click"),
        SPEED,
        BACK
    ]

    return {
        "actions": create_menu(_T.ACTIONS_MENU, basic_actions, "ActionsTitle.TLabel"),
        "actions_with_speed_option": create_menu(_T.ACTIONS_MENU, actions_with_speed, "ActionsTitle.TLabel")
    }


def create_grid_menu() -> dict:
    """Creates a menu for cursor movement"""
    grid_items = [
        *[create_audio_item(str(i), str(i)) for i in range(1, 10)],
        ACTION,
        BACK
    ]
    return {"grid": create_menu(_T.GRID_MENU, grid_items, "gridTitle.TLabel")}


def create_mouse_speed_menu() -> dict:
    """Creates a mouse speed menu"""
    speed_items = [
        create_audio_item(_T.FASTER, "move_faster"),
        create_audio_item(_T.SLOWER, "move_slower"),
        BACK
    ]
    return {"mouse_speed": create_menu(_T.MOUSE_SPEED, speed_items)}


def create_requests_menu_system() -> dict:
    """example of what you can create to the specific person
    Creates a menu system for requests (food and actions)"""

    # Food items menu
    food_items = [
        create_audio_item(_T.WATER, "water"),
        create_audio_item(_T.BREAD, "bread"),
        create_audio_item(_T.MILK, "milk"),
        create_audio_item(_T.TEA, "tea"),
        create_audio_item(_T.COFFEE, "coffee"),
        create_audio_item(_T.JUICE, "juice"),
        create_audio_item(_T.FRUIT, "fruit"),
        create_audio_item(_T.SANDWICH, "sandwich"),
        create_audio_item(_T.SOUP, "soup"),
        create_audio_item(_T.MEAT, "meat"),
        create_audio_item(_T.FISH, "fish"),
        create_audio_item(_T.VEGETABLES, "vegetables"),
        create_audio_item(_T.DESSERT, "dessert"),
        create_audio_item(_T.SNACK, "snack"),
        BACK
    ]

    # Actions requests menu
    actions_items = [
        create_audio_item(_T.TOILET, "toilet"),
        create_audio_item(_T.HUNGRY, "hungry"),
        create_audio_item(_T.THIRSTY, "thirsty"),
        BACK
    ]

    # Actions requests menu
    actions_items = [
        create_audio_item(_T.TOILET, "toilet"),
        create_audio_item(_T.HUNGRY, "hungry"),
        create_audio_item(_T.THIRSTY, "thirsty"),
        BACK
    ]

    # Main requests menu
    requests_items = [
        create_menu_item(_T.FOOD, "food_requests"),
        create_menu_item(_T.ACTIONS_REQUESTS, "actions_requests"),
        BACK
    ]

    # Return all menus as a dictionary
    menus_dict = {
        "requests": create_menu(_T.REQUESTS_TITLE, requests_items),
        "food_requests": create_menu(_T.FOOD_TITLE, food_items),
        "actions_requests": create_menu(_T.ACTIONS_TITLE, actions_items)
    }

    return menus_dict

def create_main_menu() -> dict:
    """Creates the main menu"""
    main_items = [
        create_menu_item(_T.SHOW_GRID, "grid"),
        create_menu_item(_T.SHOW_NUMBERS, "numbers"),
        create_audio_item(_T.SHOW_KEYBOARD, "show_keyboard"),
        # {"text": _T.EXIT, "action": "exit_app"},
        create_menu_item(_T.MOUSE, "mouse"),
        create_menu_item(_T.SCROLL, "scroll"),
        create_menu_item(_T.REQUESTS, "requests"),
    ]
    return {"main": create_menu(_T.MAIN_MENU_TITLE, main_items)}


# Creating all menus
SCROLL_MENUS = create_scroll_menus()
MOUSE_MENUS = create_directional_mouse_menus()
NUM_MENUS = create_number_menu_system(1, 150, 3, 5, 2)
ACTIONS_MENUS = create_actions_menus()
GRID_MENUS = create_grid_menu()
SPEED_MENUS = create_mouse_speed_menu()
REQUESTS_MENUS = create_requests_menu_system()
MAIN_MENU = create_main_menu()


# Combining all menus into one configuration
MENU_CONFIG = {
    **MAIN_MENU,
    **MOUSE_MENUS,
    **SPEED_MENUS,
    **NUM_MENUS,
    **SCROLL_MENUS,
    **GRID_MENUS,
    **ACTIONS_MENUS,
    **REQUESTS_MENUS
}