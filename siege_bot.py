# siege_bot.py
import pyautogui
import time
import mss
import numpy as np
from PIL import Image
import pytesseract
import cv2
import random
import os

SLEEP_TIME = 1  # Time to wait between actions

# List of static (x, y) coordinates for each icon/post to click
posts = {
    # "Post1": (394, 602),
    # "Post2": (521, 770),
    # "Post3": (914, 658),
    # "Post4": (1168, 529),
    # "Post5": (1385, 488),
    # "Post6": (1225, 427),
    # "Post7": (846, 534),
    # "Post8": (654, 590),
    # "Post9": (446, 498),
    # "Post10": (598, 500),
    # "Post11": (771, 488),
    # "Post12": (998, 476),
    # "Post13": (1175, 299),
    # "Post14": (832, 397),
    # "Post15": (694, 412),
    # "Post16": (372, 263),
    # "Post17": (971, 231),
    # "Post18": (1094, 199)
}

def_towers = {
    # "DefenseTower1": (1342, 291),
    # "DefenseTower2": (265, 352),
    # "DefenseTower3": (890, 275),
    # "DefenseTower4": (928, 157),
    "DefenseTower5": (649, 188),
}

stronghold = {
    "Stronghold": (787, 130),
}

def read_siege_line_item(start_coords, items, post_name=""):
    print (f"~~~~~Results for: {post_name}~~~~~")
    # Take a screenshot of the whole screen
    with mss.mss() as sct:
        mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
        scr = np.array(sct.grab(mon))[:, :, :3]

    results = {}
    for field, (x_off, y_off, w, h) in items.items():
        x1 = start_coords[0] + x_off
        y1 = start_coords[1] + y_off
        x2 = x1 + w
        y2 = y1 + h

        crop = scr[y1:y2, x1:x2]

        if field == "Battle Status":
            # Use red channel for template matching (red icon on blue background)
            crop_red = crop[:, :, 2]
            victory_template = cv2.imread("templates/victory.png", cv2.IMREAD_COLOR)
            defeat_template = cv2.imread("templates/defeat.png", cv2.IMREAD_COLOR)
            victory_red = victory_template[:, :, 2]
            defeat_red = defeat_template[:, :, 2]
            # Resize templates to match crop size if needed
            victory_red = cv2.resize(victory_red, (crop_red.shape[1], crop_red.shape[0]))
            defeat_red = cv2.resize(defeat_red, (crop_red.shape[1], crop_red.shape[0]))
            # Optionally enhance contrast
            crop_eq = cv2.equalizeHist(crop_red)
            victory_eq = cv2.equalizeHist(victory_red)
            defeat_eq = cv2.equalizeHist(defeat_red)
            # Template matching
            victory_res = cv2.matchTemplate(crop_eq, victory_eq, cv2.TM_CCOEFF_NORMED)
            defeat_res = cv2.matchTemplate(crop_eq, defeat_eq, cv2.TM_CCOEFF_NORMED)
            victory_score = victory_res.max()
            defeat_score = defeat_res.max()
            print(f"Victory score: {victory_score}, Defeat score: {defeat_score}")
            if victory_score > defeat_score and victory_score > 0.5:
                results[field] = "Victory"
            elif defeat_score > victory_score and defeat_score > 0.5:
                results[field] = "Defeat"
            else:
                results[field] = "Unknown"
            # Save the crop for debugging
            Image.fromarray(crop_eq).save(f"debug/battle_status_crop_{post_name}.png")
        elif field == "Player 1 Power":
            # Preprocess for alphanumeric OCR (letters and numbers)
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            kernel = np.ones((2,2), np.uint8)
            thickened = cv2.dilate(thresh, kernel, iterations=1)
            img = Image.fromarray(thickened)
            img = img.resize((img.width * 10, img.height * 10), Image.BICUBIC)
            from PIL import ImageFilter
            img = img.filter(ImageFilter.SHARPEN)
            # Allow letters, numbers, comma, and space
            custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789, '
            text = pytesseract.image_to_string(img, config=custom_config).strip()
            text = text.replace(",", ".")
            results[field] = text
            # Save debug image for Player 1 Power
            img.save(f"debug/player1_power_crop_{post_name}.png")
        else:
            img = Image.fromarray(crop)
            text = pytesseract.image_to_string(img).strip()
            results[field] = text

    # Optionally, draw rectangles for debug
    scr_bgr = cv2.cvtColor(scr, cv2.COLOR_RGB2BGR)
    for field, (x_off, y_off, w, h) in items.items():
        x1 = start_coords[0] + x_off
        y1 = start_coords[1] + y_off
        x2 = x1 + w
        y2 = y1 + h
        cv2.rectangle(scr_bgr, (x1, y1), (x2, y2), (0, 255, 255), 2)
    scr_rgb = cv2.cvtColor(scr_bgr, cv2.COLOR_BGR2RGB)
    file_name = f"debug/siege_line_item_debug{post_name}.png"
    Image.fromarray(scr_rgb).save(file_name)

    return results

