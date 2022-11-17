import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from pathlib import Path
from PIL import Image
from PIL.ImageQt import ImageQt 
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSlot
from PyQt5.QtWidgets import (QWidget, QFileDialog, 
    QPushButton, QComboBox, QLabel, QTextEdit, QLineEdit, 
    QListWidget, QListWidgetItem, QListView, 
    QGridLayout, QVBoxLayout, QHBoxLayout, )
from numpy import empty

from qt.qt_calibrate import CalibWindow
from qt.qt_view_measure import ViewMeasureWindow
from qt.main_ui import Ui_Form
from calib.preprocess import Preprocess
from calib.calibration import Calibrate
from model.camera_model import CameraModel


class MainWindow(QWidget):
    def __init__(self):
        """Main window starting the project.
        """        
        super().__init__()
        # self.setWindowTitle('Ensightful Project')

        # params
        self.datasets_folder = Path("datasets")
        self.current_model = None
        self.current_image = None

        self.ui = Ui_Form()
        self.ui.setupUi(self)

    @pyqtSlot()
    def on_selectFolder_clicked(self):
        print("open folder!")
        str_path = QFileDialog.getExistingDirectory(self, "Select project folder...", "datasets")
        if str_path != '':
            self.project_folder = Path(str_path).relative_to(Path('.').resolve())
            print("Selected project folder: " + str(self.project_folder))
            self.ui.folderLineEdit.setText(str(self.project_folder))

    @pyqtSlot()
    def on_startCalibrate_clicked(self):
        print("startCalibrate!")
        if self.project_folder is None:
            print("project folder not selected")
            return 

        # start calibration
        # camera info
        image_size = (4056, 3040)       # Raspi  IMX477
        image_size = (4032, 3040)       # Jetson IMX477
        is_fisheye = False
        # Hyperparams
        operation_folder = self.project_folder
        rows = 11
        columns = 8
        CHECKERBOARD = (rows,columns)
        square_size = 60

        camera = CameraModel(image_size, is_fisheye)
        preprocess = Preprocess(camera, operation_folder,
            CHECKERBOARD=CHECKERBOARD, square_size=square_size)
        preprocess.preprocess_sbs()
        print()

        calibration = Calibrate(camera, operation_folder,
            CHECKERBOARD=CHECKERBOARD, square_size=square_size)
        calibration.calibrate_left_right()
        calibration.stereo_calibrate(fix_intrinsic = False, show_pve = False)
        print()

        self.ui.modelLineEdit.setText(str(self.project_folder / "camera_model" / "camera_model.json"))
        


    @pyqtSlot()
    def on_selectModel_clicked(self):
        print("selcect model!")
        str_path, _ = QFileDialog.getOpenFileName(self, "Select camera model...", "datasets", "JSON *.json")
        if str_path != '':
            self.camera_path = Path(str_path).relative_to(Path('.').resolve())
            print("Selected camera model: " + str(self.camera_path))
            self.ui.modelLineEdit.setText(str(self.camera_path))

    @pyqtSlot()
    def on_selectImage_clicked(self):
        print("select image!")
        str_path, _ = QFileDialog.getOpenFileName(self, "Select image...", "datasets", "*.png *.jpg")
        if str_path != '':
            self.image_path = Path(str_path).relative_to(Path('.').resolve())
            print("Selected image: " + str(self.image_path))
            self.ui.imageLineEdit.setText(str(self.image_path))


    def _open_view_measure_window(self):
        assert self.current_model.is_file()
        assert self.current_image.is_file()
        # further implement  - TODO

        # self.view_measure_window = ViewMeasureWindow(
        #     self.current_model, self.current_image, self.project_folder,
        #     parent=self)
        # self.view_measure_window.show()



