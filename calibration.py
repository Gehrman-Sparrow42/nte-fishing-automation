import cv2
import numpy as np
import mss

def nothing(x):
    pass

def calibrate():
    """
    Step 1: Captures the screen to let the user draw a box around the fishing bar (ROI).
    Step 2: Opens a trackbar window to tune the HSV values until the target is isolated.
    """
    print("Taking screenshot for ROI selection...")
    
    with mss.mss() as sct:
        # Capture the primary monitor
        monitor = sct.monitors[1] 
        screenshot = np.array(sct.grab(monitor))
        # mss returns BGRA, convert to BGR for OpenCV
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

    # 1. Select ROI
    window_name = "Select Fishing Bar (ROI) - Press ENTER to confirm"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
    
    print("Please draw a rectangle around the fishing bar.")
    print("Press ENTER to confirm your selection.")
    roi = cv2.selectROI(window_name, screenshot, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow(window_name)

    if roi == (0, 0, 0, 0):
        print("No ROI selected. Exiting calibration.")
        return

    x, y, w, h = roi
    print(f"\n[+] Selected ROI: X={x}, Y={y}, Width={w}, Height={h}")
    roi_img = screenshot[int(y):int(y+h), int(x):int(x+w)]

    # 2. Setup Trackbars for HSV Calibration
    cv2.namedWindow("HSV Calibration", cv2.WINDOW_NORMAL)
    cv2.createTrackbar("H Min", "HSV Calibration", 90, 179, nothing)
    cv2.createTrackbar("S Min", "HSV Calibration", 50, 255, nothing)
    cv2.createTrackbar("V Min", "HSV Calibration", 50, 255, nothing)
    cv2.createTrackbar("H Max", "HSV Calibration", 130, 179, nothing)
    cv2.createTrackbar("S Max", "HSV Calibration", 255, 255, nothing)
    cv2.createTrackbar("V Max", "HSV Calibration", 255, 255, nothing)

    print("\n[!] Adjust the trackbars so ONLY the blue target is WHITE.")
    print("[!] Everything else (background, UI) should be BLACK.")
    print("[!] Press 'Q' or 'ESC' when you are done to save the values.")

    h_min, s_min, v_min = 90, 50, 50
    h_max, s_max, v_max = 130, 255, 255

    while True:
        # Convert ROI to HSV for color filtering
        hsv_img = cv2.cvtColor(roi_img, cv2.COLOR_BGR2HSV)

        # Get current trackbar positions
        h_min = cv2.getTrackbarPos("H Min", "HSV Calibration")
        s_min = cv2.getTrackbarPos("S Min", "HSV Calibration")
        v_min = cv2.getTrackbarPos("V Min", "HSV Calibration")
        h_max = cv2.getTrackbarPos("H Max", "HSV Calibration")
        s_max = cv2.getTrackbarPos("S Max", "HSV Calibration")
        v_max = cv2.getTrackbarPos("V Max", "HSV Calibration")

        lower = np.array([h_min, s_min, v_min])
        upper = np.array([h_max, s_max, v_max])

        # Create a mask based on the HSV range
        mask = cv2.inRange(hsv_img, lower, upper)
        result = cv2.bitwise_and(roi_img, roi_img, mask=mask)

        # Show the mask and the filtered result
        cv2.imshow("HSV Calibration", result)
        cv2.imshow("Mask (Target Should be White)", mask)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:  # 'q' or ESC
            break

    cv2.destroyAllWindows()

    # Final Output to user
    print("\n" + "="*40)
    print("CALIBRATION COMPLETE. COPY THESE VALUES INTO main.py:")
    print("="*40)
    print(f"ROI = {{'top': {y}, 'left': {x}, 'width': {w}, 'height': {h}}}")
    print(f"LOWER_HSV = np.array([{h_min}, {s_min}, {v_min}])")
    print(f"UPPER_HSV = np.array([{h_max}, {s_max}, {v_max}])")
    print("="*40)

if __name__ == "__main__":
    calibrate()
