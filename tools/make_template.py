# make_template_and_test.py
import os, time
import numpy as np
import cv2, mss, pyautogui as pag

BASE = os.path.dirname(os.path.abspath(__file__))
TPL_PATH = os.path.join(BASE, "templates", "victory.png")
WIDTH, HEIGHT = 140, 75

os.makedirs(os.path.dirname(TPL_PATH), exist_ok=True)

def grab_primary():
    with mss.mss() as sct:
        mon = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
        img = np.array(sct.grab(mon))   # BGRA
        return img[:, :, :3], mon       # BGR

def save_crop_around_cursor(box_w=WIDTH, box_h=HEIGHT):
    screen_bgr, mon = grab_primary()
    x, y = pag.position()
    # Clamp to screen bounds
    x1 = max(0, x - box_w//2)
    y1 = max(0, y - box_h//2)
    x2 = min(screen_bgr.shape[1], x1 + box_w)
    y2 = min(screen_bgr.shape[0], y1 + box_h)
    crop = screen_bgr[y1:y2, x1:x2].copy()
    if crop.size == 0:
        raise RuntimeError("Empty crop; check cursor position.")
    cv2.imwrite(TPL_PATH, crop)
    print(f"Saved template to {TPL_PATH} with shape {crop.shape}")

def match_once():
    # Load template (ensure 3-channel BGR)
    tpl = cv2.imread(TPL_PATH, cv2.IMREAD_UNCHANGED)
    if tpl is None:
        raise FileNotFoundError(TPL_PATH)
    if tpl.ndim == 3 and tpl.shape[2] == 4:
        tpl = cv2.cvtColor(tpl, cv2.COLOR_BGRA2BGR)

    scr, _ = grab_primary()
    res = cv2.matchTemplate(scr, tpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    print("Confidence:", round(float(max_val), 3))
    print("True" if max_val >= 0.80 else "False")

if __name__ == "__main__":
    input("Hover the cursor over the icon, then press ENTER…")
    time.sleep(0.1)
    save_crop_around_cursor()
    match_once()
