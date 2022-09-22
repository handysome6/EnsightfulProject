import sys
import numpy as np
import cv2
import os
from statistics import mean, stdev
from tqdm.auto import tqdm
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QApplication, QPushButton, QSizePolicy, 
    QVBoxLayout, QHBoxLayout, QFileDialog, QLabel,
    QLineEdit, QGridLayout, QTextEdit, QPlainTextEdit 
)
from PyQt5.QtGui import QWindow, QIcon, QPalette, QColor
from PyQt5.QtCore import QSize, Qt, pyqtSignal, QThread, QObject
from PyQt5 import QtWidgets


from measure.ruler import Ruler
from model.camera_model import CameraModel
from calib.rectification import StereoRectify



class Evaluation(QWidget):
    def __init__(self, CHECKERBOARD=(11, 8)):
        super().__init__()
        self.CHECKERBOARD = CHECKERBOARD

        self._load_layout()
        self._load_camera_model()

    def _load_layout(self):
        # widgets
        camera_label = QLabel("Current Label:")
        self.camera_path = QLineEdit()
        camera_button = QPushButton("Select")
        camera_button.clicked.connect(self._slot_select_camera)

        image_label = QLabel("Evaluation Img:")
        self.image_path = QLineEdit()
        image_button = QPushButton("Select")
        image_button.clicked.connect(self._slot_select_image)

        eval_button = QPushButton("Evaluate")
        eval_button.clicked.connect(self._slot_eval_sbs_image)
        self.console = QPlainTextEdit()

        # main layout
        layout = QGridLayout(self)
        layout.addWidget(camera_label, 0, 0)
        layout.addWidget(self.camera_path, 0, 1)
        layout.addWidget(camera_button, 0, 2)

        layout.addWidget(image_label, 1, 0)
        layout.addWidget(self.image_path, 1, 1)
        layout.addWidget(image_button, 1, 2)

        layout.addWidget(eval_button, 2, 1)
        layout.addWidget(self.console, 3, 0, 2, 3)


    def _load_camera_model(self, cam_path=None):
        """Load the camera model. Default from example folder"""
        if cam_path is None:
            self.console.appendPlainText("Loading default camera model...")
            cam_path = Path(".") / "example" / "camera_model.json"
        else:
            self.console.appendPlainText("Loading selected camera model...")
        camera_model = CameraModel.load_model(cam_path)
        self.rectifier = StereoRectify(camera_model, None)
        self.camera_path.setText(str(cam_path))


    def _slot_select_camera(self):
        str_path, _ = QFileDialog.getOpenFileName(
            self, "Select another camera model...", "./datasets", "*.json *.npz"
        )
        if str_path != '':
            cam_path = Path(str_path).relative_to(Path('.').resolve())
            self._load_camera_model(cam_path=cam_path)


    def _slot_select_image(self):
        str_path, _ = QFileDialog.getOpenFileName(
            self, "Select a sbs image...", "./datasets", "Images (*.png *.jpg)"
        )
        if str_path != '':
            img_path = Path(str_path).relative_to(Path('.').resolve())
            self.image_path.setText(str(img_path))
            self.console.appendPlainText(f"Selected evaluation image {str(img_path)}")


    def _slot_eval_sbs_image(self):
        assert self.rectifier is not None
        sbs_img = cv2.imread(str(self.image_path.text()))
        assert sbs_img is not None

        cornersL, cornersR = self.find_chessboard_sbs(sbs_img)
        self.eval_box_edge_len(cornersL, cornersR)
        self.eval_long_edge_len(cornersL, cornersR)


    def find_chessboard_sbs(self, sbs_img):
        left_rect, right_rect = self.rectifier.rectify_image(sbs_img=sbs_img)

        grayL = cv2.cvtColor(left_rect,cv2.COLOR_BGR2GRAY)
        grayR = cv2.cvtColor(right_rect,cv2.COLOR_BGR2GRAY)
        retL, cornersL = cv2.findChessboardCorners(grayL, self.CHECKERBOARD, None)
        retR, cornersR = cv2.findChessboardCorners(grayR, self.CHECKERBOARD, None)

        subpix_criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        if ((retL == True) and (retR == True)):
            cv2.cornerSubPix(grayL,cornersL,(11,11),(-1,-1),subpix_criteria)
            cv2.cornerSubPix(grayR,cornersR,(11,11),(-1,-1),subpix_criteria)
            return cornersL, cornersR


    def eval_box_edge_len(self, cornersL, cornersR):
        # box edge lengths
        edges = []
        for i in range(self.CHECKERBOARD[0] * self.CHECKERBOARD[1] - 1):
            # select two points
            point_id_1 = i
            point_id_2 = i+1

            img_coord_1 = [cornersL[point_id_1][0], cornersR[point_id_1][0]]
            img_coord_2 = [cornersL[point_id_2][0], cornersR[point_id_2][0]]

            coord1 = Ruler.get_world_coord_Q(self.rectifier.Q, img_coord_1[0], img_coord_1[1])
            coord2 = Ruler.get_world_coord_Q(self.rectifier.Q, img_coord_2[0], img_coord_2[1])

            distance = cv2.norm(coord1, coord2)
            if distance < 100:
                edges.append(distance)
            else:
                # print(point_id_1, point_id_2)
                pass
        msg = f'''Box Length Performance:
Max: {max(edges)}; Min: {min(edges)}
Mean: {mean(edges)}; Stdev: {stdev(edges)} '''
        self.console.appendPlainText(msg)


    def eval_long_edge_len(self, cornersL, cornersR):
        # long edge lengths
        edges = []
        for i in range(0, 87, 11):
            # select two points
            point_id_1 = i
            point_id_2 = i+10

            img_coord_1 = [cornersL[point_id_1][0], cornersR[point_id_1][0]]
            img_coord_2 = [cornersL[point_id_2][0], cornersR[point_id_2][0]]

            coord1 = Ruler.get_world_coord_Q(self.rectifier.Q, img_coord_1[0], img_coord_1[1])
            coord2 = Ruler.get_world_coord_Q(self.rectifier.Q, img_coord_2[0], img_coord_2[1])
            distance = cv2.norm(coord1, coord2)
            edges.append(distance)
            print(distance)
        msg = f'''
Long Edge Length Performance:
Max: {max(edges)}; Min: {min(edges)}
Mean: {mean(edges)}; Stdev: {stdev(edges)}
'''
        self.console.appendPlainText(msg)

        



if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = Evaluation()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
