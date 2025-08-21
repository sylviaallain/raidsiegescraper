import cv2
import numpy as np
import mss
import pytesseract
from PIL import Image

# Paths to your template images
VICTORY_TEMPLATE = "templates/victory.png"
DEFEAT_TEMPLATE = "templates/defeat.png"

def detect_template(template_path, screenshot, threshold=0.8):
    template = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
    if template is None:
        raise FileNotFoundError(f"Couldn't load {template_path}")
    if template.shape[2] == 4:
        template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    tH, tW = template_gray.shape[:2]

    res = cv2.matchTemplate(screenshot, template_gray, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)
    points = list(zip(*loc[::-1]))

    # Non-Maximum Suppression
    def non_max_suppression(points, tW, tH, overlapThresh=0.3):
        if len(points) == 0:
            return []
        boxes = np.array([[x, y, x + tW, y + tH] for (x, y) in points])
        pick = []
        x1 = boxes[:,0]
        y1 = boxes[:,1]
        x2 = boxes[:,2]
        y2 = boxes[:,3]
        area = (x2 - x1 + 1) * (y2 - y1 + 1)
        idxs = np.argsort(y2)
        while len(idxs) > 0:
            last = idxs[-1]
            pick.append(last)
            xx1 = np.maximum(x1[last], x1[idxs[:-1]])
            yy1 = np.maximum(y1[last], y1[idxs[:-1]])
            xx2 = np.minimum(x2[last], x2[idxs[:-1]])
            yy2 = np.minimum(y2[last], y2[idxs[:-1]])
            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)
            overlap = (w * h) / area[idxs[:-1]]
            idxs = np.delete(
                idxs, np.concatenate(([len(idxs)-1], np.where(overlap > overlapThresh)[0]))
            )
        return [points[i] for i in pick]

    filtered_points = non_max_suppression(points, tW, tH, overlapThresh=0.3)
    return filtered_points, tW, tH

def extract_names(scr, icon_points, icon_width, icon_height, debug_img_path=None):
    # Offsets and box size (adjust as needed)
    left_offset_x = -310 
    left_offset_y = -70 
    right_offset_x = 175
    right_offset_y = -70
    name_box_width = 275
    name_box_height = 75

    # Make a copy for debug drawing
    debug_img = scr.copy() if debug_img_path else None

    results = []
    for (x, y) in icon_points:
        left_x1 = x + left_offset_x
        left_y1 = y + left_offset_y
        left_x2 = left_x1 + name_box_width
        left_y2 = left_y1 + name_box_height

        right_x1 = x + right_offset_x
        right_y1 = y + right_offset_y
        right_x2 = right_x1 + name_box_width
        right_y2 = right_y1 + name_box_height

        # Draw rectangles on debug image
        if debug_img is not None:
            cv2.rectangle(debug_img, (left_x1, left_y1), (left_x2, left_y2), (255, 255, 0), 2)   # Cyan
            cv2.rectangle(debug_img, (right_x1, right_y1), (right_x2, right_y2), (255, 0, 255), 2) # Magenta

        # Crop regions and convert to PIL Image for pytesseract
        left_img = Image.fromarray(scr[left_y1:left_y2, left_x1:left_x2])
        right_img = Image.fromarray(scr[right_y1:right_y2, right_x1:right_x2])

        left_name = pytesseract.image_to_string(left_img).strip()
        right_name = pytesseract.image_to_string(right_img).strip()

        results.append((left_name, right_name))

    # Save debug image if requested
    if debug_img_path and debug_img is not None:
        cv2.imwrite(debug_img_path, debug_img)

    return results

# Grab screenshot
with mss.mss() as sct:
    mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
    scr = np.array(sct.grab(mon))[:, :, :3].copy()
scr_gray = cv2.cvtColor(scr, cv2.COLOR_BGR2GRAY)

# Detect victories
victory_points, vW, vH = detect_template(VICTORY_TEMPLATE, scr_gray)
for pt in victory_points:
    cv2.rectangle(scr, pt, (pt[0] + vW, pt[1] + vH), (0, 255, 0), 2)

# Detect defeats
defeat_points, dW, dH = detect_template(DEFEAT_TEMPLATE, scr_gray)
for pt in defeat_points:
    cv2.rectangle(scr, pt, (pt[0] + dW, pt[1] + dH), (0, 0, 255), 2)

print(f"Victory image detected {len(victory_points)} time(s) on screen!")
print(f"Defeat image detected {len(defeat_points)} time(s) on screen!")

# Save the result image with detections
cv2.imwrite("detection_result.png", scr)

# Sort detected icons by y-coordinate (top to bottom)
victory_points_sorted = sorted(victory_points, key=lambda pt: pt[1])
defeat_points_sorted = sorted(defeat_points, key=lambda pt: pt[1])

# Use sorted lists for name extraction and reporting
victory_names = extract_names(scr, victory_points_sorted, vW, vH, debug_img_path="victory_names_debug.png")
defeat_names = extract_names(scr, defeat_points_sorted, dW, dH, debug_img_path="defeat_names_debug.png")

# Combine victories and defeats with labels
all_results = [
    *[(pt, 'victory', vW, vH) for pt in victory_points],
    *[(pt, 'defeat', dW, dH) for pt in defeat_points]
]

# Sort all by y-coordinate (top to bottom)
all_results_sorted = sorted(all_results, key=lambda item: item[0][1])

for idx, (pt, result_type, w, h) in enumerate(all_results_sorted):
    names = extract_names(scr, [pt], w, h)
    left, right = names[0]
    if result_type == 'victory':
        print(f"{idx+1}. Victory: {left} defeated {right}")
    else:
        print(f"{idx+1}. Defeat: {left} was defeated by {right}")