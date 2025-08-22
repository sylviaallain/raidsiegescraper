import pyautogui

print("Click anywhere on the screen. Press Ctrl+C to exit.")

try:
    while True:
        x, y = pyautogui.position()
        input("Move your mouse to a spot and press Enter to record its coordinates...")
        x, y = pyautogui.position()
        print(f"Recorded coordinates: ({x}, {y})")
except KeyboardInterrupt:
    print("\nDone recording coordinates.")
    