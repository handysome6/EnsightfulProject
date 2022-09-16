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
            self.project_folder_container.setText(str(self.project_folder))
            self._load_camera_model_combo()
            self._load_recent_photo_list()

    
    @pyqtSlot()
    def on_selectModel_clicked(self):
        print("selcect model!")

    @pyqtSlot()
    def on_selectImage_clicked(self):
        print("select image!")


    def _open_view_measure_window(self):
        assert self.current_model.is_file()
        assert self.current_image.is_file()
        # self.view_measure_window = ViewMeasureWindow(
        #     self.current_model, self.current_image, self.project_folder,
        #     parent=self)
        # self.view_measure_window.show()



