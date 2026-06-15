# 🎣 Neverness to Everness AFK Fishing Bot

An automated, intelligent desktop assistant for the Neverness to Everness fishing mini-game. Features real-time computer vision detection, multi-threaded GUI, automated bite monitoring, and custom-tailored humanized inputs (aim-assist feathering) to avoid macro detection signatures.

---

## ✨ Features

- **📺 Intuitive GUI Setup**: Fully-featured Tkinter dark-theme interface for setting up Regions of Interest (ROI) and calibrating colors.
- **👁️ Computer Vision Tracking**: Uses OpenCV and HSV thresholding to track the target gauge and cursor positions in real-time.
- **🤖 Smart Reeling Logic**: Alternates between holding keys for large distances and micro-taps (feathering) for precision alignment close to the target.
- **🔄 Complete AFK Loop**: Can automatically cast the bait, detect bites, hook the fish, play the reeling minigame, claim the fish, and recast.
- **⌨️ Global Hotkeys & Failsafes**: Start and stop the bot instantly at any time via F8 (Start) and F9 (Stop/Emergency Exit).

---

## 📋 Requirements & Dependencies

- **Operating System**: Windows (required for key/mouse event simulation)
- **Python Version**: Python 3.8 or higher
- **Permissions**: **Must be run as Administrator** (required by the `keyboard` library to intercept/inject global inputs).

To install the required dependencies:
```bash
pip install -r requirements.txt
```

---

## 🛠️ Calibration & Setup Guide

Before launching the bot, you must calibrate it to match your game's screen resolution and settings. In the GUI, click **Show Calibration & Setup (Steps 1 & 2)** to expand the configuration section:

### Step 1: Draw the Scanning Regions
1. Start the bot (see [Running the Bot](#-running-the-bot) below).
2. Click **1a. Select Fishing Bar Area** to capture the screen. Draw a box around the entire horizontal reel bar (where the target and cursor slide left/right) and press **ENTER**.
3. Click **1b. Select 'Fish on Hook!' Area** and draw a box around the region where the "Fish on the hook!" notification appears when a fish bites, then press **ENTER**.

### Step 2: Auto-Detect Colors
1. Launch the fishing mini-game so the target bar is visible.
2. Click **2a. Detect CYAN Target**. On the window that opens, click directly on the cyan target marker. Make sure the mask view on the right displays the target clearly in white. Press **Q** to save.
3. Click **2b. Detect YELLOW Cursor**. Click directly on the yellow slider cursor. Verify it's isolated on the mask, then press **Q** to save.

### Step 3: Configure Settings
- **Enable 100% AFK Auto-Farm Loop**: Check this to automatically cast bait, detect bites, hook, reel, and loop.
- **Invert Controls**: Toggle this if the bot moves the cursor in the opposite direction of the target.
- **Tolerance**: Adjusts the sensitivity of the aim assist. Higher values reduce key press frequency.

---

## 🚀 Running the Bot

Because the bot interacts with input APIs, it **must run with administrator privileges**:

1. Open a terminal (CMD or PowerShell) **as Administrator**.
2. Run the script:
   ```bash
   python app.py
   ```
   *(Alternatively, run `Start_Fishing_Bot.bat` as Administrator to launch the GUI in windowless mode).*

3. **Hotkeys**:
   - Press **F8** to start the bot loop.
   - Press **F9** to halt the bot immediately.

---

## ⚠️ Disclaimer & Safety Warning

This project is created for educational and personal use only. Using third-party automation tools or bots in online games may violate the game's Terms of Service (ToS) and could result in account restriction or ban. Use at your own discretion.
