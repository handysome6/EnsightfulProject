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


# camera info
CCD = 'IMX477'
fisheye = False

# Hyperparams
operation_folder = '0610_IMX477_infinity_still'
rows = 8
columns = 11
CHECKERBOARD = (rows,columns)
square_size = 25

camera = CameraModel(CCD, fisheye)
preprocess = Preprocess(camera, operation_folder)
preprocess.discard()
preprocess.rename()
preprocess.find_chessboard_corners()
print()

calibration = Calibrate(camera, operation_folder, show_result=False)
calibration.single_calibrate()
calibration.stereo_calibrate()
print()

rectifier = StereoRectify(camera, operation_folder)
rectifier.rectify_camera()
rectifier.rectify_samples()
print()
