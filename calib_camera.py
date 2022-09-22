"""
This program is for camera calibration.

Steps:
1. preprocess
2. calibrate
3. rectify

Results have proved that, seperate calibration for 
left/right camera is not good, so not used here. 
"""

from model.camera_model import CameraModel
from calib.preprocess import Preprocess
from calib.calibration import Calibrate
from calib.rectification import StereoRectify

import sys
import logging
from pathlib import Path
logFormatter = logging.Formatter("[%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


# camera info
image_size = (4056, 3040)       # Raspi  IMX477
image_size = (4032, 3040)       # Jetson IMX477
is_fisheye = False

# Hyperparams
folder_name = "0920_m12_Cplus"
operation_folder = Path("datasets") / folder_name
rows = 11
columns = 8
CHECKERBOARD = (rows,columns)
square_size = 60

# camera = CameraModel(image_size, is_fisheye)
# preprocess = Preprocess(camera, operation_folder,
#     CHECKERBOARD=CHECKERBOARD, square_size=square_size)
# data_path = operation_folder / "calibration_data"
# preprocess.preprocess_sbs()
# print()

# calibration = Calibrate(camera, operation_folder,
#     CHECKERBOARD=CHECKERBOARD, square_size=square_size)
# calibration.calibrate_left_right()
# calibration.stereo_calibrate(fix_intrinsic = False, show_pve = False)
# print()

camera_path = operation_folder / 'camera_model'
model_path = Path("example") / "camera_model.json"
camera = CameraModel.load_model(model_path)
rectifier = StereoRectify(camera, operation_folder)
rectifier.rectify_camera(roi_ratio=0, new_image_ratio=1)
rectifier.rectify_samples()
print()
