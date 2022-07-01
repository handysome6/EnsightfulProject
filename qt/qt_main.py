import sys
from pathlib import Path
from time import sleep
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import Qt, QSize, QThread
from PySide6.QtWidgets import QPushButton, QComboBox, QLabel, QGridLayout, QHBoxLayout
from PySide6.QtWidgets import QScrollArea, QWidget, QTextEdit
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QListView
from PySide6.QtGui import QPalette, QIcon
from qt.qt_calibrate import CalibWindow
from qt.qt_take_photo import TakePhotoWindow
from qt.qt_view_measure import ViewMeasureWindow
from concurrent.futures import ThreadPoolExecutor
import subprocess


class MyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle('Ensightful Project')

        # components
        self.btn_calibrate_camera = QPushButton("Calibrate Camera...")
        self.model_selection = QComboBox()
        self.label_recent = QLabel("Recent Images:")
        self.btn_take_photo = QPushButton("Take a New Photo...")
        self.btn_proceed_measure = QPushButton("View and Measure...")
        self.image_display = QScrollArea()
        self.copy_right = QLabel("© Ensightful Ltd. All Rights Reserved.")
        self.copy_right.setStyleSheet("color: gray;")
        
        # grid layout 
        self._init_model_menu()
        self.grid_layout = QGridLayout(self)
        self.grid_layout.addWidget(self.btn_calibrate_camera, 0, 0)
        self.grid_layout.addWidget(self.model_selection, 0, 1)
        self.grid_layout.addWidget(self.label_recent, 1, 0)
        self.img_list_region = QListWidget()
        self.grid_layout.addWidget(self.img_list_region, 2, 0, 1, 2)
        self.grid_layout.addWidget(self.btn_take_photo, 3, 0)
        self.grid_layout.addWidget(self.btn_proceed_measure, 3, 1)
        self.grid_layout.addWidget(self.copy_right, 4,0, 1, 2, alignment=Qt.AlignCenter)

        # setup btn 
        self.btn_calibrate_camera.clicked.connect(self._open_calib_window)
        self.btn_take_photo.clicked.connect(self._open_take_photo_window)
        self.btn_proceed_measure.clicked.connect(self._open_view_measure_window)

        # load images icons
        self._init_dispaly_image()

    def _init_model_menu(self):
        # search and addItem
        from PIL import Image
        import numpy as np
        from PIL.ImageQt import ImageQt 
        from PySide6.QtGui import QPixmap
        numpy_image = np.zeros((10, 10, 3))
        PIL_image = Image.fromarray(numpy_image.astype('uint8'), 'RGB')
        icon = QPixmap.fromImage(ImageQt(PIL_image))

        model_path = Path('datasets/calibration_data')
        models = model_path.glob('*.npz')
        for model in models:
            self.model_selection.addItem(icon, model.name)

    def _init_dispaly_image(self):
        self.img_list_region.setViewMode(QListWidget.IconMode)
        self.img_list_region.setResizeMode(QListWidget.Adjust)
        self.img_list_region.setMovement(QListView.Static)
        self.img_list_region.setIconSize(QSize(230,230))

        def load_image(img_path):
            path = str(img_path)
            return QIcon(path), img_path.name

        executor = ThreadPoolExecutor(5)
        test_folder = Path('datasets/0617_IMX477_5000/test')
        imgs = list(test_folder.glob("*.jpg"))
        for img_path in imgs[:5]:
            future = executor.submit(load_image, (img_path))
            future.add_done_callback(self.insert_images)
            
    def insert_images(self, future):
        icon, name = future.result()
        item = QListWidgetItem(icon, name)
        self.img_list_region.addItem(item)

    @QtCore.Slot()
    def _open_calib_window(self):
        self.calib_window = CalibWindow(self)
        self.calib_window.show()

    @QtCore.Slot()
    def _open_take_photo_window(self):
        # self.take_photo_window = TakePhotoWindow(self)
        # self.take_photo_window.show()
        command = "raspistill -3d sbs -t 0 -fp -h 3040 -w 8112 -dt -o datasets/test/sbs_%d.jpg -k"
        p = subprocess.Popen("ls -lh", stdout=subprocess.PIPE, shell=True)
        print(p.communicate())

    @QtCore.Slot()
    def _open_view_measure_window(self):
        self.view_measure_window = ViewMeasureWindow(self)
        self.view_measure_window.show()



if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())