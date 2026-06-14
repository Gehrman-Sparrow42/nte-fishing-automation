import cv2
import numpy as np
import mss
import pydirectinput
import keyboard
import time
import random
import sys

# =====================================================================
# CONFIGURATION (Paste values from calibration.py here)
# =====================================================================
ROI = {'top': 500, 'left': 800, 'width': 300, 'height': 50}
LOWER_HSV = np.array([90, 50, 50])
UPPER_HSV = np.array([130, 255, 255])

# BOT LOGIC CONFIGURATION
TOLERANCE = 15       # Margin of error (in pixels). If within this, don't press keys.
START_KEY = 'f8'     # Key to start the bot
KILL_SWITCH = 'f9'   # Emergency stop key

# Reference X: The fixed center point of the cursor.
# If the cursor defaults to the exact middle of the ROI, we use half the width.
REF_X = ROI['width'] // 2  
# =====================================================================

def press_key_humanized(key):
    """
    Simulates a non-mechanical key tap.
    Adds a very short, random delay between pressing and releasing the key.
    """
    pydirectinput.keyDown(key)
    time.sleep(random.uniform(0.01, 0.04)) # Imperfect hold duration
    pydirectinput.keyUp(key)

def main():
    print(f"[*] Fishing Bot initialized.")
    print(f"[*] Press '{START_KEY}' to START. Press '{KILL_SWITCH}' to STOP.")
    
    # Wait for the user to press the start key
    keyboard.wait(START_KEY)
    print("\n[+] Bot Started! Scanning screen...")
    
    current_action = 'NONE'
    
    # Initialize MSS for fast screen capture
    with mss.mss() as sct:
        while True:
            # 1. Kill Switch Check
            if keyboard.is_pressed(KILL_SWITCH):
                print("\n[!] Kill switch activated. Exiting...")
                sys.exit(0)
                
            # 2. Capture Region of Interest (ROI)
            screenshot = np.array(sct.grab(ROI))
            
            # 3. Process image to locate the blue target
            # Convert BGRA (mss format) directly to HSV
            hsv_img = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2HSV)
            mask = cv2.inRange(hsv_img, LOWER_HSV, UPPER_HSV)
            
            # 4. Find the centroid of the target
            target_x = None
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Filter out small noise, grab the largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > 20: 
                    M = cv2.moments(largest_contour)
                    if M["m00"] != 0:
                        target_x = int(M["m10"] / M["m00"])
            
            # 5. Logic and Humanized Decision Making
            if target_x is not None:
                # Calculate how far the target is from our reference point
                distance = target_x - REF_X
                
                # Determine what we should do
                if distance > TOLERANCE:
                    required_action = 'D'
                elif distance < -TOLERANCE:
                    required_action = 'A'
                else:
                    required_action = 'NONE'
                
                # Humanization 1: Reaction Time Delay on Direction Change
                if required_action != current_action:
                    # If we need to change our input, we don't react instantly
                    time.sleep(random.uniform(0.08, 0.18))
                    current_action = required_action
                
                # Humanization 2 & 3: Execute Action with Imperfect Taps
                if current_action == 'D':
                    press_key_humanized('d')
                elif current_action == 'A':
                    press_key_humanized('a')
                
            # Small sleep to prevent 100% CPU usage and simulate a tick rate
            time.sleep(0.005)

if __name__ == "__main__":
    # Safety delay on launch
    time.sleep(1)
    main()
