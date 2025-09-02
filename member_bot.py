import mss
import numpy as np
from PIL import Image
import pytesseract
import cv2
import pyautogui
import time
import csv
from datetime import datetime
import argparse
import os
import sqlite3

def read_single_line_item(upper_left, debug_img_path=None):
    # Field definitions: (x_offset, y_offset, width, height)
    fields = {
        "Player Name": (112, 16, 250, 55),
        "Level": (53, 81, 50, 29),
        "Clan XP earned": (895, 38, 110, 50)
    }

    # Take a screenshot of the whole screen
    with mss.mss() as sct:
        mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
        scr = np.array(sct.grab(mon))[:, :, :3]

    results = {}
    debug_img = scr.copy()

    for field, (x_off, y_off, w, h) in fields.items():
        x1 = upper_left[0] + x_off
        y1 = upper_left[1] + y_off
        x2 = x1 + w
        y2 = y1 + h

        crop = scr[y1:y2, x1:x2]
        if field == "Level":
            hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 60, 255])
            mask_white = cv2.inRange(hsv, lower_white, upper_white)
            filtered = cv2.bitwise_and(crop, crop, mask=mask_white)
            gray = cv2.cvtColor(filtered, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            img = Image.fromarray(thresh)
            img = img.resize((img.width * 3, img.height * 3), Image.BICUBIC)
            custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
            text = pytesseract.image_to_string(img, config=custom_config).strip()
            try:
                level_int = int(text)
                if level_int > 100:
                    level_int = level_int % 100
                text = str(level_int)
            except ValueError:
                pass
        elif field == "Clan XP earned":
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            # Thicken digits using dilation
            kernel = np.ones((2,2), np.uint8)  # You can try (3,3) for even thicker
            thickened = cv2.dilate(thresh, kernel, iterations=1)
            img = Image.fromarray(thickened)
            img = img.resize((img.width * 10, img.height * 10), Image.BICUBIC)
            from PIL import ImageFilter
            img = img.filter(ImageFilter.SHARPEN)
            custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789,'
            text = pytesseract.image_to_string(img, config=custom_config).strip()
            img.save(f"debug/xp_field_{y1}_{x1}.png")
            # If OCR detects '0', set field to 0
            if text is None or text == "":
                text = "0"
        else:
            img = Image.fromarray(crop)
            text = pytesseract.image_to_string(img).strip()
        results[field] = text

        cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 255), 2)

    # Optionally save debug image
    if debug_img_path:
        Image.fromarray(debug_img).save(debug_img_path)

    return results

def read_all_line_items(start_upper_left, num_items=5, item_height=141, debug_img_path=None):
    results = []
    debug_img = None

    # Take a screenshot of the whole screen
    with mss.mss() as sct:
        mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
        scr = np.array(sct.grab(mon))[:, :, :3]

    for i in range(num_items):
        upper_left = (start_upper_left[0], start_upper_left[1] + i * item_height)
        item_result = read_single_line_item(upper_left)
        results.append(item_result)

        # Draw rectangles for debug image
        if debug_img is None:
            debug_img = scr.copy()
        for field, (x_off, y_off, w, h) in {
                "Player Name": (112, 16, 250, 55),
                "Level": (53, 81, 50, 29),
                "Clan XP earned": (895, 38, 110, 50)
        }.items():
            x1 = upper_left[0] + x_off
            y1 = upper_left[1] + y_off
            x2 = x1 + w
            y2 = y1 + h
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 255), 2)

    # Optionally save debug image
    if debug_img_path and debug_img is not None:
        Image.fromarray(debug_img).save(debug_img_path)

    return results

