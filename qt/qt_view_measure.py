from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from PyQt5 import QtCore, QtWidgets, QtGui
import cv2
import numpy as np
from pathlib import Path

from measure.matcher import MATCHER_TYPE
from model.camera_model import CameraModel
from calib.rectification import StereoRectify
from utils.utils import snap_subpix_corner, imshow
from measure.ruler import Ruler

class ViewMeasureWindow(QWidget):
    def __init__(self, cam_path, img_path, project_folder, parent = None):
        super().__init__()
        self.setWindowTitle("View and Measure")

        print("--------View and Measure--------")
        print("Viewing image:", img_path)
        print("Measure using:", cam_path)

        # load camera model
        camera = CameraModel.load_model(cam_path)

        # rectify image
        sbs_img = cv2.imread(str(img_path))
        rectifier = StereoRectify(camera, project_folder)
        imgL, imgR = rectifier.rectify_image(sbs_img)

        # measure
        ruler = Ruler(camera, imgL, imgR)
        ruler.click_segment(automatch=False, matcher=MATCHER_TYPE.VGG)
        len = ruler.measure_segment()
        print(len)

        ruler.show_endpoints()

