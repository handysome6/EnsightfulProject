import os
import cv2
import numpy as np
from tqdm import tqdm
from pathlib import Path

# from showimg import imshow
from model.camera_model import CameraModel
from calib.preprocess import Preprocess
from calib.calibration import Calibrate
from calib.rectification import StereoRectify

import logging
import sys
logFormatter = logging.Formatter("[%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)
# fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
# fileHandler.setFormatter(logFormatter)
# rootLogger.addHandler(fileHandler)
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


# camera info
CCD = 'IMX477'
fisheye = False

# Hyperparams
operation_folder = '0610_IMX477_infinity_still'
operation_folder = '0617_IMX477_5000'
rows = 8
columns = 11
CHECKERBOARD = (rows,columns)
square_size = 25

camera = CameraModel(CCD, fisheye)
preprocess = Preprocess(camera, operation_folder)
operation_path = Path('datasets') / operation_folder
data_path = operation_path / "calibration_data"
# preprocess.preprocess_single(operation_path / "left", data_path / 'left.npz')
# preprocess.preprocess_single(operation_path / "right", data_path / 'right.npz')
# preprocess.preprocess_sbs()
print()

# calibration = Calibrate(camera, operation_folder)
# calibration.calibrate_left_right()
# calibration.stereo_calibrate(fix_intrinsic = False)
# print()

model_path = data_path / "camera_model.npz"
camera = CameraModel.load_model(model_path)
rectifier = StereoRectify(camera, operation_folder)
rectifier.rectify_camera(roi_ratio=0, new_image_ratio=1)
rectifier.rectify_samples()
# print()
