import mss
import numpy as np
from PIL import Image
import pytesseract
import cv2

def read_single_line_item(upper_left, debug_img_path=None):
    # Field definitions: (x_offset, y_offset, width, height)
    fields = {
        "Player Name": (112, 21, 250, 35),
        "Level": (53, 80, 45, 27),
        "Clan XP earned": (895, 45, 110, 40)
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

        # Crop region
        crop = scr[y1:y2, x1:x2]
        if field == "Level":
            # Convert to grayscale
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            alpha = 2.0
            beta = -160
            contrasted = cv2.convertScaleAbs(gray, alpha=alpha, beta=beta)
            _, thresh = cv2.threshold(contrasted, 180, 255, cv2.THRESH_BINARY)
            kernel = np.ones((2,2), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            img = Image.fromarray(cleaned)
            img = img.resize((img.width * 2, img.height * 2), Image.BICUBIC)
            img.save(f"debug/level_field_{y1}_{x1}.png")
            custom_config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
            text = pytesseract.image_to_string(img, config=custom_config).strip()
        else:
            img = Image.fromarray(crop)
            text = pytesseract.image_to_string(img).strip()
        results[field] = text

        # Draw rectangle for debug
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
            "Player Name": (112, 21, 250, 35),
            "Level": (53, 83, 45, 25),
            "Clan XP earned": (895, 45, 110, 35)
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

if __name__ == "__main__":
    line_item = read_single_line_item(
        upper_left=(339, 313),
        debug_img_path="debug/member_bot_lineitem.png"
    )
    print("Line Item OCR Result:")
    for k, v in line_item.items():
        print(f"{k}: {v}")

    all_items = read_all_line_items(
        start_upper_left=(339, 313),
        num_items=5,
        item_height=141,
        debug_img_path="debug/member_bot_allitems.png"
    )
    for idx, item in enumerate(all_items, 1):
        print(f"Line Item {idx}:")
        for k, v in item.items():
            print(f"  {k}: {v}")