def scroll_and_read_all_items_drag(start_upper_left, scrollbar_coords, drag_pixels=707, num_items_per_page=5, item_height=141, num_pages=2, debug_img_path=None):
    all_results = []
    last_page_y = 308  # Y coordinate of start of last page
    for page in range(num_pages):
        # For the last page, adjust the start Y coordinate
        if page == num_pages - 1:
            page_start = (start_upper_left[0], last_page_y)
        else:
            page_start = start_upper_left
        # Read items on the current page
        page_results = read_all_line_items(
            start_upper_left=page_start,
            num_items=num_items_per_page,
            item_height=item_height,
            debug_img_path=f"debug/member_bot_allitems_page{page+1}.png" if debug_img_path else None
        )
        all_results.extend(page_results)
        # Drag the scrollbar down by the specified pixel amount, except after last page
        if page < num_pages - 1:
            pyautogui.moveTo(*scrollbar_coords)
            pyautogui.mouseDown()
            pyautogui.moveRel(0, drag_pixels, duration=0.3)
            time.sleep(0.5)  # Hold the mouse for half a second before releasing
            pyautogui.mouseUp()
            time.sleep(0.5)  # Wait for UI to update
    return all_results

def save_to_csv(items, filename=None):
    # Deduplicate by Player Name, skip invalid names
    deduped = {}
    for item in items:
        name = item.get("Player Name", "").strip()
        # Skip if name is empty or looks like a header
        if not name or ("Player" in name or "Power" in name):
            continue
        if name not in deduped:
            deduped[name] = item
    # Write to CSV
    fieldnames = ["Player Name", "Level", "Clan XP earned"]
    if filename is None:
        date_str = datetime.now().strftime("%Y_%m_%d")
        filename = f"member_records/members_{date_str}.csv"
    with open(filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in deduped.values():
            writer.writerow(record)

def clear_debug_folder():
    debug_folder = "debug"
    if os.path.exists(debug_folder):
        for filename in os.listdir(debug_folder):
            file_path = os.path.join(debug_folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

def init_members_db(db_path="raid.db"):
    os.makedirs("member_records", exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT,
            level TEXT,
            clan_xp_earned TEXT,
            is_opponent INTEGER,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_members_to_db(items, is_opponent, db_path="raid.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d")
    for item in items:
        name = item.get("Player Name", "").strip()
        # Skip if name is empty or looks like a header
        if not name or ("Player" in name or "Power" in name):
            continue
        level = item.get("Level", "").strip()
        clan_xp_earned = item.get("Clan XP earned", "").strip()
        c.execute("""
            INSERT INTO members (player_name, level, clan_xp_earned, is_opponent, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (name, level, clan_xp_earned, int(is_opponent), timestamp))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    clear_debug_folder()  # Clear debug files at the start

    parser = argparse.ArgumentParser()
    parser.add_argument("--is_opponent", action="store_true", help="Read opponent member list")
    args = parser.parse_args()

    scrollbar_coords = (1597, 1019)  # <-- Adjust to your scrollbar's position
    exit_coords = (1198, 429) # Coordinates to hide terminal

    pyautogui.moveTo(*exit_coords)
    pyautogui.click()

    opponent_coords = (330, 213)  # Coordinates of the first item in the opponent list
    member_coords = (339, 313)    # Coordinates of the first item in the member list
    date_str = datetime.now().strftime("%Y_%m_%d")

    if args.is_opponent:
        start_coords = opponent_coords
        filename = f"member_records/opponents_{date_str}.csv"
    else:
        start_coords = member_coords
        filename = f"member_records/members_{date_str}.csv"

    all_items = scroll_and_read_all_items_drag(
        start_upper_left=start_coords,
        scrollbar_coords=scrollbar_coords,
        drag_pixels= -884,  # Has one overlapping member: -709,
        num_items_per_page=5,
        item_height=142,
        num_pages=6,  # True pages = 6
        debug_img_path="debug/member_bot_allitems.png"
    )
    for idx, item in enumerate(all_items, 1):
        print(f"Line Item {idx}:")
        for k, v in item.items():
            print(f"  {k}: {v}")
    save_to_csv(all_items, filename)
    init_members_db()
    save_members_to_db(all_items, args.is_opponent)