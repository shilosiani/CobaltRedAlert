import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import time
import requests
import hashlib
import pygame
import tempfile
import os
import asyncio
import edge_tts


class ModernRedAlertGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_variables()
        self.load_targets()
        self.setup_styles()
        self.create_widgets()
        self.monitoring_thread = None
        self.is_monitoring = False
        self.last_alert_hash = None
        self.temp_audio_path = None

    def setup_window(self):
        self.root.title("מערכת התרעות אזעקה אדומה")
        self.root.geometry("800x600")
        self.root.minsize(750, 550)
        self.root.configure(bg="#f3f2f1")

        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"800x600+{x}+{y}")

    def setup_variables(self):
        self.monitored_areas = {
            "בני ברק",
            "תל אביב - מרכז העיר",
            "תל אביב - עבר הירקון",
        }
        self.all_targets = []
        self.filtered_targets = []
        self.tts_voice = tk.StringVar(value="he-IL-HilaNeural")
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="🟢 אין התרעות כרגע")
        self.monitor_button_text = tk.StringVar(value="הפעל ניטור")

    def load_targets(self):
        try:
            with open("appDesktop/targets.json", "r", encoding="utf-8") as f:
                self.all_targets = json.load(f)
                self.filtered_targets = self.all_targets.copy()
        except FileNotFoundError:
            messagebox.showerror("שגיאה", "קובץ targets.json לא נמצא!")
            self.all_targets = []
            self.filtered_targets = []

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("default")

        # Modern button style
        style.configure(
            "Modern.TButton",
            background="#0078d4",
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            padding=(20, 10),
        )
        style.map(
            "Modern.TButton", background=[("active", "#106ebe"), ("pressed", "#005a9e")]
        )

        # Stop button style
        style.configure(
            "Stop.TButton",
            background="#d13438",
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            padding=(20, 10),
        )
        style.map(
            "Stop.TButton", background=[("active", "#a4282c"), ("pressed", "#8b1e22")]
        )

        # Settings button style
        style.configure(
            "Settings.TButton",
            background="#6c757d",
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            padding=(10, 8),
        )

    def create_widgets(self):
        # Main container
        main_container = tk.Frame(self.root, bg="#f3f2f1")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        self.create_header(main_container)

        # Status section
        self.create_status_section(main_container)

        # Main content area
        content_frame = tk.Frame(main_container, bg="#f3f2f1")
        content_frame.pack(fill="both", expand=True, pady=(20, 0))

        # Right panel - Monitored areas (switched for RTL)
        self.create_monitored_areas_panel(content_frame)

        # Left panel - Add areas (switched for RTL)
        self.create_add_areas_panel(content_frame)

        # Bottom panel - Settings
        self.create_settings_panel(main_container)

    def create_header(self, parent):
        header_frame = tk.Frame(parent, bg="#f3f2f1")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = tk.Label(
            header_frame,
            text="🚨 מערכת התרעות אזעקה אדומה",
            font=("Arial", 24, "bold"),
            bg="#f3f2f1",
            fg="#323130",
            justify="right"
        )
        title_label.pack(side="right")

        # Monitor toggle button
        self.monitor_button = ttk.Button(
            header_frame,
            textvariable=self.monitor_button_text,
            style="Modern.TButton",
            command=self.toggle_monitoring,
        )
        self.monitor_button.pack(side="left", padx=(0, 10))

    def create_status_section(self, parent):
        status_frame = tk.Frame(parent, bg="white", relief="solid", bd=1)
        status_frame.pack(fill="x", pady=(0, 10))

        status_inner = tk.Frame(status_frame, bg="white")
        status_inner.pack(fill="x", padx=20, pady=15)

        tk.Label(
            status_inner,
            text="מצב נוכחי:",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#323130",
            justify="right"
        ).pack(side="right")

        self.status_label = tk.Label(
            status_inner,
            textvariable=self.status_var,
            font=("Arial", 12),
            bg="white",
            fg="#107c10",
            justify="right"
        )
        self.status_label.pack(side="right", padx=(0, 10))

    def create_monitored_areas_panel(self, parent):
        right_frame = tk.Frame(parent, bg="white", relief="solid", bd=1)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Header
        header = tk.Frame(right_frame, bg="white")
        header.pack(fill="x", padx=20, pady=(15, 10))

        tk.Label(
            header,
            text="אזורים מנוטרים",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#323130",
            justify="right"
        ).pack(side="right")

        # List with scrollbar
        list_frame = tk.Frame(right_frame, bg="white")
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="left", fill="y")

        self.monitored_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Arial", 10),
            bg="#fafafa",
            fg="#323130",
            selectbackground="#0078d4",
            selectforeground="white",
            bd=0,
            highlightthickness=1,
            highlightcolor="#0078d4",
            justify="right"
        )
        self.monitored_listbox.pack(side="right", fill="both", expand=True)
        scrollbar.config(command=self.monitored_listbox.yview)

        # Populate monitored areas
        for area in sorted(self.monitored_areas):
            self.monitored_listbox.insert("end", area)

        # Remove button
        remove_btn = ttk.Button(
            right_frame,
            text="הסר נבחר",
            command=self.remove_area,
            style="Settings.TButton",
        )
        remove_btn.pack(pady=(0, 15))

    def create_add_areas_panel(self, parent):
        left_frame = tk.Frame(parent, bg="white", relief="solid", bd=1)
        left_frame.pack(side="left", fill="both", expand=True)

        # Header
        header = tk.Frame(left_frame, bg="white")
        header.pack(fill="x", padx=20, pady=(15, 10))

        tk.Label(
            header,
            text="הוסף אזורים",
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#323130",
            justify="right"
        ).pack(side="right")

        # Search box
        search_frame = tk.Frame(left_frame, bg="white")
        search_frame.pack(fill="x", padx=20, pady=(0, 10))

        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Arial", 10),
            bg="#fafafa",
            relief="solid",
            bd=1,
            justify="right"
        )
        search_entry.pack(side="right", fill="x", expand=True, padx=(0, 10))
        search_entry.bind("<KeyRelease>", self.filter_targets)

        tk.Label(
            search_frame,
            text="חיפוש:",
            font=("Arial", 10),
            bg="white",
            fg="#323130",
            justify="right"
        ).pack(side="right")

        # Available areas list
        list_frame = tk.Frame(left_frame, bg="white")
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        scrollbar2 = ttk.Scrollbar(list_frame)
        scrollbar2.pack(side="left", fill="y")

        self.available_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar2.set,
            font=("Arial", 10),
            bg="#fafafa",
            fg="#323130",
            selectbackground="#0078d4",
            selectforeground="white",
            bd=0,
            highlightthickness=1,
            highlightcolor="#0078d4",
            justify="right"
        )
        self.available_listbox.pack(side="right", fill="both", expand=True)
        scrollbar2.config(command=self.available_listbox.yview)

        self.update_available_list()

        # Add button
        add_btn = ttk.Button(
            left_frame,
            text="הוסף נבחר",
            command=self.add_area,
            style="Modern.TButton",
        )
        add_btn.pack(pady=(0, 15))

    def create_settings_panel(self, parent):
        settings_frame = tk.Frame(parent, bg="white", relief="solid", bd=1)
        settings_frame.pack(fill="x", pady=(20, 0))

        settings_inner = tk.Frame(settings_frame, bg="white")
        settings_inner.pack(fill="x", padx=20, pady=15)

        # Exit button (moved to left for RTL)
        exit_btn = ttk.Button(
            settings_inner,
            text="יציאה",
            command=self.root.quit,
            style="Settings.TButton",
        )
        exit_btn.pack(side="left")

        # TTS Voice selection
        voice_combo = ttk.Combobox(
            settings_inner,
            textvariable=self.tts_voice,
            values=["he-IL-HilaNeural", "he-IL-AvriNeural"],
            state="readonly",
            width=15,
        )
        voice_combo.pack(side="right", padx=(20, 5))

        tk.Label(
            settings_inner,
            text="קול הודעה:",
            font=("Arial", 10),
            bg="white",
            fg="#323130",
            justify="right"
        ).pack(side="right", padx=(5, 30))

        tk.Label(
            settings_inner,
            text="הגדרות",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#323130",
            justify="right"
        ).pack(side="right")

    def filter_targets(self, event=None):
        search_text = self.search_var.get().lower()
        self.filtered_targets = [
            target for target in self.all_targets if search_text in target.lower()
        ]
        self.update_available_list()

    def update_available_list(self):
        self.available_listbox.delete(0, "end")
        for target in sorted(self.filtered_targets):
            if target not in self.monitored_areas:
                self.available_listbox.insert("end", target)

    def add_area(self):
        selection = self.available_listbox.curselection()
        if selection:
            area = self.available_listbox.get(selection[0])
            self.monitored_areas.add(area)
            self.monitored_listbox.insert("end", area)
            self.update_available_list()

    def remove_area(self):
        selection = self.monitored_listbox.curselection()
        if selection:
            area = self.monitored_listbox.get(selection[0])
            self.monitored_areas.discard(area)
            self.monitored_listbox.delete(selection[0])
            self.update_available_list()

    def toggle_monitoring(self):
        if not self.is_monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        self.is_monitoring = True
        self.monitor_button_text.set("עצור ניטור")
        self.monitor_button.configure(style="Stop.TButton")
        self.monitoring_thread = threading.Thread(
            target=self.monitor_alerts, daemon=True
        )
        self.monitoring_thread.start()

    def stop_monitoring(self):
        self.is_monitoring = False
        self.monitor_button_text.set("הפעל ניטור")
        self.monitor_button.configure(style="Modern.TButton")
        self.status_var.set("🟢 אין התרעות כרגע")
        self.status_label.configure(fg="#107c10")

    def monitor_alerts(self):
        while self.is_monitoring:
            try:
                if self.check_alerts():
                    time.sleep(25)
                else:
                    time.sleep(3)
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(5)

    def check_alerts(self):
        try:
            url = "https://www.oref.org.il/WarningMessages/alert/alerts.json"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            text = response.content.decode("utf-8-sig")

            if not text.strip() or not (text.startswith("[") or text.startswith("{")):
                self.root.after(
                    0, lambda: self.update_status("🟢 אין התרעות כרגע", "#107c10")
                )
                return False

            data = json.loads(text)
            alert_hash = hashlib.md5(text.encode()).hexdigest()

            if alert_hash == self.last_alert_hash:
                return False

            areas = data.get("data", [])
            relevant_areas = [area for area in areas if area in self.monitored_areas]

            if relevant_areas:
                title = data.get("title", "")
                description = data.get("desc", "")

                self.last_alert_hash = alert_hash

                # Update UI in main thread
                self.root.after(
                    0, lambda: self.handle_alert(title, description, relevant_areas)
                )

                return True

            return False

        except Exception as e:
            print(f"Alert check error: {e}")
            return False

    def handle_alert(self, title, description, areas):
        # Update status
        area_text = ", ".join(areas)
        self.update_status(f"🔴 התרעה פעילה ב: {area_text}", "#d13438")

        # Show toast
        self.show_toast_notification(title, area_text)

        # Play sound and TTS in background
        threading.Thread(
            target=self.play_alert_audio, args=(title, description), daemon=True
        ).start()

    def update_status(self, text, color):
        self.status_var.set(text)
        self.status_label.configure(fg=color)

    def show_toast_notification(self, title, areas):
        toast = tk.Toplevel(self.root)
        toast.title("אזעקה אדומה")
        toast.geometry("400x120")
        toast.configure(bg="#d13438")
        toast.attributes("-topmost", True)

        # Position toast at top-right of screen
        screen_width = toast.winfo_screenwidth()
        toast.geometry(f"400x120+{screen_width-420}+20")

        # Toast content
        toast_frame = tk.Frame(toast, bg="#d13438", padx=20, pady=15)
        toast_frame.pack(fill="both", expand=True)

        tk.Label(
            toast_frame,
            text="🚨 אזעקה אדומה",
            font=("Arial", 14, "bold"),
            bg="#d13438",
            fg="white",
            justify="right"
        ).pack()

        tk.Label(
            toast_frame,
            text=f"{title}",
            font=("Arial", 12),
            bg="#d13438",
            fg="white",
            justify="right"
        ).pack(pady=(5, 0))

        tk.Label(
            toast_frame,
            text=f"אזורים: {areas}",
            font=("Arial", 10),
            bg="#d13438",
            fg="white",
            wraplength=350,
            justify="right"
        ).pack(pady=(5, 0))

        # Auto-close toast after 10 seconds
        toast.after(10000, toast.destroy)

    async def convert_text_to_speech(self, texts):
        """Convert Hebrew text to speech using edge-tts"""
        try:
            voice_name = self.tts_voice.get()
            temp_dir = tempfile.mkdtemp()
            audio_files = []

            for idx, text in enumerate(texts):
                if not text.strip():
                    continue

                temp_file = os.path.join(temp_dir, f"tts_{idx}.mp3")
                communicate = edge_tts.Communicate(text, voice_name)
                await communicate.save(temp_file)
                audio_files.append(temp_file)

            return audio_files, temp_dir

        except Exception as e:
            print(f"TTS error: {e}")
            return [], None

    def play_tts_files(self, audio_files):
        """Play TTS audio files"""
        try:
            pygame.mixer.init()

            for audio_file in audio_files:
                if os.path.exists(audio_file):
                    pygame.mixer.music.load(audio_file)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.wait(100)
                    time.sleep(0.4)

        except Exception as e:
            print(f"TTS playback error: {e}")

    def cleanup_tts_files(self, temp_dir):
        """Clean up temporary TTS files"""
        try:
            if temp_dir and os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                os.rmdir(temp_dir)
        except Exception as e:
            print(f"Cleanup error: {e}")

    def play_sound(self):
        """Play alert sound"""
        try:
            sound_url = "https://cdn.pixabay.com/audio/2025/03/05/audio_3f481e8b25.mp3"
            response = requests.get(sound_url, timeout=10)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(response.content)
                self.temp_audio_path = tmp_file.name

            pygame.mixer.init()
            pygame.mixer.music.load(self.temp_audio_path)

            for i in range(3):
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                if i < 2:
                    time.sleep(0.3)

        except Exception as e:
            print(f"Sound error: {e}")
        finally:
            self.cleanup_audio()

    def cleanup_audio(self):
        try:
            pygame.mixer.quit()
            if self.temp_audio_path and os.path.exists(self.temp_audio_path):
                os.unlink(self.temp_audio_path)
                self.temp_audio_path = None
        except:
            pass

    def play_alert_audio(self, title, description):
        """Play TTS announcement and sound alert"""
        try:
            texts_to_speak = []

            if title:
                texts_to_speak.append(f"התרעה: {title}")

            if description:
                texts_to_speak.append(description)

            if texts_to_speak:
                # Run TTS conversion and playback
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                audio_files, temp_dir = loop.run_until_complete(
                    self.convert_text_to_speech(texts_to_speak)
                )

                if audio_files:
                    self.play_tts_files(audio_files)
                    self.cleanup_tts_files(temp_dir)

                loop.close()

            # Play alert sound
            self.play_sound()

        except Exception as e:
            print(f"Alert audio error: {e}")

    def run(self):
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.is_monitoring = False
            self.cleanup_audio()


if __name__ == "__main__":
    app = ModernRedAlertGUI()
    app.run()
