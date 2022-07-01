from hashlib import algorithms_available
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QGroupBox, QGridLayout, QVBoxLayout
from PySide6.QtWidgets import QLabel, QPushButton, QLineEdit, QCheckBox
from PySide6 import QtCore, QtWidgets, QtGui

class CalibWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Calibrate camera")
        self._calib_single_camera_group_box()
        self._calib_dual_camera_group_box()
        self._start_calib_config_group_box()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.single_group_box)
        self.main_layout.addWidget(self.dual_group_box)
        self.main_layout.addWidget(self.config_group_box)


    def _calib_single_camera_group_box(self):
        self.single_group_box = QGroupBox("Single Camera Calibration")
        # indenp checker box
        independent_single_label = QLabel("Calibrate single cameras independently:")
        independent_single_checker = QCheckBox()
        # left 
        single_left_label = QLabel("Calib left camera path:")
        single_left_path = QLineEdit("Please select folder...")
        single_left_btn = QPushButton("...")
        # right 
        single_right_label = QLabel("Calib right camera path:")
        single_right_path = QLineEdit("Please select folder...")
        single_right_btn = QPushButton("...")

        layout = QGridLayout()
        layout.addWidget(independent_single_label,   0,0,1,2)
        layout.addWidget(independent_single_checker, 0,2, alignment=Qt.AlignCenter)
        layout.addWidget(single_left_label,  1,0)
        layout.addWidget(single_left_path,   1,1)
        layout.addWidget(single_left_btn,    1,2)
        layout.addWidget(single_right_label, 2,0)
        layout.addWidget(single_right_path,  2,1)
        layout.addWidget(single_right_btn,   2,2)

        self.single_group_box.setLayout(layout)

    def _calib_dual_camera_group_box(self):
        self.dual_group_box = QGroupBox("Dual Camera Calibration")
        # dual
        dual_label = QLabel("Calib dual camera path:")
        dual_path = QLineEdit("Please select folder...")
        dual_btn = QPushButton("...")
        # checker: Fix intrinsic
        fix_intrinsic_label = QLabel("Fix intrinsic params when dual calibration:")
        fix_intrinsic_checker = QCheckBox()

        layout = QGridLayout()
        layout.addWidget(dual_label,  0,0)
        layout.addWidget(dual_path,   0,1)
        layout.addWidget(dual_btn,    0,2)
        layout.addWidget(fix_intrinsic_label, 1,0,1,2)
        layout.addWidget(fix_intrinsic_checker, 1,2, alignment=Qt.AlignCenter)

        self.dual_group_box.setLayout(layout)

    def _start_calib_config_group_box(self):
        self.config_group_box = QGroupBox("Calibration Configuration")
        # camera model save as file
        model_save_label = QLabel("Camera model save as: ")
        model_save_path = QLineEdit("Please input target...")
        model_save_btn = QPushButton("...")
        # fisheye 
        fisheye_label = QLabel("FishEye Mode: ")
        fisheye_checker = QCheckBox()
        # start button
        start_calib_btn = QPushButton("Start Calibration")

        layout = QGridLayout()
        layout.addWidget(model_save_label, 0,0)
        layout.addWidget(model_save_path, 0,1)
        layout.addWidget(model_save_btn, 0,2)
        layout.addWidget(fisheye_label, 1,0)
        layout.addWidget(fisheye_checker, 1,2, alignment=Qt.AlignCenter)
        layout.addWidget(start_calib_btn, 2,0,1,3)

        self.config_group_box.setLayout(layout)
        