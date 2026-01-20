# ToDo def server text's values in app_config class _UI(str, Enum):
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sys
import subprocess
import pygame
import socket
import json
import pyautogui
import queue

from menu_config import MENU_CONFIG
from app_config import AUDIO_CONFIG, SERVER_CONFIG, UI_CONFIG, STYLE_CONFIG, _UI


class GraphicMenuServer:
    def __init__(self, root):
        self.root = root
        self.root.title(_UI.APP_TITLE)

        # Initialize pygame for audio
        pygame.mixer.init()

        self.menu_config = MENU_CONFIG
        self.audio_config = AUDIO_CONFIG
        self.server_config = SERVER_CONFIG
        self.ui_config = UI_CONFIG
        self.style_config = STYLE_CONFIG

        self.transparency_level = self.ui_config["transparency"]
        self.root.attributes('-alpha', self.transparency_level)

        # Set to be on top of all windows
        self.root.attributes('-topmost', True)

        # Menu navigation history
        self.menu_history = ["main"]  # Start with main menu
        self.current_menu = "main"

        self.highlight_index = 0
        self.running = True
        self.highlight_interval = self.ui_config["highlight_interval"]

        # Server settings
        self.server_socket = None
        self.server_running = True
        self.client_connections = []

        # Queue for commands from clients
        self.command_queue = queue.Queue()

        # Button widgets cache
        self.buttons = []

        # Create styles
        self.setup_styles()

        # Create widgets
        self.create_widgets()

        # Start highlight thread
        self.highlight_thread = threading.Thread(target=self.highlight_cycle, daemon=True)
        self.highlight_thread.start()

        # Start server
        self.start_server()

        # Start command handler
        self.start_command_handler()

        # Key bindings
        self.root.bind('<space>', self.select_item)
        self.root.bind('<Up>', lambda e: self.move_highlight(-1))
        self.root.bind('<Down>', lambda e: self.move_highlight(1))

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        """Configure styles for widgets"""
        style = ttk.Style()
        style.theme_use('clam')

        colors = self.style_config["colors"]

        style.configure('Highlight.TButton',
                        background=colors["highlight"],
                        foreground='white',
                        font=('Arial', 12, 'bold'),
                        padding=10)

        style.configure('Normal.TButton',
                        background=colors["normal"],
                        foreground=colors["text"],
                        font=('Arial', 11),
                        padding=10)

        style.configure('Title.TLabel',
                        font=('Arial', 14, 'bold'),
                        background=colors["bg_main"],
                        foreground=colors["title_main"])

        style.configure('CursorTitle.TLabel',
                        font=('Arial', 14, 'bold'),
                        background=colors["bg_cursor"],
                        foreground=colors["title_cursor"])

        style.configure('ActionsTitle.TLabel',
                        font=('Arial', 14, 'bold'),
                        background=colors["bg_actions"],
                        foreground=colors["title_actions"])

    def create_widgets(self):
        """Create all interface widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.title_label = ttk.Label(main_frame,
                                     style='Title.TLabel')
        self.title_label.pack(fill=tk.X, padx=5, pady=(10, 20))

        # Frame for menu buttons
        self.menu_frame = ttk.Frame(main_frame)
        self.menu_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Transparency control panel
        self.create_transparency_controls(main_frame)

        # Server status control panel
        self.create_server_status_controls(main_frame)

        # Initialize menu
        self.update_menu()

    def create_transparency_controls(self, parent):
        """Create transparency control elements"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        ttk.Label(control_frame,
                  text=_UI.TRANSPARENCY,
                  font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 10))

        # Transparency slider
        self.transparency_var = tk.DoubleVar(value=self.transparency_level)
        transparency_slider = ttk.Scale(control_frame,
                                        from_=0.1,
                                        to=1.0,
                                        variable=self.transparency_var,
                                        command=self.update_transparency,
                                        length=150)
        transparency_slider.pack(side=tk.LEFT)

        # Value label
        self.transparency_label = ttk.Label(control_frame,
                                            text=f"{self.transparency_level:.1f}",
                                            width=5)
        self.transparency_label.pack(side=tk.LEFT, padx=(10, 0))

    def create_server_status_controls(self, parent):
        """Create server status control elements"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Server status
        self.server_status_label = ttk.Label(status_frame,
                                             text=_UI.SERVER_STATUS,
                                             foreground='green',
                                             font=('Arial', 10, 'bold'))
        self.server_status_label.pack(side=tk.LEFT)

        # Server port
        ttk.Label(status_frame,
                  text=f"{_UI.PORT}: {self.server_config['port']}",
                  font=('Arial', 9)).pack(side=tk.RIGHT)

    def update_menu(self):
        """Update menu display based on configuration"""
        # Check if application is still running and window exists
        if not self.running or not self.root.winfo_exists():
            return

        try:
            # Get configuration of current menu
            menu_config = self.menu_config[self.current_menu]

            # Update title
            self.title_label.config(text=menu_config["title"])
            self.title_label.configure(style=menu_config["title_style"])

            # Clear current menu
            for widget in self.menu_frame.winfo_children():
                widget.destroy()

            # Create buttons based on configuration
            self.buttons = []
            for i, item_config in enumerate(menu_config["items"]):
                btn = ttk.Button(self.menu_frame,
                                 text=item_config["text"],
                                 style='Normal.TButton' if i != 0 else 'Highlight.TButton',
                                 command=lambda config=item_config: self.execute_action(config))
                btn.pack(fill=tk.X, pady=1 if self.current_menu == "cursor" else 2)
                self.buttons.append(btn)

            # Reset highlight index
            self.highlight_index = 0
            self.update_highlight()

        except Exception as e:
            print(f"Error in update_menu: {e}")

    def go_to_main_menu(self):
        """Return to main menu"""
        if self.current_menu != "main":
            # Clear history, keeping only main menu
            self.menu_history = ["main"]
            self.current_menu = "main"
            self.highlight_index = 0
            self.update_menu()
            self.show_transition_effect()

    def go_back(self):
        """Go back one step"""
        if len(self.menu_history) > 0:
            # Take last menu from history
            self.current_menu = self.menu_history[-1]
            # Remove it from history
            self.menu_history.pop()
            self.highlight_index = 0
            self.update_menu()
            self.show_transition_effect()

    def go_back_levels(self, levels):
        """Go back N steps"""
        try:
            levels = int(levels)

            # Play back sound
            self.play_audio("back")

            # Calculate how far we can go back
            # Considering that after going back we'll be in menu_history[-1]
            steps_available = len(self.menu_history)

            if steps_available >= levels:
                # If we can go back the requested number of steps
                for _ in range(levels - 1):
                    self.menu_history.pop()

                # Last step - go to menu
                self.current_menu = self.menu_history.pop()
                self.highlight_index = 0
                self.update_menu()
                self.show_transition_effect()

            elif steps_available > 0:
                # If we can go back, but less than requested
                # Go back maximum possible
                for _ in range(steps_available - 1):
                    self.menu_history.pop()

                self.current_menu = self.menu_history.pop()
                self.highlight_index = 0
                self.update_menu()
                self.show_transition_effect()

            else:
                # History is empty
                self.show_cannot_go_back_effect()

        except Exception as e:
            print(f"Error when going back {levels} steps: {e}")
            self.go_back()

    def show_cannot_go_back_effect(self):
        """Show effect when cannot go back further"""
        if self.running and self.root.winfo_exists():
            try:
                original_bg = self.title_label.cget('background')
                self.title_label.configure(background='red')
                self.root.update()
                time.sleep(0.3)
                self.title_label.configure(background=original_bg)
            except:
                pass

    def execute_action(self, action_config):
        """Execute action based on configuration"""
        if not self.running:
            return

        action_type = action_config.get("action", "")

        try:
            if action_type == "open_menu":
                menu_name = action_config.get("menu", "")
                if menu_name in self.menu_config:
                    if self.current_menu == "main" and menu_name == "grid":
                        self.play_audio("grid")
                    elif self.current_menu == "main" and menu_name == "numbers":
                        self.play_audio("numbers")
                    elif self.current_menu == "mouse" and menu_name == "mouse_right":
                        self.play_audio("move_mouse_right")
                    elif self.current_menu == "mouse" and menu_name == "mouse_left":
                        self.play_audio("move_mouse_left")
                    elif self.current_menu == "mouse" and menu_name == "mouse_up":
                        self.play_audio("move_mouse_up")
                    elif self.current_menu == "mouse" and menu_name == "mouse_down":
                        self.play_audio("move_mouse_down")

                    # Add current menu to history
                    self.menu_history.append(self.current_menu)
                    self.current_menu = menu_name
                    self.highlight_index = 0
                    self.update_menu()

                    # Show transition effect
                    self.show_transition_effect()

            elif action_type == "go_back":
                # Go back
                # if len(self.menu_history) > 1:
                #     self.current_menu = self.menu_history.pop()
                #     self.highlight_index = 0
                #     self.update_menu()
                #     self.show_transition_effect()
                self.go_back()


            elif action_type == "go_back_levels":
                # Go back N steps
                levels = action_config.get("levels", 1)
                self.go_back_levels(levels)

            elif action_type == "go_to_main_menu":
                # Go back to main menu
                self.go_to_main_menu()

            elif action_type == "play_audio":
                # Play sound
                audio_type = action_config.get("audio", "")
                if audio_type:
                    self.play_audio(audio_type)

                    # Visual feedback
                    if self.buttons:
                        btn_index = next((i for i, item in enumerate(
                            self.menu_config[self.current_menu]["items"])
                                          if item.get("audio") == audio_type), 0)

                        if btn_index < len(self.buttons):
                            original_bg = self.buttons[btn_index].cget('background')
                            color = '#00ff00' if audio_type == "left_click" else '#ff0000'
                            self.buttons[btn_index].configure(background=color)
                            self.root.update()
                            self.root.after(200, lambda: self.buttons[btn_index].configure(background=original_bg))

            elif action_type == "open_notepad":
                # Open notepad
                self.open_notepad()

            elif action_type == "minimize_windows":
                # Minimize all windows
                self.minimize_all_windows()

            elif action_type == "exit_app":
                # Exit application
                self.exit_app()

        except Exception as e:
            print(f"Error in execute_action: {e}")

    def select_item(self, event=None):
        """Select currently highlighted item (by space or from CV)"""
        if not self.running:
            return

        try:
            # Get configuration of current menu
            menu_config = self.menu_config[self.current_menu]

            # Check if index is within bounds
            if self.highlight_index < len(menu_config["items"]):
                # Get configuration of selected item
                action_config = menu_config["items"][self.highlight_index]

                # Execute action
                self.execute_action(action_config)

        except Exception as e:
            print(f"Error in select_item: {e}")

    def play_audio(self, audio_type):
        """Play audio file by type"""
        filename = self.audio_config.get(audio_type)
        if filename and os.path.exists(filename):
            try:
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                print(f"Playing audio: {filename}")
                return True
            except Exception as e:
                print(f"Error playing audio {filename}: {e}")
        else:
            print(f"Audio file not found for type: {audio_type}")

        return False


    def open_notepad(self):
        """Open notepad """
        self.play_audio("notepad")

        # Open notepad
        try:
            if sys.platform == "win32":
                subprocess.Popen(['notepad.exe'])
            elif sys.platform == "darwin":
                subprocess.Popen(['open', '-a', 'TextEdit'])
            else:
                subprocess.Popen(['gedit'])

            # Show notification with delay
            self.root.after(500, lambda:
            messagebox.showinfo("Notification", "Notepad launched with audio effect"))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Notepad: {e}")


    def highlight_cycle(self):
        """Automatic highlight cycling"""
        while self.running:
            time.sleep(self.highlight_interval)
            if self.running:
                self.root.after(0, self.auto_highlight)

    def auto_highlight(self):
        """Automatic highlight switching"""
        if not self.running:
            return

        try:
            menu_config = self.menu_config[self.current_menu]
            max_index = len(menu_config["items"])
            self.highlight_index = (self.highlight_index + 1) % max_index
            self.update_highlight()
        except Exception as e:
            print(f"Error in auto_highlight: {e}")

    def update_highlight(self):
        """Update highlighting of all buttons"""
        if not self.running or not self.buttons:
            return

        try:
            for i, btn in enumerate(self.buttons):
                if i == self.highlight_index:
                    btn.configure(style='Highlight.TButton')
                else:
                    btn.configure(style='Normal.TButton')
        except Exception as e:
            print(f"Error in update_highlight: {e}")

    def move_highlight(self, direction):
        """Manual highlight movement"""
        if not self.running or not self.buttons:
            return

        try:
            max_index = len(self.buttons) - 1
            self.highlight_index = max(0, min(self.highlight_index + direction, max_index))
            self.update_highlight()
        except Exception as e:
            print(f"Error in move_highlight: {e}")

    def show_transition_effect(self):
        """Show transition effect between menus"""
        original_alpha = self.root.attributes('-alpha')

        def fade_out():
            for alpha in [original_alpha * 0.7, original_alpha * 0.4, original_alpha * 0.1]:
                if self.running and self.root.winfo_exists():
                    self.root.attributes('-alpha', alpha)
                    self.root.update()
                    time.sleep(0.05)

        def fade_in():
            for alpha in [original_alpha * 0.3, original_alpha * 0.6, original_alpha]:
                if self.running and self.root.winfo_exists():
                    self.root.attributes('-alpha', alpha)
                    self.root.update()
                    time.sleep(0.05)

        threading.Thread(target=lambda: (fade_out(), fade_in()), daemon=True).start()

    def update_transparency(self, value):
        """Update transparency level"""
        try:
            transparency = float(value)
            self.transparency_level = transparency
            self.root.attributes('-alpha', transparency)
            self.transparency_label.config(text=f"{transparency:.1f}")
        except:
            pass



    def get_menu_structure_info(self):
        """Get information about menu structure"""
        info_lines = []
        for menu_name, menu_config in self.menu_config.items():
            info_lines.append(f"• {menu_name}: {len(menu_config['items'])} items")
            for item in menu_config['items']:
                action = item.get('action', '')
                if action == 'open_menu':
                    info_lines.append(f"  → {item['text']} → {item['menu']}")
                elif action == 'play_number':
                    info_lines.append(f"  → {item['text']} (sound {item['number']}.mp3)") #ToDo
                elif action == 'play_audio':
                    info_lines.append(f"  → {item['text']} (sound {item['audio']}.mp3)") #ToDo
                else:
                    info_lines.append(f"  → {item['text']}")
        return "\n".join(info_lines)

    def start_server(self):
        """Start server for receiving commands from computer vision system"""

        def server_thread():
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind((self.server_config['host'], self.server_config['port']))
                self.server_socket.listen(5)
                self.server_socket.settimeout(1.0)

                print(f"Menu server started on port {self.server_config['port']}")

                while self.server_running:
                    try:
                        client_socket, address = self.server_socket.accept()
                        print(f"Client connected: {address}")

                        client_thread = threading.Thread(
                            target=self.handle_client,
                            args=(client_socket, address),
                            daemon=True
                        )
                        client_thread.start()

                    except socket.timeout:
                        continue
                    except Exception as e:
                        if self.server_running:
                            print(f"Accept error: {e}")

            except Exception as e:
                print(f"Failed to start server: {e}")

        server_thread_instance = threading.Thread(target=server_thread, daemon=True)
        server_thread_instance.start()

    def handle_client(self, client_socket, address):
        """Handle client connection"""
        try:
            client_socket.settimeout(5.0)

            while self.server_running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break

                    try:
                        command_data = json.loads(data.decode('utf-8'))
                        command = command_data.get('command', '')

                        print(f"Command received from {address}: {command}")

                        self.command_queue.put((command, address))

                        response = json.dumps({"status": "received", "command": command})
                        client_socket.send(response.encode('utf-8'))

                    except json.JSONDecodeError as e:
                        print(f"JSON decoding error from {address}: {e}")
                        continue

                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Read error from {address}: {e}")
                    break

        except Exception as e:
            print(f"Error processing client {address}: {e}")
        finally:
            try:
                client_socket.close()
                print(f"Client disconnected: {address}")
            except:
                pass

    def start_command_handler(self):
        """Start command handler from queue"""

        def command_handler():
            while self.server_running:
                try:
                    command, address = self.command_queue.get(timeout=1.0)

                    if not self.server_running:
                        break

                    if command == "select_current_item":
                        self.root.after_idle(self.select_item_from_cv)

                    self.command_queue.task_done()

                except queue.Empty:
                    continue
                except Exception as e:
                    if self.server_running:
                        print(f"Command handler error: {e}")

        command_thread = threading.Thread(target=command_handler, daemon=True)
        command_thread.start()

    def select_item_from_cv(self):
        """Select current menu item by command from computer vision system"""
        if not self.running or not self.root.winfo_exists():
            print("Application closed, ignoring CV command")
            return

        try:
            self.select_item()
            self.show_cv_selection_feedback()
        except Exception as e:
            print(f"Error processing CV command: {e}")

    def show_cv_selection_feedback(self):
        """Show feedback when selecting from CV system"""
        if not self.running or not self.root.winfo_exists():
            return

        try:
            original_bg = self.title_label.cget('background')
            original_fg = self.title_label.cget('foreground')

            self.title_label.configure(background='yellow', foreground='black')

            def restore_colors():
                if self.running and self.root.winfo_exists():
                    try:
                        self.title_label.configure(background=original_bg, foreground=original_fg)
                    except:
                        pass

            self.root.after(300, restore_colors)

            current_text = self.title_label.cget('text')
            if "[CV SELECTED]" not in current_text:
                def update_text():
                    if self.running and self.root.winfo_exists():
                        try:
                            self.title_label.config(text=f"{current_text} [CV SELECTED]")
                        except:
                            pass

                def restore_text():
                    if self.running and self.root.winfo_exists():
                        try:
                            self.title_label.config(text=current_text)
                        except:
                            pass

                self.root.after(0, update_text)
                self.root.after(1000, restore_text)

        except Exception as e:
            print(f"Error in show_cv_selection_feedback: {e}")

    def exit_app(self):
        """Exit application"""
        print("Starting application exit...")

        self.running = False
        self.server_running = False

        if self.server_socket:
            try:
                self.server_socket.close()
                print("Server socket closed")
            except Exception as e:
                print(f"Error closing server socket: {e}")

        try:
            pygame.mixer.quit()
            print("Pygame mixer stopped")
        except Exception as e:
            print(f"Error stopping pygame mixer: {e}")

        try:
            while not self.command_queue.empty():
                try:
                    self.command_queue.get_nowait()
                    self.command_queue.task_done()
                except:
                    break
            print("Command queue cleared")
        except Exception as e:
            print(f"Error clearing queue: {e}")

        time.sleep(0.1)

        try:
            if self.root and self.root.winfo_exists():
                self.root.destroy()
                print("Window destroyed")
        except Exception as e:
            print(f"Error destroying window: {e}")

        print("Application exit completed")

    def on_closing(self):
        """Handle window closing"""
        print("Window closing initiated by user")
        self.exit_app()


def main():
    """Main application launch function"""
    try:
        import pygame
        import pyautogui
    except ImportError:
        print("Install required libraries:")
        print("pip install pygame pyautogui")
        return

    root = tk.Tk()

    try:
        root.geometry(UI_CONFIG["window_size"])
        root.resizable(UI_CONFIG["resizable"], UI_CONFIG["resizable"])

        app = GraphicMenuServer(root)

        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')

        root.mainloop()

    except Exception as e:
        print(f"Critical error in main loop: {e}")
    finally:
        print("Application completed")


if __name__ == "__main__":
    main()