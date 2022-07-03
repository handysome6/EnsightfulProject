import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from pathlib import Path
from PIL import Image
from PIL.ImageQt import ImageQt 
from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QSize, QThread
from PySide6.QtWidgets import (QWidget, QFileDialog, 
    QPushButton, QComboBox, QLabel, QTextEdit, QLineEdit, 
    QListWidget, QListWidgetItem, QListView, 
    QGridLayout, QVBoxLayout, QHBoxLayout, )

from qt.qt_calibrate import CalibWindow
# from qt.qt_take_photo import TakePhotoWindow
from qt.qt_view_measure import ViewMeasureWindow


class MainWindow(QWidget):
    def __init__(self):
        """Main window starting the project.
        """        
        super().__init__()
        self.setWindowTitle('Ensightful Project')

        # params
        self.project_folder = None
        self.current_model = None
        self.current_image = None
        self.models = None
        self.img_paths = []

        # 1st line
        self.btn_calibrate_camera = QPushButton("Calibrate Camera...")
        self.model_selection = QComboBox()
        self._init_model_menu()
        h1 = QHBoxLayout()
        h1.addWidget(self.btn_calibrate_camera)
        h1.addWidget(self.model_selection)

        # 2nd line
        self.project_folder_label = QLabel("Project folder:")
        self.project_folder_path = QLineEdit()
        self.project_folder_btn = QPushButton("...")
        h2 = QHBoxLayout()
        h2.addWidget(self.project_folder_label)
        h2.addWidget(self.project_folder_path)
        h2.addWidget(self.project_folder_btn)

        # 3rd line
        self.btn_take_photo = QPushButton("Take a New Photo...")
        self.btn_proceed_measure = QPushButton("View and Measure...")
        h3 = QHBoxLayout()
        h3.addWidget(self.btn_take_photo)
        h3.addWidget(self.btn_proceed_measure)

        # other component
        self.label_recent = QLabel("Recent Images:")
        self.img_list_region = QListWidget()
        self._init_dispaly_image()
        self.copy_right = QLabel("© Ensightful Ltd. All Rights Reserved.")
        self.copy_right.setStyleSheet("color: gray;")

        # main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(h1)
        self.main_layout.addLayout(h2)
        self.main_layout.addWidget(self.label_recent)
        self.main_layout.addWidget(self.img_list_region)
        self.main_layout.addLayout(h3)
        self.main_layout.addWidget(self.copy_right, alignment=Qt.AlignHCenter)

        # setup btn 
        self.btn_calibrate_camera.clicked.connect(self._open_calib_window)
        self.btn_take_photo.clicked.connect(self._open_take_photo_window)
        self.btn_proceed_measure.clicked.connect(self._open_view_measure_window)
        self.project_folder_btn.clicked.connect(self._select_project_folder)

    def _init_model_menu(self):
        """Initialize the Camera Model Selection Menu
        """        
        # add camera model under {folder} to model menu
        icon = QIcon("qt/cam_model_icon.png")
        model_path = Path('datasets/calibration_data')
        self.models = list(model_path.glob('*.npz'))
        for model in self.models:
            self.model_selection.addItem(icon, model.name)
        
        # try set current selected model
        try:    self.current_model = self.models[0]
        except: pass
        
        # add listener to respond selection change
        self.model_selection.currentIndexChanged.connect(self._model_select_event)

    def _init_dispaly_image(self):
        """Initialize Image Selection Region
        """        
        # self.img_list_region.clear()
        self.img_list_region.setViewMode(QListWidget.IconMode)
        self.img_list_region.setResizeMode(QListWidget.Adjust)
        self.img_list_region.setMovement(QListView.Static)
        self.img_list_region.setIconSize(QSize(230,230))
        self._thread_load_image()
        # add handler to selected change signal
        self.img_list_region.currentItemChanged.connect(self._image_select_event)

    def _thread_load_image(self):
        """multithread load all images under {folder} to region
        """
        def _load_icon(img_path):
            path = str(img_path)
            with Image.open(path) as im:
                width, height = im.size
                new_width = width // 2
                view = im.transform((532,400), Image.Transform.EXTENT, data=(0,0,new_width, height))
                icon = QPixmap.fromImage(ImageQt(view))
                return icon, img_path

        # multi-thread implement
        executor = ThreadPoolExecutor(2)
        test_folder = Path('datasets/0617_IMX477_5000/test')
        imgs = list(test_folder.glob("*.jpg"))
        for img_path in imgs:
            if img_path not in self.img_paths:
                self.img_paths.append(img_path)
                future = executor.submit(_load_icon, (img_path))
                future.add_done_callback(self._insert_images)
            
    def _insert_images(self, future):
        """hand returned future object

        Args:
            future (Future): Future object contains transformed Icons
        """        
        # fetch result from future object
        icon, path = future.result()
        item = QListWidgetItem(icon, path.name)
        # attach data to the list item
        item.setData(Qt.UserRole, path)
        self.img_list_region.addItem(item)

    @QtCore.Slot()
    def _model_select_event(self, index):
         self.current_model = self.models[index]
         print("Selected camera model:", self.current_model)

    @QtCore.Slot()
    def _image_select_event(self, current, previous):
        self.current_image = current.data(Qt.UserRole)
        print("Selected image:", self.current_image)

    @QtCore.Slot()
    def _select_project_folder(self):
        str_path = QFileDialog.getExistingDirectory(self, "Select project folder...")
        print("Project folder selected:", str_path)
        self.project_folder_path.setText(str_path)
        self.project_folder = Path(str_path)

    @QtCore.Slot()
    def _open_calib_window(self):
        self.calib_window = CalibWindow(self)
        self.calib_window.show()

    @QtCore.Slot()
    def _open_take_photo_window(self):
        # self.take_photo_window = TakePhotoWindow(self)
        # self.take_photo_window.show()
        command = "raspistill -3d sbs -t 0 -fp -h 3040 -w 8112 -dt -o datasets/test/sbs_%d.jpg -k"
        subprocess.call(command, stdout=subprocess.PIPE, shell=True)
        self._thread_load_image()
    
    @QtCore.Slot()
    def _open_view_measure_window(self):
        assert self.current_model.is_file()
        assert self.current_image.is_file()
        self.view_measure_window = ViewMeasureWindow(
            self.current_model, self.current_image, self.project_folder,
            parent=self)
        # self.view_measure_window.show()



if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MainWindow()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())