import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
import cv2
import numpy as np
import mss
import pydirectinput
import keyboard
import time
import random

import sys

# Get directory where script/executable is located to keep configuration portable
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

# ── Dark Theme Palette ────────────────────────────────────────────────────────
C_BG        = "#0d1117"   # root / main background
C_SURFACE   = "#161b22"   # card / frame surface
C_BORDER    = "#30363d"   # frame borders
C_ACCENT    = "#38bdf8"   # cyan accent (fishing vibe)
C_TEXT      = "#e6edf3"   # primary text
C_TEXT_DIM  = "#8b949e"   # secondary / hint text
C_GREEN     = "#22c55e"   # start button
C_GREEN_DK  = "#15803d"   # start button hover/disabled
C_RED       = "#ef4444"   # stop button
C_RED_DK    = "#991b1b"   # stop button disabled
C_BTN       = "#21262d"   # normal button bg
C_BTN_ACT   = "#30363d"   # normal button active bg
C_ORANGE    = "#f97316"   # warning status color
# ─────────────────────────────────────────────────────────────────────────────

class FishingBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Zero-Risk Fishing Bot - AFK Mode")
        self.root.geometry("480x520")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.configure(bg=C_BG)
        
        # Default configuration
        self.config = {
            'roi': {'top': 0, 'left': 0, 'width': 0, 'height': 0},
            'bite_roi': {'top': 0, 'left': 0, 'width': 0, 'height': 0},
            'hsv_lower': [60, 50, 50],
            'hsv_upper': [130, 255, 255],
            'cursor_lower': [20, 100, 100], 
            'cursor_upper': [40, 255, 255],
            'tolerance': 15,
            'invert_controls': False,
            'auto_farm': False
        }
        self.load_config()
        self.calculate_runtime_rois()
        
        self.bot_running = False
        self.bot_thread = None
        self.last_screenshot = None
        
        self.setup_ui()
        
        keyboard.add_hotkey('f8', self.toggle_bot_hotkey)
        keyboard.add_hotkey('f9', self.stop_bot_hotkey)
        
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.config.update(json.load(f))
            except Exception as e:
                print("Error loading config:", e)

    def calculate_runtime_rois(self):
        if 'base_resolution' not in self.config:
            self.config['base_resolution'] = [2560, 1440]
            
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        
        base_w, base_h = self.config['base_resolution']
        scale_x = screen_w / base_w
        scale_y = screen_h / base_h
        
        if abs(scale_x - 1.0) < 0.01 and abs(scale_y - 1.0) < 0.01:
            self.runtime_roi = self.config['roi'].copy()
            self.runtime_bite_roi = self.config.get('bite_roi', {'top': 0, 'left': 0, 'width': 0, 'height': 0}).copy()
        else:
            print(f"Auto-scaling ROIs from {base_w}x{base_h} to {screen_w}x{screen_h} (scale X: {scale_x:.2f}, Y: {scale_y:.2f})")
            
            roi = self.config['roi']
            self.runtime_roi = {
                'top': int(roi['top'] * scale_y),
                'left': int(roi['left'] * scale_x),
                'width': int(roi['width'] * scale_x),
                'height': int(roi['height'] * scale_y)
            }
            
            bite_roi = self.config.get('bite_roi', {'top': 0, 'left': 0, 'width': 0, 'height': 0})
            self.runtime_bite_roi = {
                'top': int(bite_roi['top'] * scale_y),
                'left': int(bite_roi['left'] * scale_x),
                'width': int(bite_roi['width'] * scale_x),
                'height': int(bite_roi['height'] * scale_y)
            }

    def save_config(self):
        if hasattr(self, 'invert_var'):
            self.config['invert_controls'] = self.invert_var.get()
            self.config['auto_farm'] = self.autofarm_var.get()
            self.config['tolerance'] = self.tol_var.get()
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print("Error saving config:", e)
            
    def setup_ui(self):
        # ── Apply dark ttk theme ───────────────────────────────────────────────
        style = ttk.Style(self.root)
        style.theme_use('clam')  # clam gives the most control over colors

        # Base widget backgrounds
        style.configure(".",
            background=C_BG, foreground=C_TEXT,
            fieldbackground=C_SURFACE, troughcolor=C_SURFACE,
            bordercolor=C_BORDER, darkcolor=C_BORDER, lightcolor=C_BORDER,
            font=("Segoe UI", 10))

        # Frames
        style.configure("TFrame", background=C_BG)
        style.configure("Dark.TFrame", background=C_SURFACE)

        # LabelFrame (the section boxes)
        style.configure("TLabelframe",
            background=C_SURFACE, bordercolor=C_BORDER,
            darkcolor=C_BORDER, lightcolor=C_BORDER, relief="solid")
        style.configure("TLabelframe.Label",
            background=C_SURFACE, foreground=C_ACCENT,
            font=("Segoe UI", 9, "bold"))

        # Labels
        style.configure("TLabel", background=C_BG, foreground=C_TEXT)
        style.configure("Surface.TLabel", background=C_SURFACE, foreground=C_TEXT)
        style.configure("Header.TLabel",
            background=C_BG, foreground=C_TEXT,
            font=("Segoe UI", 16, "bold"))
        style.configure("Info.TLabel",
            background=C_SURFACE, foreground=C_TEXT_DIM,
            font=("Segoe UI", 9))

        # Buttons (ttk)
        style.configure("TButton",
            background=C_BTN, foreground=C_TEXT,
            bordercolor=C_BORDER, darkcolor=C_BTN, lightcolor=C_BTN,
            font=("Segoe UI", 10), padding=6, relief="flat")
        style.map("TButton",
            background=[("active", C_BTN_ACT), ("pressed", C_BORDER)],
            foreground=[("active", C_ACCENT)],
            bordercolor=[("active", C_ACCENT)])

        # Collapsible Section Headers (Flat, highlight color)
        style.configure("Collapsible.TButton",
            background=C_SURFACE, foreground=C_ACCENT,
            bordercolor=C_BORDER, darkcolor=C_SURFACE, lightcolor=C_SURFACE,
            font=("Segoe UI", 10, "bold"), padding=8, relief="flat")
        style.map("Collapsible.TButton",
            background=[("active", C_BTN_ACT), ("pressed", C_BORDER)],
            foreground=[("active", C_TEXT)],
            bordercolor=[("active", C_ACCENT)])

        # Checkbutton
        style.configure("TCheckbutton",
            background=C_SURFACE, foreground=C_TEXT,
            indicatorcolor=C_BTN, indicatorbackground=C_BTN,
            font=("Segoe UI", 9))
        style.map("TCheckbutton",
            background=[("active", C_SURFACE)],
            foreground=[("active", C_ACCENT)],
            indicatorcolor=[("selected", C_ACCENT), ("!selected", C_BTN)])

        # Spinbox
        style.configure("TSpinbox",
            background=C_BTN, foreground=C_TEXT,
            fieldbackground=C_BTN, arrowcolor=C_TEXT_DIM,
            bordercolor=C_BORDER, darkcolor=C_BTN, lightcolor=C_BTN,
            insertcolor=C_TEXT)
        style.map("TSpinbox",
            fieldbackground=[("focus", C_SURFACE)],
            bordercolor=[("focus", C_ACCENT)])
        # ──────────────────────────────────────────────────────────────────────

        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        ttk.Label(main_frame, text="🎣 Neverness to Everness AFK Bot",
                  style="Header.TLabel").pack(pady=(0, 2))
        ttk.Label(main_frame, text="Colors & regions are pre-calibrated and will auto-scale to your screen size. If it works, just press START! Otherwise, expand 'Calibration & Setup' below to calibrate manually.",
                  style="TLabel", foreground=C_TEXT_DIM,
                  font=("Segoe UI", 9), wraplength=440).pack(pady=(0, 10))

        # Thin accent separator line under header
        sep = tk.Frame(main_frame, height=1, bg=C_ACCENT)
        sep.pack(fill=tk.X, pady=(0, 8))

        # --- COLLAPSIBLE SETUP PANEL ---
        self.calib_expanded = False

        self.calib_toggle_btn = ttk.Button(
            main_frame,
            text="▶  Show Calibration & Setup (Steps 1 & 2)",
            style="Collapsible.TButton",
            command=self.toggle_calibration
        )
        self.calib_toggle_btn.pack(fill=tk.X, pady=(0, 5))

        # Container frame for Step 1 and Step 2 (starts hidden / unpacked)
        self.calib_container = ttk.Frame(main_frame)

        # --- STEP 1: ROI ---
        step1_frame = ttk.LabelFrame(self.calib_container, text=" ▸ Step 1: Screen Regions (ROI) ", padding=10)
        step1_frame.pack(fill=tk.X, pady=5)

        ttk.Label(step1_frame,
                  text="1. Click below, draw a horizontal box covering the game's slider gauge (where cursor/target slide left/right), and press ENTER.",
                  wraplength=420, style="Info.TLabel").pack(anchor=tk.W, pady=(0, 4))
        ttk.Button(step1_frame, text="🖼  1a. Select Fishing Gauge Area",
                   command=lambda: self.calibrate_roi('fishing_bar')).pack(fill=tk.X, pady=(0, 10))

        ttk.Label(step1_frame,
                  text="2. (For 100% AFK) Click below and draw a box over the screen area where the yellow 'Fish on the hook!' text appears. Press ENTER.",
                  wraplength=420, style="Info.TLabel").pack(anchor=tk.W, pady=(0, 4))
        ttk.Button(step1_frame, text="🎣  1b. Select 'Fish on Hook!' Alert Area",
                   command=lambda: self.calibrate_roi('bite_area')).pack(fill=tk.X)

        # --- STEP 2: Color ---
        step2_frame = ttk.LabelFrame(self.calib_container, text=" ▸ Step 2: Target & Cursor Colors ", padding=10)
        step2_frame.pack(fill=tk.X, pady=5)

        ttk.Label(step2_frame,
                  text="Make sure the fishing gauge is visible on screen before clicking below.",
                  wraplength=420, style="Info.TLabel", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 6))

        ttk.Label(step2_frame,
                  text="1. Click 2a. On the screenshot, click directly on the CYAN target marker. Ensure it is white in the right preview window. Press Q to save.",
                  wraplength=420, style="Info.TLabel").pack(anchor=tk.W, pady=(0, 4))
        ttk.Button(step2_frame, text="🎯  2a. Detect CYAN Target Color",
                   command=lambda: self.calibrate_color('target')).pack(fill=tk.X, pady=(0, 10))

        ttk.Label(step2_frame,
                  text="2. Click 2b. On the same screenshot, click directly on the YELLOW cursor slider. Ensure it is white in the right preview window. Press Q to save.",
                  wraplength=420, style="Info.TLabel").pack(anchor=tk.W, pady=(0, 4))
        ttk.Button(step2_frame, text="🎯  2b. Detect YELLOW Cursor Color",
                   command=lambda: self.calibrate_color('cursor')).pack(fill=tk.X)

        # --- COLLAPSIBLE SETTINGS PANEL ---
        self.settings_expanded = False

        self.settings_toggle_btn = ttk.Button(
            main_frame,
            text="▶  Show Bot Settings (AFK Loop, Invert, Tolerance)",
            style="Collapsible.TButton",
            command=self.toggle_settings
        )
        self.settings_toggle_btn.pack(fill=tk.X, pady=(5, 5))

        # Container frame for Settings (starts hidden / unpacked)
        self.settings_container = ttk.Frame(main_frame)

        # --- SETTINGS ---
        settings_frame = ttk.LabelFrame(self.settings_container, text=" ▸ Bot Settings ", padding=10)
        settings_frame.pack(fill=tk.X, pady=5)

        self.autofarm_var = tk.BooleanVar(value=self.config.get('auto_farm', False))
        chk_afk = ttk.Checkbutton(settings_frame,
                                   text="Enable 100% AFK Auto-Farm Loop (Auto-casts bait)",
                                   variable=self.autofarm_var, command=self.save_config)
        chk_afk.pack(anchor=tk.W, pady=(0, 5))

        self.invert_var = tk.BooleanVar(value=self.config.get('invert_controls', False))
        chk_inv = ttk.Checkbutton(settings_frame,
                                   text="Invert Controls (If bot pulls AWAY from the target)",
                                   variable=self.invert_var, command=self.save_config)
        chk_inv.pack(anchor=tk.W, pady=(0, 5))

        tol_frame = ttk.Frame(settings_frame, style="Dark.TFrame")
        tol_frame.pack(fill=tk.X)
        ttk.Label(tol_frame, text="Tolerance (Aim Assist margin):",
                  style="Surface.TLabel").pack(side=tk.LEFT)
        self.tol_var = tk.IntVar(value=self.config.get('tolerance', 15))
        ttk.Spinbox(tol_frame, from_=5, to=50, textvariable=self.tol_var,
                    command=self.save_config, width=5).pack(side=tk.LEFT, padx=5)

        # --- STATUS ---
        status_outer = tk.Frame(main_frame, bg=C_SURFACE, bd=0, highlightthickness=1,
                                highlightbackground=C_BORDER)
        status_outer.pack(fill=tk.X, pady=8)

        # Check if pre-existing calibration is loaded
        if self.config.get('roi', {}).get('width', 0) > 0:
            initial_status = "Status: Ready"
            initial_color = C_GREEN
        else:
            initial_status = "Status: Waiting for Setup..."
            initial_color = C_ORANGE

        self.status_var = tk.StringVar(value=initial_status)
        self.status_label = tk.Label(status_outer, textvariable=self.status_var,
                                     fg=initial_color, bg=C_SURFACE,
                                     font=("Segoe UI", 12, "bold"), pady=6)
        self.status_label.pack()

        # --- RUN CONTROLS ---
        run_frame = ttk.LabelFrame(main_frame, text=" ▸ Step 3: Play ", padding=10)
        run_frame.pack(fill=tk.X, pady=5)

        self.start_btn = tk.Button(
            run_frame, text="▶  START BOT  (F8)",
            bg=C_GREEN, fg="#ffffff", activebackground=C_GREEN_DK, activeforeground="#ffffff",
            font=("Segoe UI", 11, "bold"), height=2, bd=0, cursor="hand2",
            command=self.start_bot)
        self.start_btn.pack(fill=tk.X, pady=(0, 5))

        self.stop_btn = tk.Button(
            run_frame, text="⏹  STOP BOT  (F9)",
            bg=C_RED, fg="#ffffff", activebackground=C_RED_DK, activeforeground="#ffffff",
            font=("Segoe UI", 11, "bold"), height=2, bd=0, cursor="hand2",
            command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X)

        # Footer hint
        tk.Label(main_frame,
                 text="Hotkeys: F8 = Start  •  F9 = Stop",
                 bg=C_BG, fg=C_TEXT_DIM, font=("Segoe UI", 8)).pack(pady=(8, 0))

        self.resize_to_fit()

    def toggle_calibration(self):
        if self.calib_expanded:
            self.calib_container.pack_forget()
            self.calib_toggle_btn.config(text="▶  Show Calibration & Setup (Steps 1 & 2)")
            self.calib_expanded = False
        else:
            self.calib_container.pack(fill=tk.X, after=self.calib_toggle_btn, pady=5)
            self.calib_toggle_btn.config(text="▼  Hide Calibration & Setup (Steps 1 & 2)")
            self.calib_expanded = True
        self.resize_to_fit()
    def toggle_settings(self):
        if self.settings_expanded:
            self.settings_container.pack_forget()
            self.settings_toggle_btn.config(text="▶  Show Bot Settings (AFK Loop, Invert, Tolerance)")
            self.settings_expanded = False
        else:
            self.settings_container.pack(fill=tk.X, after=self.settings_toggle_btn, pady=5)
            self.settings_toggle_btn.config(text="▼  Hide Bot Settings (AFK Loop, Invert, Tolerance)")
            self.settings_expanded = True
        self.resize_to_fit()

    def resize_to_fit(self):
        self.root.geometry("")
        self.root.update_idletasks()
        required_height = self.root.winfo_reqheight()
        # Add 12px extra buffer space at the bottom to ensure no compression
        self.root.geometry(f"480x{required_height + 12}")

    def calibrate_roi(self, mode):
        self.root.withdraw()
        self.root.update()
        time.sleep(0.3)
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = np.array(sct.grab(monitor))
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            
        window_name = "Select ROI - Drag box and press ENTER"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
        
        roi = cv2.selectROI(window_name, screenshot, fromCenter=False, showCrosshair=True)
        cv2.destroyWindow(window_name)
        
        if roi != (0, 0, 0, 0):
            x, y, w, h = roi
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            self.config['base_resolution'] = [screen_w, screen_h]

            if mode == 'fishing_bar':
                self.config['roi'] = {'top': y, 'left': x, 'width': w, 'height': h}
                self.status_var.set("Status: Fishing Bar Saved!")
            else:
                self.config['bite_roi'] = {'top': y, 'left': x, 'width': w, 'height': h}
                self.status_var.set("Status: Bite Area Saved!")
            self.save_config()
            self.calculate_runtime_rois()
            self.status_label.config(fg=C_GREEN)
        else:
            self.status_var.set("Status: Calibration Cancelled")
            self.status_label.config(fg=C_ORANGE)
            
        self.root.deiconify()

    def calibrate_color(self, mode):
        if self.config['roi']['width'] == 0:
            messagebox.showerror("Error", "Please complete Step 1a first!")
            return
            
        self.root.withdraw()
        self.root.update()
        time.sleep(0.3)
        
        if mode == 'cursor' and self.last_screenshot is not None:
            roi_img = self.last_screenshot.copy()
        else:
            with mss.mss() as sct:
                roi_img_bgra = np.array(sct.grab(self.runtime_roi))
                roi_img = cv2.cvtColor(roi_img_bgra, cv2.COLOR_BGRA2BGR)
            self.last_screenshot = roi_img.copy()
            
        self.show_color_picker(mode, roi_img)
        
    def show_color_picker(self, mode, roi_img):
        window_title = f"Detect {'CYAN Target' if mode == 'target' else 'YELLOW Cursor'}"
        cv2.namedWindow(window_title, cv2.WINDOW_AUTOSIZE)
        cv2.setWindowProperty(window_title, cv2.WND_PROP_TOPMOST, 1)
        
        hsv_img = cv2.cvtColor(roi_img, cv2.COLOR_BGR2HSV)
        
        height = roi_img.shape[0]
        width = roi_img.shape[1]
        if height > 0 and width > 0:
            scale_h = 200.0 / height
            scale_w = 800.0 / width
            scale = min(scale_h, scale_w)
            
            if scale > 1.0:
                new_width = int(width * scale)
                new_height = int(height * scale)
                display_bgr = cv2.resize(roi_img, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
                display_hsv = cv2.resize(hsv_img, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
            else:
                display_bgr = roi_img.copy()
                display_hsv = hsv_img.copy()
        else:
            display_bgr = roi_img.copy()
            display_hsv = hsv_img.copy()
            
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                if x >= display_hsv.shape[1]:
                    x = x % display_hsv.shape[1]
                pixel_hsv = display_hsv[y, x]
                h, s, v = pixel_hsv
                
                h_min = max(0, int(h) - 15)
                h_max = min(179, int(h) + 15)
                s_min = max(0, int(s) - 60)
                s_max = 255
                v_min = max(0, int(v) - 60)
                v_max = 255
                
                if mode == 'target':
                    self.config['hsv_lower'] = [h_min, s_min, v_min]
                    self.config['hsv_upper'] = [h_max, s_max, v_max]
                else:
                    self.config['cursor_lower'] = [h_min, s_min, v_min]
                    self.config['cursor_upper'] = [h_max, s_max, v_max]
                print(f"Sampled HSV for {mode}: {h},{s},{v}. New bounds set.")
                
        cv2.setMouseCallback(window_title, mouse_callback)
        
        color_rgb = (0, 255, 255) if mode == 'cursor' else (255, 255, 0)
        
        while True:
            if mode == 'target':
                lower = np.array(self.config['hsv_lower'])
                upper = np.array(self.config['hsv_upper'])
            else:
                lower = np.array(self.config['cursor_lower'])
                upper = np.array(self.config['cursor_upper'])
            
            mask = cv2.inRange(display_hsv, lower, upper)
            
            left_side = display_bgr.copy()
            mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
            combined = np.hstack((left_side, mask_bgr))
            
            cv2.putText(combined, f"1. CLICK on the {'YELLOW Cursor' if mode == 'cursor' else 'CYAN Target'}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_rgb, 2)
            cv2.putText(combined, "2. Check right side -> Object should be white", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_rgb, 2)
            cv2.putText(combined, "3. Press 'Q' to Save", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_rgb, 2)
            
            cv2.imshow(window_title, combined)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                self.save_config()
                break
                
        cv2.destroyAllWindows()
        self.status_var.set(f"Status: {mode.title()} Color Saved!")
        self.status_label.config(fg=C_GREEN)
        self.root.deiconify()

    def toggle_bot_hotkey(self):
        if not self.bot_running:
            self.root.after(0, self.start_bot)

    def stop_bot_hotkey(self):
        if self.bot_running:
            self.root.after(0, self.stop_bot)

    def start_bot(self):
        if self.config['roi']['width'] == 0:
            messagebox.showerror("Error", "You must complete Calibration Step 1a first!")
            return
            
        if self.config.get('auto_farm', False) and self.config.get('bite_roi', {}).get('width', 0) == 0:
            messagebox.showerror("Error", "To use Auto-Farm, you must complete Calibration Step 1b!")
            return
            
        if self.bot_running:
            return
            
        self.bot_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Status: 🟢 BOT IS RUNNING")
        self.status_label.config(fg=C_GREEN)
        
        self.save_config()
        
        self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        self.bot_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Status: 🔴 BOT STOPPED")
        self.status_label.config(fg=C_RED)
        
        # Failsafe: Ensure keys are physically released if stopped while holding
        try:
            pydirectinput.keyUp('a')
            pydirectinput.keyUp('d')
            pydirectinput.keyUp('f')
        except:
            pass

    def bot_loop(self):
        roi = self.runtime_roi
        bite_roi = self.runtime_bite_roi
        
        lower_hsv = np.array(self.config['hsv_lower'])
        upper_hsv = np.array(self.config['hsv_upper'])
        
        cursor_lower = np.array(self.config['cursor_lower'])
        cursor_upper = np.array(self.config['cursor_upper'])
        
        tolerance = self.config['tolerance']
        invert = self.config.get('invert_controls', False)
        auto_farm = self.config.get('auto_farm', False)
        
        current_action = 'NONE'
        held_key = None
        lost_target_time = 0
        state_start_time = time.time()
        baseline_white = 0
        bite_confirm_count = 0  # Properly-scoped local — never leaks between cycles
        
        state = 'CASTING' if auto_farm else 'REELING'

        with mss.mss() as sct:
            while self.bot_running:
                try:
                    if state == 'CASTING':
                        self.root.after(0, lambda: self.status_var.set("Status: 🎣 Casting Bait..."))
                        pydirectinput.keyDown('f')
                        time.sleep(random.uniform(0.10, 0.22)) # Firm enough for game to register, faster than before
                        pydirectinput.keyUp('f')

                        # --- FIX: Monitor for bites DURING the post-cast window ---
                        # Instead of sleeping blindly, we poll every 50ms so that a
                        # fish that bites immediately after the cast is never missed.
                        bite_detected_early = False
                        bite_confirm_count = 0  # Always reset at the start of a new cast

                        if bite_roi['width'] > 0:
                            # Animation cooldown: let bait-fly + splash finish before watching
                            anim_cooldown = random.uniform(1.5, 2.2)
                            self.root.after(0, lambda: self.status_var.set("Status: 🎣 Bait in the air..."))
                            time.sleep(anim_cooldown)

                            # Baseline grabbed AFTER animation — clean reference
                            screenshot = np.array(sct.grab(bite_roi))
                            hsv = cv2.cvtColor(cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR), cv2.COLOR_BGR2HSV)
                            mask = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 50, 255]))
                            baseline_white = cv2.countNonZero(mask)

                            # Deadline set AFTER cooldown so the full window is used for detection
                            monitoring_deadline = time.time() + random.uniform(2.5, 3.5)
                            confirm_streak = 0

                            self.root.after(0, lambda: self.status_var.set("Status: ⏳ Waiting for Bite..."))
                            while time.time() < monitoring_deadline and self.bot_running:
                                time.sleep(0.025)
                                screenshot = np.array(sct.grab(bite_roi))
                                hsv = cv2.cvtColor(cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR), cv2.COLOR_BGR2HSV)
                                mask = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 50, 255]))
                                current_white = cv2.countNonZero(mask)

                                if current_white > baseline_white + 600:  # Higher threshold = fewer false positives
                                    confirm_streak += 1
                                else:
                                    confirm_streak = 0

                                if confirm_streak >= 5:  # 5 frames × 25ms = ~125ms confirmation
                                    bite_detected_early = True
                                    self.root.after(0, lambda: self.status_var.set("Status: ❗ FISH ON! Hooking..."))
                                    time.sleep(random.uniform(0.10, 0.25))
                                    pydirectinput.keyDown('f')
                                    time.sleep(random.uniform(0.06, 0.14))
                                    pydirectinput.keyUp('f')
                                    time.sleep(random.uniform(0.18, 0.38))
                                    state = 'REELING'
                                    state_start_time = time.time()
                                    lost_target_time = 0
                                    bite_confirm_count = 0
                                    break
                        else:
                            # No bite ROI — plain sleep
                            time.sleep(random.uniform(3.0, 4.5))

                        if not bite_detected_early:
                            # Refresh baseline for WAITING_BITE
                            if bite_roi['width'] > 0:
                                screenshot = np.array(sct.grab(bite_roi))
                                hsv = cv2.cvtColor(cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR), cv2.COLOR_BGR2HSV)
                                mask = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 50, 255]))
                                baseline_white = cv2.countNonZero(mask)
                            bite_confirm_count = 0  # Critical: reset before entering WAITING_BITE
                            state = 'WAITING_BITE'
                            state_start_time = time.time()
                        
                    elif state == 'WAITING_BITE':
                        self.root.after(0, lambda: self.status_var.set("Status: ⏳ Waiting for Bite..."))

                        # Failsafe: 45-second timeout — recast if nothing happened
                        if time.time() - state_start_time > 45.0:
                            bite_confirm_count = 0  # Reset before recasting
                            state = 'CASTING'
                            continue

                        if bite_roi['width'] > 0:
                            screenshot = np.array(sct.grab(bite_roi))
                            hsv = cv2.cvtColor(cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR), cv2.COLOR_BGR2HSV)
                            mask = cv2.inRange(hsv, np.array([0, 0, 200]), np.array([180, 50, 255]))
                            current_white = cv2.countNonZero(mask)

                            # Same gate as CASTING loop: +600 threshold, 5 consecutive frames
                            if current_white > baseline_white + 600:
                                bite_confirm_count += 1
                            else:
                                bite_confirm_count = 0  # Transient — reset

                            if bite_confirm_count >= 5:
                                bite_confirm_count = 0  # Reset for next cycle
                                self.root.after(0, lambda: self.status_var.set("Status: ❗ FISH ON! Hooking..."))
                                time.sleep(random.uniform(0.10, 0.25))
                                pydirectinput.keyDown('f')
                                time.sleep(random.uniform(0.06, 0.14))
                                pydirectinput.keyUp('f')
                                time.sleep(random.uniform(0.18, 0.38))
                                state = 'REELING'
                                state_start_time = time.time()
                                lost_target_time = 0
                        time.sleep(0.025)
                        
                    elif state == 'REELING':
                        self.root.after(0, lambda: self.status_var.set("Status: ⚔️ Reeling Mini-Game..."))
                        
                        # Failsafe: If stuck reeling for over 90 seconds, minigame is bugged. Cancel and recast.
                        if time.time() - state_start_time > 90.0:
                            if current_action != 'NONE':
                                pydirectinput.keyUp(current_action.lower())
                                current_action = 'NONE'
                            state = 'CASTING'
                            continue
                        
                        screenshot = np.array(sct.grab(roi))
                        screenshot_bgr = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
                        hsv_img = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2HSV)
                        
                        # Target (Cyan)
                        mask_t = cv2.inRange(hsv_img, lower_hsv, upper_hsv)
                        target_x = None
                        contours_t, _ = cv2.findContours(mask_t, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        # Increased max limit to 40000 (200x200 pixels) because high-res screens have large UI elements
                        valid_t = [c for c in contours_t if 10 < cv2.contourArea(c) < 40000]
                        if valid_t:
                            c = max(valid_t, key=cv2.contourArea)
                            M = cv2.moments(c)
                            if M["m00"] != 0:
                                target_x = int(M["m10"] / M["m00"])
                                    
                        # Cursor (Yellow)
                        mask_c = cv2.inRange(hsv_img, cursor_lower, cursor_upper)
                        cursor_x = None
                        contours_c, _ = cv2.findContours(mask_c, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        valid_c = [c for c in contours_c if 2 < cv2.contourArea(c) < 40000]
                        if valid_c:
                            c = max(valid_c, key=cv2.contourArea)
                            M = cv2.moments(c)
                            if M["m00"] != 0:
                                cursor_x = int(M["m10"] / M["m00"])

                        if target_x is not None and cursor_x is not None:
                            lost_target_time = 0
                            distance = target_x - cursor_x
                            
                            if distance > tolerance:
                                required_action = 'A' if invert else 'D'
                            elif distance < -tolerance:
                                required_action = 'D' if invert else 'A'
                            else:
                                required_action = 'NONE'
                                
                            abs_distance = abs(distance)
                            
                            # Pro-Gamer Human Logic: Hold key continuously if far, feather/tap if close.
                            # Threshold lowered 50→35: hold aggressively for longer so we close distance faster.
                            if abs_distance > 35:
                                # Far away: Continuous holding for maximum speed
                                if held_key != required_action:
                                    if held_key is not None:
                                        pydirectinput.keyUp(held_key.lower())
                                        time.sleep(random.uniform(0.02, 0.05)) # Quick direction-change reaction
                                    
                                    if required_action != 'NONE':
                                        pydirectinput.keyDown(required_action.lower())
                                        held_key = required_action
                                        current_action = required_action
                                    else:
                                        # Target is inside tolerance while we were holding — release and idle
                                        held_key = None
                                        current_action = 'NONE'
                            else:
                                # Close range: Release continuous holds and use precision feathering
                                if held_key is not None:
                                    pydirectinput.keyUp(held_key.lower())
                                    held_key = None
                                    
                                if required_action != 'NONE':
                                    key = required_action.lower()
                                    # Scale tap length to distance: further = longer tap, closer = shorter
                                    tap_dur = random.uniform(0.016, 0.035) if abs_distance > 18 else random.uniform(0.008, 0.018)
                                    time.sleep(random.uniform(0.003, 0.010)) # Tiny human micro-hesitation
                                    
                                    pydirectinput.keyDown(key)
                                    time.sleep(tap_dur)
                                    pydirectinput.keyUp(key)
                                    current_action = required_action
                                else:
                                    current_action = 'NONE'
                        else:
                            # Lost sight of target
                            if held_key is not None:
                                pydirectinput.keyUp(held_key.lower())
                                held_key = None
                            current_action = 'NONE'
                                
                            if auto_farm:
                                if lost_target_time == 0:
                                    lost_target_time = time.time()
                                elif time.time() - lost_target_time > 4.0:
                                    # Minigame ended
                                    self.root.after(0, lambda: self.status_var.set("Status: Minigame Ended. Claiming fish..."))
                                    time.sleep(random.uniform(0.8, 1.4)) # Faster settle before dismissing summary
                                    
                                    # Click M1 to dismiss the summary screen
                                    pydirectinput.mouseDown(button='left')
                                    time.sleep(random.uniform(0.04, 0.10)) # Quick natural click
                                    pydirectinput.mouseUp(button='left')
                                    
                                    self.root.after(0, lambda: self.status_var.set("Status: Waiting to recast..."))
                                    time.sleep(random.uniform(1.2, 2.2)) # Shorter wait before recasting
                                    state = 'CASTING'
                                    
                        time.sleep(0.002) # 2ms tick — faster loop = better real-time tracking of cursor/target
                        
                except Exception as e:
                    print("Error in bot loop:", e)
                    import traceback
                    err_msg = traceback.format_exc()
                    self.root.after(0, lambda e=err_msg: messagebox.showerror("Bot Crashed", f"Error:\n{e}"))
                    break

        self.root.after(0, self.stop_bot)

if __name__ == "__main__":
    # Enable High DPI awareness on Windows to fix blurry/hazy window scaling
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1) # System DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware() # Fallback for older Windows
        except Exception:
            pass

    root = tk.Tk()
    app = FishingBotGUI(root)
    root.mainloop()
