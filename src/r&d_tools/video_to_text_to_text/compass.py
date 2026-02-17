#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Camera Llama Analyzer - для API формата /v1/chat/completions
С возможностью изменения размера изображения
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

# Отключаем MSMF
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"


class CameraLlamaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Camera Llama Analyzer - Chat Completions API")
        self.root.geometry("1200x700")

        # Настройки для API формата
        self.server_url = "http://localhost:8080"
        self.api_endpoint = "/v1/chat/completions"
        self.camera_id = 0
        self.interval = 0.5
        self.is_running = False
        self.cap = None
        self.current_frame = None
        self.camera_ready = False

        # Настройки размера изображения
        self.image_sizes = {
            "160x120 (очень маленький)": (160, 120),
            "320x240 (маленький)": (320, 240),
            "640x480 (средний)": (640, 480),
            "800x600 (большой)": (800, 600),
            "1024x768 (очень большой)": (1024, 768),
            "Оригинальный размер": None
        }
        self.selected_size = "320x240 (маленький)"  # По умолчанию маленький для экономии

        # Создаем сессию с повторными попытками
        self.session = self.create_session()

        # Промпты
        self.default_prompts = {
            "What do you see?": "What do you see?",
            "Describe in detail": "Describe in detail what you see in this image.",
            "List objects": "List all objects you can see in this image.",
            "Describe scene": "Describe the scene, environment, time of day.",
            "How many faces?": "How many faces are in this image?",
            "Read text": "What text is written in this image?"
        }

        # Очереди
        self.frame_queue = Queue(maxsize=5)
        self.result_queue = Queue()

        # Статистика
        self.stats = {'captured': 0, 'sent': 0, 'failed': 0, 'start_time': None}
        self.camera_error = None
        self.last_send_time = 0

        # Блокировка для предотвращения множественных запросов
        self.send_lock = threading.Lock()

        # Максимальное количество строк в результатах
        self.max_result_lines = 100

        self.setup_ui()
        self.init_camera_threaded()
        self.update_preview()
        self.process_results()

    def create_session(self):
        """Создание HTTP сессии с повторными попытками"""
        session = requests.Session()

        # Настройка повторных попыток
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
        """Создание интерфейса"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Левая панель - видео
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.video_label = ttk.Label(left_frame)
        self.video_label.grid(row=0, column=0, pady=5)

        self.video_info = ttk.Label(left_frame, text="cam: init...")
        self.video_info.grid(row=1, column=0, pady=2)

        # Информация о размере
        self.size_info = ttk.Label(left_frame, text="cur size: 320x240")
        self.size_info.grid(row=2, column=0, pady=2)

        self.stats_label = ttk.Label(left_frame, text="📸 0 | ✅ 0 | ❌ 0")
        self.stats_label.grid(row=3, column=0, pady=2)

        # Правая панель
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Информация о API
        info_frame = ttk.LabelFrame(right_frame, text="API Information", padding="10")
        info_frame.grid(row=0, column=0, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(info_frame, text="Endpoint:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="/v1/chat/completions",
                  foreground="blue").grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)

        ttk.Label(info_frame, text="Format:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="OpenAI-compatible chat API",
                  foreground="green").grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)

        # Настройки сервера
        server_frame = ttk.LabelFrame(right_frame, text="Server Settings", padding="10")
        server_frame.grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(server_frame, text="Base URL:").grid(row=0, column=0, sticky=tk.W)
        self.server_entry = ttk.Entry(server_frame, width=40)
        self.server_entry.grid(row=0, column=1, padx=5, pady=2)
        self.server_entry.insert(0, self.server_url)
        self.server_entry.bind('<KeyRelease>', self.on_server_url_change)

        # Кнопка проверки
        self.test_button = ttk.Button(server_frame, text="🔍 Test Connection",
                                      command=self.test_server)
        self.test_button.grid(row=0, column=2, padx=5, pady=2)

        # Настройки камеры
        camera_frame = ttk.LabelFrame(right_frame, text="Camera Settings", padding="10")
        camera_frame.grid(row=2, column=0, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(camera_frame, text="Camera ID:").grid(row=0, column=0, sticky=tk.W)
        self.camera_spin = ttk.Spinbox(camera_frame, from_=0, to=10, width=10)
        self.camera_spin.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        self.camera_spin.insert(0, "0")

        self.scan_button = ttk.Button(camera_frame, text="🔍 Scan Cameras",
                                      command=self.scan_cameras)
        self.scan_button.grid(row=0, column=2, padx=5, pady=2)

        # Интервал в миллисекундах
        ttk.Label(camera_frame, text="Interval (ms):").grid(row=1, column=0, sticky=tk.W)
        self.interval_combo = ttk.Combobox(camera_frame,
                                           values=["100", "250", "500", "1000", "2000", "3000", "5000"], width=8)
        self.interval_combo.grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)
        self.interval_combo.set("500")

        # НОВОЕ: Настройка размера изображения
        size_frame = ttk.LabelFrame(right_frame, text="Image Size", padding="10")
        size_frame.grid(row=3, column=0, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(size_frame, text="Send size:").grid(row=0, column=0, sticky=tk.W)
        self.size_combo = ttk.Combobox(size_frame,
                                       values=list(self.image_sizes.keys()), width=25)
        self.size_combo.grid(row=0, column=1, padx=5, pady=2)
        self.size_combo.set(self.selected_size)
        self.size_combo.bind('<<ComboboxSelected>>', self.on_size_selected)

        # Информация о размере
        self.size_info_label = ttk.Label(size_frame,
                                         text="Smaller size = faster, but less detail",
                                         foreground="gray", font=("Arial", 8))
        self.size_info_label.grid(row=1, column=0, columnspan=2, pady=2)

        # Промпт
        prompt_frame = ttk.LabelFrame(right_frame, text="Instruction", padding="10")
        prompt_frame.grid(row=4, column=0, pady=5, sticky=(tk.W, tk.E))

        self.prompt_combo = ttk.Combobox(prompt_frame, values=list(self.default_prompts.keys()), width=37)
        self.prompt_combo.grid(row=0, column=0, padx=5, pady=2)
        self.prompt_combo.set("What do you see?")
        self.prompt_combo.bind('<<ComboboxSelected>>', self.on_prompt_selected)

        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, height=2, width=40)
        self.prompt_text.grid(row=1, column=0, padx=5, pady=2)
        self.prompt_text.insert('1.0', self.default_prompts["What do you see?"])

        # Кнопки
        control_frame = ttk.Frame(right_frame)
        control_frame.grid(row=5, column=0, pady=10)

        self.start_button = ttk.Button(control_frame, text="▶ Start",
                                       command=self.toggle_capture, width=12)
        self.start_button.grid(row=0, column=0, padx=2)

        self.snapshot_button = ttk.Button(control_frame, text="📸 Snapshot",
                                          command=self.capture_snapshot, width=12)
        self.snapshot_button.grid(row=0, column=1, padx=2)

        self.clear_button = ttk.Button(control_frame, text="🧹 Clear",
                                       command=self.clear_results, width=12)
        self.clear_button.grid(row=0, column=2, padx=2)

        # Результаты
        result_frame = ttk.LabelFrame(right_frame, text="Response", padding="10")
        result_frame.grid(row=6, column=0, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.result_text = scrolledtext.ScrolledText(result_frame, height=15, width=50, wrap=tk.WORD)
        self.result_text.grid(row=0, column=0, pady=2)

        # Статус
        self.status_label = ttk.Label(right_frame, text="Ready", foreground="green")
        self.status_label.grid(row=7, column=0, pady=5)

        # Настройка весов
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)

    def on_server_url_change(self, event):
        """При изменении URL сервера обновляем сессию"""
        self.session = self.create_session()

    def on_size_selected(self, event):
        """При изменении размера изображения"""
        selected = self.size_combo.get()
        self.selected_size = selected
        size = self.image_sizes[selected]
        if size:
            self.size_info.config(text=f"Текущий размер: {size[0]}x{size[1]}")
        else:
            self.size_info.config(text="Текущий размер: оригинальный")
        self.status_label.config(text=f"Size changed to: {selected}", foreground="blue")

    def resize_image(self, frame):
        """Изменение размера изображения в соответствии с настройками"""
        try:
            selected = self.size_combo.get()
            target_size = self.image_sizes.get(selected)

            if target_size is None:  # Оригинальный размер
                return frame

            # Изменяем размер
            resized = cv2.resize(frame, target_size, interpolation=cv2.INTER_AREA)
            return resized

        except Exception as e:
            print(f"Error resizing image: {e}")
            return frame  # В случае ошибки возвращаем оригинал

    def send_chat_completion(self, instruction, image_base64):
        """
        Отправка запроса в формате /v1/chat/completions
        """
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
        """Подготовка и отправка кадра с изменением размера"""
        try:
            # Изменяем размер перед отправкой
            resized_frame = self.resize_image(frame)

            # Кодируем JPEG
            ret, buffer = cv2.imencode('.jpg', resized_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                return None, "Failed to encode image"

            img_base64 = base64.b64encode(buffer).decode('utf-8')
            img_base64_url = f"data:image/jpeg;base64,{img_base64}"

            # Получаем размер для статистики
            height, width = resized_frame.shape[:2]
            size_info = f"{width}x{height}"

            instruction = self.prompt_text.get('1.0', 'end-1c').strip()
            if not instruction:
                instruction = "What do you see?"

            # Отправляем
            response, error = self.send_chat_completion(instruction, img_base64_url)

            # Добавляем информацию о размере к результату
            if response and not error:
                response = f"[Size: {size_info}] {response}"

            return response, error

        except Exception as e:
            return None, f"Error preparing image: {str(e)}"

    def test_server(self):
        """Тестирование подключения к серверу"""

        def test():
            try:
                # Проверяем доступность базового URL
                response = self.session.get(self.server_url, timeout=3)

                # Проверяем chat completions endpoint
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
        """Цикл захвата с интервалом в миллисекундах"""
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
        """Обработка одного кадра"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            with self.send_lock:
                self.stats['captured'] += 1

            response, error = self.send_to_server(frame)
            self.result_queue.put((timestamp, response, error))

        except Exception as e:
            print(f"Error processing frame: {e}")

    def process_results(self):
        """Обработка результатов из очереди"""
        try:
            processed = 0
            max_per_cycle = 5

            while not self.result_queue.empty() and processed < max_per_cycle:
                timestamp, response, error = self.result_queue.get_nowait()

                if error:
                    self.result_text.insert('1.0',
                                            f"[{timestamp}] ❌ {error}\n{'-' * 50}\n")
                else:
                    if response and len(response) > 500:
                        display_response = response[:500] + "...\n[response truncated]"
                    else:
                        display_response = response if response else "Empty response"

                    self.result_text.insert('1.0',
                                            f"[{timestamp}] 🤖 Response:\n{display_response}\n{'-' * 50}\n")

                processed += 1

            # Ограничиваем количество строк
            lines = self.result_text.get('1.0', 'end-1c').split('\n')
            if len(lines) > self.max_result_lines * 2:
                self.result_text.delete(f"{self.max_result_lines}.0", 'end')

            # Обновляем статистику
            with self.send_lock:
                self.stats_label.config(
                    text=f"📸 {self.stats['captured']} | ✅ {self.stats['sent']} | ❌ {self.stats['failed']}"
                )

        except Exception as e:
            print(f"Error in process_results: {e}")

        self.root.after(100, self.process_results)

    def on_prompt_selected(self, event):
        """Выбор промпта"""
        try:
            selected = self.prompt_combo.get()
            if selected in self.default_prompts:
                self.prompt_text.delete('1.0', 'end')
                self.prompt_text.insert('1.0', self.default_prompts[selected])
                self.status_label.config(
                    text=f"Instruction changed to: {selected}",
                    foreground="blue"
                )
        except Exception as e:
            print(f"Error in prompt selection: {e}")

    def toggle_capture(self):
        """Запуск/остановка"""
        if not self.camera_ready:
            messagebox.showerror("Error", "Camera not ready!")
            return

        if not self.is_running:
            try:
                self.camera_id = int(self.camera_spin.get())
                self.server_url = self.server_entry.get().rstrip('/')

                self.session = self.create_session()

                self.is_running = True
                self.start_button.config(text="⏸ Stop")
                self.stats['start_time'] = time.time()

                self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
                self.capture_thread.start()

                self.status_label.config(text="Processing started...", foreground="red")
                instruction_text = self.prompt_text.get('1.0', 'end-1c').strip()
                size_text = self.size_combo.get()
                self.result_text.insert('1.0',
                                        f"Started with instruction: '{instruction_text}', Size: {size_text}\n{'-' * 50}\n")

            except Exception as e:
                messagebox.showerror("Error", f"Invalid settings: {e}")
        else:
            self.is_running = False
            self.start_button.config(text="▶ Start")
            self.status_label.config(text="Processing stopped", foreground="blue")

    def capture_snapshot(self):
        """Ручной снимок"""
        if self.current_frame is not None and self.camera_ready:
            thread = threading.Thread(
                target=self.process_frame,
                args=(self.current_frame.copy(),),
                daemon=True
            )
            thread.start()
            size_text = self.size_combo.get()
            self.status_label.config(text=f"Snapshot sent ({size_text})", foreground="green")

    def clear_results(self):
        """Очистка результатов"""
        self.result_text.delete('1.0', tk.END)
        with self.send_lock:
            self.stats = {'captured': 0, 'sent': 0, 'failed': 0, 'start_time': None}
        self.stats_label.config(text="📸 0 | ✅ 0 | ❌ 0")
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
                                            f"✓ Camera ready ({name})", "green")
                            return
                        else:
                            cap.release()
                except:
                    if 'cap' in locals():
                        cap.release()

            self.camera_ready = False
            self.root.after(0, self.update_camera_status,
                            "❌ Camera not found", "red")

        except Exception as e:
            self.camera_ready = False
            self.root.after(0, self.update_camera_status,
                            f"❌ Error: {str(e)[:30]}", "red")

    def update_camera_status(self, text, color):
        self.video_info.config(text=text, foreground=color)

    def update_preview(self):
        if self.cap and self.cap.isOpened() and self.camera_ready:
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.current_frame = frame

                    if self.is_running:
                        cv2.putText(frame, "REC", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                    # Показываем в превью оригинальный размер (не измененный)
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    img = img.resize((480, 360), Image.Resampling.LANCZOS)
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
        self.root.destroy()


def main():
    root = tk.Tk()
    app = CameraLlamaApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()