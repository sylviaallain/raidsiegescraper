# bot.py
import pyautogui
import time
from victory_detect import report_victories

SLEEP_TIME = .75  # Time to wait between actions

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

exit_coords = (1198, 429)
tower_defense_report_coords = (703, 112)
post_defense_report_coords = (422, 110)

pyautogui.moveTo(*exit_coords)
pyautogui.click()
time.sleep(SLEEP_TIME)


for post, coords in posts.items():
    # Move to the post and click
    x, y = coords
    pyautogui.moveTo(x, y)
    pyautogui.click()
    time.sleep(SLEEP_TIME)
    # Move to the post defense report button and click
    pyautogui.moveTo(*post_defense_report_coords)
    pyautogui.click()
    time.sleep(SLEEP_TIME)
    results = report_victories()
    print(f"~~~RESULTS FOR {post}~~~")
    for idx, result in enumerate(results):
        if result[0] == 'victory':
            print(f"{idx+1}. Victory: {result[1]} defeated {result[2]}")
        else:
            print(f"{idx+1}. Defeat: {result[1]} was defeated by {result[2]}")
    print("~~~~~~~~~~~~~~~~~~~~~~")

    # Exit the report
    pyautogui.moveTo(*exit_coords)
    pyautogui.click()
    time.sleep(SLEEP_TIME)