def random_sleep():
    time.sleep(random.uniform(1, 1.5))

def read_tower_items(start_coords, last_start_coords, items, line_item_height, tower_name, scrollbar_coords, drag_pixels):
    results = []
    # Read first two line items (first page)
    for i in range(2):
        item_coords = (start_coords[0], start_coords[1] + i * line_item_height)
        result = read_siege_line_item(item_coords, items, post_name=f"{tower_name}_item{i+1}")
        if result.get("Battle Status", "Unknown") != "Unknown":
            results.append(result)
    # Move mouse to scroller at scrollbar_coords before dragging
    pyautogui.moveTo(*scrollbar_coords)
    pyautogui.mouseDown()
    pyautogui.moveRel(0, -drag_pixels, duration=0.3)
    time.sleep(0.5)  # Hold the mouse for half a second before releasing
    pyautogui.mouseUp()
    # Read third line item
    result = read_siege_line_item(last_start_coords, items, post_name=f"{tower_name}_item3")
    if result.get("Battle Status", "Unknown") != "Unknown":
        results.append(result)
    return results

# Constants for coordinates and item definitions
START_COORDS = (16, 337)
LAST_START_COORDS = (16, 748) # start coords for last line item
EXIT_COORDS = (1198, 429)
TOWER_DEFENSE_REPORT_COORDS = (703, 112)
POST_DEFENSE_REPORT_COORDS = (422, 110)
LINE_ITEM_HEIGHT = 259 # Height of each line item block
SUB_LINE_ITEM_HEIGHT = 168 # Height of each sub-item within a line item
GROUP_HEADER_HEIGHT = 259 # Height of the group header
DRAG_PIXELS_INITIAL = 135 # Pixels to drag the scrollbar down so third item is visible
ITEMS = {
    "Player 1 Name":  (79,  14, 282, 36),
    "Player 2 Name":  (565, 14, 282, 36),
    "Player 1 Power": (232, 173,  85, 25),
    "Battle Status":  (392, 87, 140, 75),
    "Battle Log":     (653, 216, 260, 34),
}

def clear_debug_folder():
    debug_folder = "debug"
    if os.path.exists(debug_folder):
        for filename in os.listdir(debug_folder):
            file_path = os.path.join(debug_folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

if __name__ == "__main__":
    clear_debug_folder()  # Clear debug files at the start

    pyautogui.moveTo(*EXIT_COORDS)
    pyautogui.click()
    random_sleep()

    all_results = {}

    # Read posts as before
    for post, coords in posts.items():
        x, y = coords
        pyautogui.moveTo(x, y)
        pyautogui.click()
        random_sleep()
        pyautogui.moveTo(*POST_DEFENSE_REPORT_COORDS)
        pyautogui.click()
        random_sleep()

        result = read_siege_line_item(START_COORDS, ITEMS, post_name=post)
        if result.get("Battle Status", "Unknown") != "Unknown":
            all_results[post] = result

        pyautogui.moveTo(*EXIT_COORDS)
        pyautogui.click()
        random_sleep()

    # Combine defense towers and stronghold
    towers = {**def_towers, **stronghold}
    for tower_name, coords in towers.items():
        pyautogui.moveTo(*coords)
        pyautogui.click()
        random_sleep()
        pyautogui.moveTo(*TOWER_DEFENSE_REPORT_COORDS)
        pyautogui.click()
        random_sleep()
        tower_results = read_tower_items(
            START_COORDS, LAST_START_COORDS, ITEMS, LINE_ITEM_HEIGHT, tower_name, LAST_START_COORDS, DRAG_PIXELS_INITIAL
        )
        if tower_results:
            all_results[tower_name] = tower_results
        pyautogui.moveTo(*EXIT_COORDS)
        pyautogui.click()
        random_sleep()

    import json
    print(json.dumps(all_results, indent=4, ensure_ascii=False))


