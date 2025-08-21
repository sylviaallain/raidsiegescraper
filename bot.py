# bot.py
import pyautogui
import time
import keyboard
from PIL import ImageGrab
import pytesseract

SLEEP_TIME = 1  # Time to wait between actions

# List of static (x, y) coordinates for each icon/post to click
posts = {
    "Post1": (394, 602),
    "Post2": (521, 770),
    "Post3": (914, 658),
    "Post4": (1168, 529),
    "Post5": (1385, 488),
    "Post6": (1225, 427),
    "Post7": (846, 534),
    "Post8": (654, 590),
    "Post9": (446, 498),
    "Post10": (598, 500),
    "Post11": (771, 488),
    "Post12": (998, 476),
    "Post13": (1175, 299),
    "Post14": (832, 397),
    "Post15": (694, 412),
    "Post16": (372, 263),
    "Post17": (971, 231),
    "Post18": (1094, 199)
}

exit_coords = (1198, 429)
defense_report_coords = (703, 112)

pyautogui.moveTo(*exit_coords)
pyautogui.click()
time.sleep(SLEEP_TIME)

stop = False

def stop_script():
    global stop
    stop = True

keyboard.add_hotkey('esc', stop_script)

for x, y in posts.values():
    if stop:
        print("Stopped by user.")
        break
    pyautogui.moveTo(x, y)
    pyautogui.click()
    time.sleep(SLEEP_TIME)
    pyautogui.moveTo(*exit_coords)
    pyautogui.click()
    time.sleep(SLEEP_TIME)
