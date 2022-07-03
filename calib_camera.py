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
CCD = 'IMX477'
fisheye = False

# Hyperparams
operation_folder = Path("datasets") / '0617_IMX477_5000'
rows = 8
columns = 11
CHECKERBOARD = (rows,columns)
square_size = 25

camera = CameraModel(CCD, fisheye)
preprocess = Preprocess(camera, operation_folder)
data_path = operation_folder / "calibration_data"
preprocess.preprocess_sbs()
print()

calibration = Calibrate(camera, operation_folder)
calibration.calibrate_left_right()
calibration.stereo_calibrate(fix_intrinsic = False)
print()

model_path = data_path / "camera_model.npz"
camera = CameraModel.load_model(model_path)
rectifier = StereoRectify(camera, operation_folder)
rectifier.rectify_camera(roi_ratio=0, new_image_ratio=1)
rectifier.rectify_samples()
print()
