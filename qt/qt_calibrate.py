import sys
import logging
from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QGroupBox, QGridLayout, QVBoxLayout
from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QCheckBox, QFileDialog
from PyQt5 import QtCore, QtWidgets, QtGui
from model.camera_model import CameraModel
from calib.preprocess import Preprocess
from calib.calibration import Calibrate
from calib.rectification import StereoRectify



class CalibWindow(QWidget):
    def __init__(self, project_folder, parent=None):
        super().__init__()
        self.setWindowTitle("Calibrate camera")

        self.project_folder = project_folder
        self.dual_folder = None

        self._calib_single_camera_group_box()
        self._calib_dual_camera_group_box()
        self._start_calib_config_group_box()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.single_group_box)
        self.main_layout.addWidget(self.dual_group_box)
        self.main_layout.addWidget(self.config_group_box)


    def _calib_single_camera_group_box(self):
        # checker: single intrinsic calib
        single_intrinsic_calib_label = QLabel("Calibrate single intrinsic independently:")
        self.single_intrinsic_calib_checker = QCheckBox()
        # left 
        self.single_left_label = QLabel("Calib left camera path:")
        self.single_left_path = QLineEdit()
        self.single_left_btn = QPushButton("...")
        # right 
        self.single_right_label = QLabel("Calib right camera path:")
        self.single_right_path = QLineEdit()
        self.single_right_btn = QPushButton("...")

        # init widgets
        self._slot_single_intrinsic_calib_toggled(0)
        self.single_intrinsic_calib_checker.stateChanged.connect(self._slot_single_intrinsic_calib_toggled)
        # self.single_left_path.setPlaceholderText("Please select folder...")
        # self.single_right_path.setPlaceholderText("Please select folder...")

        layout = QGridLayout()
        layout.addWidget(single_intrinsic_calib_label,   0,0,1,2)
        layout.addWidget(self.single_intrinsic_calib_checker, 0,2, alignment=Qt.AlignCenter)
        layout.addWidget(self.single_left_label,  1,0)
        layout.addWidget(self.single_left_path,   1,1)
        layout.addWidget(self.single_left_btn,    1,2)
        layout.addWidget(self.single_right_label, 2,0)
        layout.addWidget(self.single_right_path,  2,1)
        layout.addWidget(self.single_right_btn,   2,2)

        self.single_group_box = QGroupBox("Single Camera Calibration")
        self.single_group_box.setLayout(layout)
        # self.single_group_box.setEnabled(False)

    def _calib_dual_camera_group_box(self):
        self.dual_group_box = QGroupBox("Dual Camera Calibration")
        # dual
        dual_label = QLabel("Calib dual camera path:")
        self.dual_path = QLineEdit()
        dual_btn = QPushButton("...")
        fix_intrinsic_label = QLabel("Fix intrinsic params when dual calibration:")
        fix_intrinsic_checker = QCheckBox()
        # init
        dual_btn.clicked.connect(self._slot_select_dual_folder)

        layout = QGridLayout()
        layout.addWidget(dual_label,  0,0)
        layout.addWidget(self.dual_path,   0,1)
        layout.addWidget(dual_btn,    0,2)
        layout.addWidget(fix_intrinsic_label, 1,0,1,2)
        layout.addWidget(fix_intrinsic_checker, 1,2, alignment=Qt.AlignCenter)

        self.dual_group_box.setLayout(layout)

    def _start_calib_config_group_box(self):
        self.config_group_box = QGroupBox("Calibration Configuration")
        # camera model save as file
        model_save_label = QLabel("Camera model save as: ")
        model_save_path = QLineEdit()
        model_save_btn = QPushButton("...")
        # fisheye 
        fisheye_label = QLabel("FishEye Mode: ")
        fisheye_checker = QCheckBox()
        # start button
        start_calib_btn = QPushButton("Start Calibration")

        # init
        start_calib_btn.clicked.connect(self._slot_start_calibration)

        layout = QGridLayout()
        layout.addWidget(model_save_label, 0,0)
        layout.addWidget(model_save_path, 0,1)
        layout.addWidget(model_save_btn, 0,2)
        layout.addWidget(fisheye_label, 1,0)
        layout.addWidget(fisheye_checker, 1,2, alignment=Qt.AlignCenter)
        layout.addWidget(start_calib_btn, 2,0,1,3)

        self.config_group_box.setLayout(layout)
        


    def _slot_single_intrinsic_calib_toggled(self, state):
        if self.single_intrinsic_calib_checker.isChecked():
            self.single_left_label.setEnabled(True)
            self.single_left_path.setEnabled(True)
            self.single_left_btn.setEnabled(True)
            self.single_right_label.setEnabled(True)
            self.single_right_path.setEnabled(True)
            self.single_right_btn.setEnabled(True)
        else:
            self.single_left_label.setEnabled(False)
            self.single_left_path.setEnabled(False)
            self.single_left_btn.setEnabled(False)
            self.single_right_label.setEnabled(False)
            self.single_right_path.setEnabled(False)
            self.single_right_btn.setEnabled(False)

    def _slot_select_dual_folder(self):
        str_path = QFileDialog.getExistingDirectory(self, "Select project folder...", str(self.project_folder))
        if str_path != '':
            self.dual_folder = Path(str_path).relative_to(Path('.').resolve())
            print("Selected dual folder: " + str(self.dual_folder))
            self.dual_path.setText(str(self.dual_folder))

    def _slot_start_calibration(self):
        # camera info
        CCD = 'IMX477'
        fisheye = False
        camera = CameraModel(CCD, fisheye)
        preprocess = Preprocess(camera, self.project_folder)
        data_path = self.project_folder / "calibration_data"
        preprocess.preprocess_sbs()
        print()

        calibration = Calibrate(camera, self.project_folder)
        calibration.calibrate_left_right()
        calibration.stereo_calibrate(fix_intrinsic = False)
        print()

        # camera_path = self.project_folder / 'camera_model'
        # model_path = camera_path / "camera_model.npz"
        # camera = CameraModel.load_model(model_path)
        rectifier = StereoRectify(camera, self.project_folder)
        rectifier.rectify_camera(roi_ratio=0, new_image_ratio=1)
        rectifier.rectify_samples()
        print()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = CalibWindow()
    # widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())