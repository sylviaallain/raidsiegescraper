# siege_bot.py
import pyautogui
import time
import mss
import numpy as np
from PIL import Image
import pytesseract
import cv2
import random

SLEEP_TIME = 1  # Time to wait between actions

# List of static (x, y) coordinates for each icon/post to click
posts = {
    "Post1": (394, 602),
    "Post2": (521, 770),
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
    "DefenseTower1": (1342, 291),
    "DefenseTower2": (265, 352),
    "DefenseTower3": (890, 275),
    "DefenseTower4": (928, 157),
    "DefenseTower5": (649, 188),
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

if __name__ == "__main__":
    start_coords = (16, 291)
    last_start_coords = (16, 748) # start coords for last line item
    items = {
        "Player 1 Name":  (79,  60, 285, 36),
        "Player 2 Name":  (565, 60, 285, 36),
        "Player 1 Power": (232, 219,  85, 25),
        "Battle Status":  (392, 133, 140, 75),
        "Battle Log":     (753, 262, 157, 34),
    }

    exit_coords = (1198, 429)
    tower_defense_report_coords = (703, 112)
    post_defense_report_coords = (422, 110)
    line_item_height = 399 # Height of each line item block
    sub_line_item_height = 168 # Height of each sub-item within a line item

    pyautogui.moveTo(*exit_coords)
    pyautogui.click()
    random_sleep()

    all_results = {}

    for post, coords in posts.items():
        # Move to the post and click
        x, y = coords
        pyautogui.moveTo(x, y)
        pyautogui.click()
        random_sleep()
        # Move to the post defense report button and click
        pyautogui.moveTo(*post_defense_report_coords)
        pyautogui.click()
        random_sleep()

        result = read_siege_line_item(start_coords, items, post_name=post)
        # Only add results where battle status is not "Unknown"
        if result.get("Battle Status", "Unknown") != "Unknown":
            all_results[post] = result

        # Exit the report
        pyautogui.moveTo(*exit_coords)
        pyautogui.click()
        random_sleep()

    # Print formatted results
    import json
    print(json.dumps(all_results, indent=4, ensure_ascii=False))


