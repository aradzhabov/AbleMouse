#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Camera Llama Analyzer - for /v1/chat/completions API format
With image resizing capability
"""

import cv2
import numpy as np
import requests
import base64
import json
import time
import threading
import os
from datetime import datetime
from queue import Queue
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from PIL import Image, ImageTk
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
try:
    import vlc
    import Kostya_demo_cfg_helper as cfg
    VLC_AVAILABLE = True
except Exception:
    vlc = None
    cfg = None
    VLC_AVAILABLE = False

# Disable MSMF
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"


class CameraLlamaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Camera Llama Analyzer")
        self.root.geometry("900x600")

        # Settings for API format
        self.server_url = "http://localhost:8080"
        self.api_endpoint = "/v1/chat/completions"
        self.camera_id = 0
        self.interval = 0.5
        self.is_running = False
        self.cap = None
        self.current_frame = None
        self.camera_ready = False

        # UI state
        self.settings_visible = False

        # Current instruction (for live updates)
        self.current_instruction = "What do you see?"

        # Image size settings
        self.image_sizes = {
            "160x120 (very small)": (160, 120),
            "320x240 (small)": (320, 240),
            "640x480 (medium)": (640, 480),
            "800x600 (large)": (800, 600),
            "1024x768 (very large)": (1024, 768),
            "Original size": None
        }
        self.selected_size = "320x240 (small)"

        # Create session with retries
        self.session = self.create_session()

        # Prompts
        self.default_prompts = {
            "What do you see?": "What do you see?",
            "Describe in detail": "Describe in detail what you see in this image.",
            "List objects": "List all objects you can see in this image.",
            "Describe scene": "Describe the scene, environment, time of day.",
            "How many faces?": "How many faces are in this image?",
            "Read text": "What text is written in this image?",
            "Your own question": "What do you see?"
        }

        # Queues
        self.frame_queue = Queue(maxsize=5)
        self.result_queue = Queue()
        self.instruction_queue = Queue()  # New queue for instruction updates

        # Statistics
        self.stats = {'captured': 0, 'sent': 0, 'failed': 0, 'start_time': None}
        self.camera_error = None
        self.last_send_time = 0

        # Lock to prevent multiple requests
        self.send_lock = threading.Lock()

        # Maximum number of lines in results
        self.max_result_lines = 100

        # Media watcher state
        self.vlc_instance = None
        self.vlc_player = None
        self.media_known_files = {}
        self.media_last_activity = time.time()

        self.setup_ui()
        self.init_camera_threaded()
        self.update_preview()
        self.process_results()
        self.process_instruction_updates()  # New: process instruction updates
        self.start_media_watcher()

    def create_session(self):
        """Create HTTP session with retries"""
        session = requests.Session()

        # Configure retries
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def setup_ui(self):
        """Create compact interface"""
        # Configure root grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Main container
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=0)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # ========== LEFT PANEL - CAMERA ==========
        camera_panel = ttk.LabelFrame(main_frame, text="📷 Camera Preview", padding="5")
        camera_panel.grid(row=0, column=0, padx=2, pady=2, sticky=(tk.N, tk.W, tk.E))
        camera_panel.columnconfigure(0, weight=1)

        # Video preview
        self.video_label = ttk.Label(camera_panel, relief="solid")
        self.video_label.grid(row=0, column=0, pady=2)

        # Camera status and basic controls
        status_frame = ttk.Frame(camera_panel)
        status_frame.grid(row=1, column=0, pady=2, sticky=(tk.W, tk.E))

        self.video_info = ttk.Label(status_frame, text="📹 Initializing...", font=("Arial", 8))
        self.video_info.pack(side=tk.LEFT, padx=2)

        self.stats_label = ttk.Label(status_frame, text="📸0 ✅0 ❌0", font=("Arial", 8))
        self.stats_label.pack(side=tk.RIGHT, padx=2)

        # Size info
        self.size_info = ttk.Label(camera_panel, text="📏 320x240", font=("Arial", 7), foreground="gray")
        self.size_info.grid(row=2, column=0, pady=1)

        # Media output under camera
        media_panel = ttk.LabelFrame(camera_panel, text="🎬 Media", padding="5")
        media_panel.grid(row=3, column=0, padx=2, pady=2, sticky=(tk.W, tk.E))
        media_panel.columnconfigure(0, weight=1)
        self.media_canvas = tk.Canvas(media_panel, width=320, height=240, bg="black", highlightthickness=1)
        self.media_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # ========== RIGHT PANEL ==========
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=0, column=1, padx=2, pady=2, sticky=(tk.N, tk.W, tk.E, tk.S))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(3, weight=1)

        # ========== TOP CONTROLS ==========
        controls = ttk.Frame(right_panel)
        controls.grid(row=0, column=0, pady=2, sticky=(tk.W, tk.E))
        controls.columnconfigure(0, weight=1)

        # Main buttons row
        button_frame = ttk.Frame(controls)
        button_frame.grid(row=0, column=0, pady=2, sticky=(tk.W, tk.E))

        self.start_button = ttk.Button(button_frame, text="▶ Start", command=self.toggle_capture, width=8)
        self.start_button.pack(side=tk.LEFT, padx=1)

        self.snapshot_button = ttk.Button(button_frame, text="📸 Shot", command=self.capture_snapshot, width=8)
        self.snapshot_button.pack(side=tk.LEFT, padx=1)

        self.clear_button = ttk.Button(button_frame, text="🧹 Clear", command=self.clear_results, width=8)
        self.clear_button.pack(side=tk.LEFT, padx=1)

        self.settings_btn = ttk.Button(button_frame, text="⚙ Settings", command=self.toggle_settings, width=8)
        self.settings_btn.pack(side=tk.LEFT, padx=1)

        # Camera ID quick selector
        cam_frame = ttk.Frame(controls)
        cam_frame.grid(row=1, column=0, pady=1, sticky=(tk.W, tk.E))

        ttk.Label(cam_frame, text="Camera:", font=("Arial", 8)).pack(side=tk.LEFT)
        self.camera_spin = ttk.Spinbox(cam_frame, from_=0, to=10, width=3)
        self.camera_spin.pack(side=tk.LEFT, padx=2)
        self.camera_spin.insert(0, "0")

        self.scan_btn = ttk.Button(cam_frame, text="🔍", command=self.scan_cameras, width=2)
        self.scan_btn.pack(side=tk.LEFT, padx=1)

        # ========== INSTRUCTION ==========
        instruction_frame = ttk.LabelFrame(right_panel, text="💬 Instruction", padding="3")
        instruction_frame.grid(row=1, column=0, pady=2, sticky=(tk.W, tk.E))
        instruction_frame.columnconfigure(1, weight=1)

        # Quick prompt selector
        self.prompt_combo = ttk.Combobox(instruction_frame,
                                         values=list(self.default_prompts.keys()),
                                         width=27, height=5)
        self.prompt_combo.grid(row=0, column=0, columnspan=2, pady=1, sticky=(tk.W, tk.E))
        self.prompt_combo.set("Your own question")
        self.prompt_combo.bind('<<ComboboxSelected>>', self.on_prompt_selected)

        # Instruction text area with send button
        text_frame = ttk.Frame(instruction_frame)
        text_frame.grid(row=1, column=0, columnspan=2, pady=1, sticky=(tk.W, tk.E))
        text_frame.columnconfigure(0, weight=1)

        self.prompt_text = scrolledtext.ScrolledText(text_frame,
                                                     height=2,
                                                     width=35,
                                                     font=("Arial", 9))
        self.prompt_text.grid(row=0, column=0, pady=1, sticky=(tk.W, tk.E))
        self.prompt_text.insert('1.0', self.default_prompts["What do you see?"])

        # NEW: Send instruction button
        self.send_instruction_btn = ttk.Button(text_frame,
                                               text="📤 Send",
                                               command=self.send_new_instruction,
                                               width=8)
        self.send_instruction_btn.grid(row=0, column=1, padx=(2, 0), pady=1)

        self.one_shot_after_send = tk.BooleanVar(value=False)
        self.one_shot_check = ttk.Checkbutton(instruction_frame,
                                              text="One-shot on Send",
                                              variable=self.one_shot_after_send)
        self.one_shot_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(2, 0))

        # ========== SETTINGS PANEL (initially hidden) ==========
        self.settings_frame = ttk.LabelFrame(right_panel, text="⚙ Advanced Settings", padding="5")
        self.settings_frame.grid(row=2, column=0, pady=2, sticky=(tk.W, tk.E))
        self.settings_frame.columnconfigure(1, weight=1)

        # Server URL
        ttk.Label(self.settings_frame, text="Server:", font=("Arial", 8)).grid(row=0, column=0, sticky=tk.W, padx=2)
        self.server_entry = ttk.Entry(self.settings_frame, width=30)
        self.server_entry.grid(row=0, column=1, pady=1, sticky=(tk.W, tk.E))
        self.server_entry.insert(0, self.server_url)
        self.server_entry.bind('<KeyRelease>', self.on_server_url_change)

        self.test_button = ttk.Button(self.settings_frame, text="Test",
                                      command=self.test_server, width=5)
        self.test_button.grid(row=0, column=2, padx=2)

        # Image size
        ttk.Label(self.settings_frame, text="Size:", font=("Arial", 8)).grid(row=1, column=0, sticky=tk.W, padx=2)
        self.size_combo = ttk.Combobox(self.settings_frame,
                                       values=list(self.image_sizes.keys()),
                                       width=27)
        self.size_combo.grid(row=1, column=1, pady=1, sticky=(tk.W, tk.E))
        self.size_combo.set(self.selected_size)
        self.size_combo.bind('<<ComboboxSelected>>', self.on_size_selected)

        # Interval
        ttk.Label(self.settings_frame, text="Interval (ms):", font=("Arial", 8)).grid(row=2, column=0, sticky=tk.W,
                                                                                      padx=2)
        self.interval_combo = ttk.Combobox(self.settings_frame,
                                           values=["100", "250", "500", "1000", "2000", "3000", "5000"],
                                           width=10)
        self.interval_combo.grid(row=2, column=1, pady=1, sticky=tk.W)
        self.interval_combo.set("3000")

        # Hide settings initially
        self.settings_frame.grid_remove()

        # ========== RESULTS ==========
        result_frame = ttk.LabelFrame(right_panel, text="📝 Response", padding="3")
        result_frame.grid(row=3, column=0, pady=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        self.result_text = scrolledtext.ScrolledText(result_frame,
                                                     height=12,
                                                     width=50,
                                                     wrap=tk.WORD,
                                                     font=("Arial", 9))
        self.result_text.grid(row=0, column=0, pady=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Status bar
        self.status_label = ttk.Label(right_panel, text="Ready",
                                      foreground="green",
                                      font=("Arial", 8))
        self.status_label.grid(row=4, column=0, pady=1, sticky=tk.W)

    def toggle_settings(self):
        """Show/hide advanced settings panel"""
        if self.settings_visible:
            self.settings_frame.grid_remove()
            self.settings_btn.config(text="⚙ Settings")
            self.settings_visible = False
        else:
            self.settings_frame.grid()
            self.settings_btn.config(text="⚙ Hide")
            self.settings_visible = True

    def send_new_instruction(self):
        """Send new instruction without stopping capture"""
        new_instruction = self.prompt_text.get('1.0', 'end-1c').strip()
        if not new_instruction:
            new_instruction = "What do you see?"
            self.prompt_text.insert('1.0', new_instruction)

        # Update current instruction
        self.current_instruction = new_instruction

        # Put instruction update in queue
        self.instruction_queue.put(new_instruction)

        # Update status
        self.status_label.config(text=f"Instruction updated", foreground="green")

        # Optional: Force immediate send of next frame with new instruction
        if self.one_shot_after_send.get():
            self.capture_snapshot()
        elif self.is_running and self.current_frame is not None:
            thread = threading.Thread(
                target=self.process_frame,
                args=(self.current_frame.copy(),),
                daemon=True
            )
            thread.start()

    def process_instruction_updates(self):
        """Process instruction updates from queue"""
        try:
            while not self.instruction_queue.empty():
                new_instruction = self.instruction_queue.get_nowait()
                # Log instruction change
                self.result_text.insert('1.0',
                                        f"[{datetime.now().strftime('%H:%M:%S')}] 📝 Instruction changed to: '{new_instruction}'\n{'-' * 40}\n")
        except Exception as e:
            print(f"Error processing instruction update: {e}")

        self.root.after(100, self.process_instruction_updates)

    def on_server_url_change(self, event):
        """Update session when server URL changes"""
        self.session = self.create_session()

    def setup_vlc_player(self):
        if not VLC_AVAILABLE:
            return
        if not self.vlc_instance:
            self.vlc_instance = vlc.Instance()
        if not self.vlc_player:
            self.vlc_player = self.vlc_instance.media_player_new()
            try:
                self.vlc_player.video_set_scale(cfg.VIDEO_SCALE_FOR_FILE_WATCHER if cfg else 1.0)
            except Exception:
                pass
        try:
            hwnd = self.media_canvas.winfo_id()
            if os.name == "nt":
                self.vlc_player.set_hwnd(hwnd)
        except Exception:
            pass

    def close_vlc_player(self):
        try:
            if self.vlc_player:
                self.vlc_player.stop()
                self.vlc_player.release()
                self.vlc_player = None
            if self.vlc_instance:
                self.vlc_instance.release()
                self.vlc_instance = None
        except Exception:
            pass

    def get_current_media_files(self):
        try:
            folder = cfg.WATCH_DIR if cfg else None
            filt = (cfg.WATCH_FILTER if cfg else ".mp4").lower()
            if not folder or not os.path.isdir(folder):
                return {}
            return {
                f.lower(): os.path.getmtime(os.path.join(folder, f))
                for f in os.listdir(folder)
                if f.lower().endswith(filt)
            }
        except Exception:
            return {}

    def is_media_file_ready(self, file_path):
        try:
            size1 = os.path.getsize(file_path)
            time.sleep(cfg.WATCH_FILE_READY_CHECK_INTERVAL if cfg else 0.1)
            size2 = os.path.getsize(file_path)
            return size1 > 0 and size1 == size2
        except Exception:
            return False

    def play_media_file(self, filepath):
        try:
            self.setup_vlc_player()
            if not self.vlc_player or not self.vlc_instance:
                return
            media = self.vlc_instance.media_new(filepath)
            self.vlc_player.set_media(media)
            self.vlc_player.play()
            time.sleep(cfg.WATCHER_VLC_DELAY_TO_START_PLAYING if cfg else 0.1)
        except Exception:
            pass

    def media_watcher_loop(self):
        if not VLC_AVAILABLE or not cfg:
            return
        try:
            folder = cfg.WATCH_DIR
            self.media_known_files = self.get_current_media_files()
            while True:
                current_files = self.get_current_media_files()
                new_files = {f: m for f, m in current_files.items() if f not in self.media_known_files}
                if new_files:
                    self.media_last_activity = time.time()
                    for filename, mtime in sorted(new_files.items(), key=lambda x: x[1]):
                        filepath = os.path.join(folder, filename)
                        if self.is_media_file_ready(filepath):
                            self.play_media_file(filepath)
                            time.sleep(cfg.WATCHER_VLC_DELAY_TO_START_PLAYING if cfg else 0.1)
                            if self.vlc_player and self.vlc_player.is_playing():
                                self.media_known_files[filename] = mtime
                                while self.vlc_player.is_playing():
                                    time.sleep(cfg.WATCHER_VLC_INTERVAL_TO_CHECK_IF_PLAYER_STILL_PLAYS if cfg else 0.1)
                else:
                    try:
                        if cfg.CLOSE_AVATAR_IF_NEW_FILES_QUEUE_EMPTY:
                            if self.vlc_player and (time.time() - self.media_last_activity >
                                                    (cfg.TIME_INTERVAL_TO_DECIDE_THAT_NO_NEW_FILES_ARE_COMING)):
                                if not self.vlc_player.is_playing():
                                    self.close_vlc_player()
                    except Exception:
                        pass
                time.sleep(1)
        except Exception:
            pass

    def start_media_watcher(self):
        try:
            if VLC_AVAILABLE and cfg:
                t = threading.Thread(target=self.media_watcher_loop, daemon=True)
                t.start()
        except Exception:
            pass

    def on_size_selected(self, event):
        """When image size changes"""
        selected = self.size_combo.get()
        self.selected_size = selected
        size = self.image_sizes[selected]
        if size:
            self.size_info.config(text=f"📏 {size[0]}x{size[1]}")
        else:
            self.size_info.config(text="📏 Original")
        self.status_label.config(text=f"Size: {selected}", foreground="blue")

    def resize_image(self, frame):
        """Resize image according to settings"""
        try:
            selected = self.size_combo.get()
            target_size = self.image_sizes.get(selected)

            if target_size is None:  # Original size
                return frame

            # Resize
            resized = cv2.resize(frame, target_size, interpolation=cv2.INTER_AREA)
            return resized

        except Exception as e:
            print(f"Error resizing image: {e}")
            return frame

    def send_chat_completion(self, instruction, image_base64):
        """Send request in /v1/chat/completions format"""
        try:
            full_url = f"{self.server_url}{self.api_endpoint}"

            payload = {
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": instruction
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_base64
                                }
                            }
                        ]
                    }
                ]
            }

            response = self.session.post(
                full_url,
                headers={'Content-Type': 'application/json'},
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                if not content:
                    content = str(data)
                with self.send_lock:
                    self.stats['sent'] += 1
                return content, None
            else:
                with self.send_lock:
                    self.stats['failed'] += 1
                error_text = f"Server error: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_text += f" - {json.dumps(error_detail)}"
                except:
                    error_text += f" - {response.text[:200]}"
                return None, error_text

        except requests.exceptions.ConnectionError as e:
            with self.send_lock:
                self.stats['failed'] += 1
            self.session = self.create_session()
            return None, f"Connection error: Server at {self.server_url} not available"
        except requests.exceptions.Timeout:
            with self.send_lock:
                self.stats['failed'] += 1
            return None, "Timeout: Server took too long to respond"
        except Exception as e:
            with self.send_lock:
                self.stats['failed'] += 1
            return None, f"Error: {str(e)}"

    def send_to_server(self, frame):
        """Prepare and send frame with resizing"""
        try:
            # Resize before sending
            resized_frame = self.resize_image(frame)

            # Encode JPEG
            ret, buffer = cv2.imencode('.jpg', resized_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                return None, "Failed to encode image"

            img_base64 = base64.b64encode(buffer).decode('utf-8')
            img_base64_url = f"data:image/jpeg;base64,{img_base64}"

            # Get size for statistics
            height, width = resized_frame.shape[:2]
            size_info = f"{width}x{height}"

            # Use current instruction (can be updated dynamically)
            instruction = self.current_instruction

            # Send
            response, error = self.send_chat_completion(instruction, img_base64_url)

            # Add size information to result
            if response and not error:
                response = f"[{size_info}] {response}"

            return response, error

        except Exception as e:
            return None, f"Error preparing image: {str(e)}"

    def test_server(self):
        """Test server connection"""

        def test():
            try:
                # Check base URL availability
                response = self.session.get(self.server_url, timeout=3)

                # Check chat completions endpoint
                test_payload = {
                    "max_tokens": 5,
                    "messages": [
                        {
                            "role": "user",
                            "content": "test"
                        }
                    ]
                }

                chat_response = self.session.post(
                    f"{self.server_url}/v1/chat/completions",
                    json=test_payload,
                    timeout=5
                )

                if chat_response.status_code in [200, 400, 422]:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "Server Test",
                        "✅ Server is online and supports chat completions API!"
                    ))
                else:
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Server Test",
                        f"⚠ Server responded with status {chat_response.status_code}"
                    ))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(
                    "Server Test",
                    f"❌ Server not available: {str(e)}"
                ))

        threading.Thread(target=test, daemon=True).start()

    def capture_loop(self):
        """Capture loop with interval in milliseconds"""
        while self.is_running:
            try:
                if self.current_frame is not None:
                    thread = threading.Thread(
                        target=self.process_frame,
                        args=(self.current_frame.copy(),),
                        daemon=True
                    )
                    thread.start()

                interval_ms = int(self.interval_combo.get())
                time.sleep(interval_ms / 1000.0)

            except Exception as e:
                print(f"Error in capture loop: {e}")
                time.sleep(0.1)

    def process_frame(self, frame):
        """Process a single frame"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            with self.send_lock:
                self.stats['captured'] += 1

            response, error = self.send_to_server(frame)
            self.result_queue.put((timestamp, response, error))

        except Exception as e:
            print(f"Error processing frame: {e}")

    def process_results(self):
        """Process results from queue"""
        try:
            processed = 0
            max_per_cycle = 5

            while not self.result_queue.empty() and processed < max_per_cycle:
                timestamp, response, error = self.result_queue.get_nowait()

                if error:
                    self.result_text.insert('1.0',
                                            f"[{timestamp}] ❌ {error}\n{'-' * 40}\n")
                else:
                    if response and len(response) > 300:
                        display_response = response[:300] + "..."
                    else:
                        display_response = response if response else "Empty response"

                    self.result_text.insert('1.0',
                                            f"[{timestamp}] 🤖 {display_response}\n{'-' * 40}\n")

                processed += 1

            # Limit number of lines
            lines = self.result_text.get('1.0', 'end-1c').split('\n')
            if len(lines) > self.max_result_lines * 2:
                self.result_text.delete(f"{self.max_result_lines}.0", 'end')

            # Update statistics
            with self.send_lock:
                self.stats_label.config(
                    text=f"📸{self.stats['captured']} ✅{self.stats['sent']} ❌{self.stats['failed']}"
                )

        except Exception as e:
            print(f"Error in process_results: {e}")

        self.root.after(100, self.process_results)

    def on_prompt_selected(self, event):
        """Select prompt"""
        try:
            selected = self.prompt_combo.get()
            if selected in self.default_prompts:
                self.prompt_text.delete('1.0', 'end')
                self.prompt_text.insert('1.0', self.default_prompts[selected])
                self.status_label.config(
                    text=f"Prompt: {selected}",
                    foreground="blue"
                )
                # Auto-update instruction when selecting from dropdown
                self.send_new_instruction()
        except Exception as e:
            print(f"Error in prompt selection: {e}")

    def toggle_capture(self):
        """Start/stop capture"""
        if not self.camera_ready:
            messagebox.showerror("Error", "Camera not ready!")
            return

        if not self.is_running:
            try:
                self.camera_id = int(self.camera_spin.get())
                self.server_url = self.server_entry.get().rstrip('/')

                self.session = self.create_session()

                # Set initial instruction
                self.current_instruction = self.prompt_text.get('1.0', 'end-1c').strip()
                if not self.current_instruction:
                    self.current_instruction = "What do you see?"

                self.is_running = True
                self.start_button.config(text="⏸ Stop")
                self.stats['start_time'] = time.time()

                self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
                self.capture_thread.start()

                self.status_label.config(text="Processing...", foreground="red")

            except Exception as e:
                messagebox.showerror("Error", f"Invalid settings: {e}")
        else:
            self.is_running = False
            self.start_button.config(text="▶ Start")
            self.status_label.config(text="Stopped", foreground="blue")

    def capture_snapshot(self):
        """Manual snapshot"""
        if self.current_frame is not None and self.camera_ready:
            thread = threading.Thread(
                target=self.process_frame,
                args=(self.current_frame.copy(),),
                daemon=True
            )
            thread.start()
            self.status_label.config(text="Snapshot sent", foreground="green")

    def clear_results(self):
        """Clear results"""
        self.result_text.delete('1.0', tk.END)
        with self.send_lock:
            self.stats = {'captured': 0, 'sent': 0, 'failed': 0, 'start_time': None}
        self.stats_label.config(text="📸0 ✅0 ❌0")
        self.status_label.config(text="Cleared", foreground="blue")

    def init_camera_threaded(self):
        thread = threading.Thread(target=self.init_camera, daemon=True)
        thread.start()

    def init_camera(self):
        try:
            camera_id = int(self.camera_spin.get())

            backends = [
                (cv2.CAP_DSHOW, "DirectShow"),
                (cv2.CAP_MSMF, "MSMF"),
                (None, "Default")
            ]

            for backend, name in backends:
                try:
                    if backend:
                        cap = cv2.VideoCapture(camera_id, backend)
                    else:
                        cap = cv2.VideoCapture(camera_id)

                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            self.cap = cap
                            self.camera_ready = True
                            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                            self.root.after(0, self.update_camera_status,
                                            f"✓ {name}", "green")
                            return
                        else:
                            cap.release()
                except:
                    if 'cap' in locals():
                        cap.release()

            self.camera_ready = False
            self.root.after(0, self.update_camera_status,
                            "❌ Not found", "red")

        except Exception as e:
            self.camera_ready = False
            self.root.after(0, self.update_camera_status,
                            f"❌ Error", "red")

    def update_camera_status(self, text, color):
        self.video_info.config(text=f"📹 {text}", foreground=color)

    def update_preview(self):
        if self.cap and self.cap.isOpened() and self.camera_ready:
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.current_frame = frame

                    if self.is_running:
                        cv2.putText(frame, "REC", (10, 25),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                    # Show original size in preview
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    img = img.resize((320, 240), Image.Resampling.LANCZOS)
                    imgtk = ImageTk.PhotoImage(image=img)

                    self.video_label.imgtk = imgtk
                    self.video_label.configure(image=imgtk)
            except Exception as e:
                print(f"Error in update_preview: {e}")

        self.root.after(30, self.update_preview)

    def scan_cameras(self):
        def scan():
            working = []
            for i in range(5):
                try:
                    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            working.append(str(i))
                        cap.release()
                except:
                    pass

            if working:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Cameras Found",
                    f"Working cameras: {', '.join(working)}"
                ))
                if working and self.camera_spin.get() not in working:
                    self.camera_spin.delete(0, tk.END)
                    self.camera_spin.insert(0, working[0])
            else:
                self.root.after(0, lambda: messagebox.showwarning(
                    "Camera Scan",
                    "No working cameras found!"
                ))

        threading.Thread(target=scan, daemon=True).start()

    def on_closing(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.session.close()
        self.close_vlc_player()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = CameraLlamaApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
