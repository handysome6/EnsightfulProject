import cv2
import numpy as np
from qt.qt_new import ProjectWindow
import sys
import logging
from pathlib import Path
logFormatter = logging.Formatter("[%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.FATAL)
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


total = 0
for i in range(14000):
    left = f"./datasets/0816_6mm_IMX477_jetson/lnr/left-output{i}.jpg"
    right = f"./datasets/0816_6mm_IMX477_jetson/lnr/right-output{i}.jpg"
    try:
        left = cv2.imread(left)
        right = cv2.imread(right)
        if left is None:
            continue
        total += 1
        print(f"stacking {i}")
        sbs = np.hstack([left, right])
        cv2.imwrite(f"datasets/0816_6mm_IMX477_jetson/scenes/sbs{i}.jpg", sbs)
    finally:
        pass