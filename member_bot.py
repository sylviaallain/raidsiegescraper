import mss
import numpy as np
from PIL import Image
import pytesseract

def read_single_line_item(upper_left, debug_img_path=None):
    # Field definitions: (x_offset, y_offset, width, height)
    fields = {
        "Player Name": (112, 21, 250, 35),
        "Level": (53, 83, 45, 25),
        "Clan XP earned": (895, 45, 110, 35)
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
        img = Image.fromarray(crop)
        text = pytesseract.image_to_string(img).strip()
        results[field] = text

        # Draw rectangle for debug
        import cv2
        cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 255), 2)

    # Optionally save debug image
    if debug_img_path:
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