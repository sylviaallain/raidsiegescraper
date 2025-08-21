import cv2
import numpy as np
import mss

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