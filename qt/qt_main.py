import sys
from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QComboBox, QLabel, QGridLayout, QHBoxLayout
from PySide6.QtWidgets import QScrollArea, QWidget, QTextEdit
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QListView
from PySide6.QtGui import QPalette, QIcon
from qt.qt_calibrate import CalibWindow
from qt.qt_take_photo import TakePhotoWindow
from qt.qt_view_measure import ViewMeasureWindow

class MyWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle('Ensightful Project')

        self.btn_calibrate_camera = QPushButton("Calibrate Camera...")
        self.model_selection = QComboBox()
        self.label_recent = QLabel("Recent Images:")
        self.btn_take_photo = QPushButton("Take a New Photo...")
        self.btn_proceed_measure = QPushButton("View and Measure...")
        self.image_display = QScrollArea()
        self.copy_right = QLabel("© Ensightful Ltd. All Rights Reserved.")
        self.copy_right.setStyleSheet("color: gray;")
        

        self._init_model_menu()
        self.grid_layout = QGridLayout(self)
        self.grid_layout.addWidget(self.btn_calibrate_camera, 0, 0)
        self.grid_layout.addWidget(self.model_selection, 0, 1)
        self.grid_layout.addWidget(self.label_recent, 1, 0)
        self._init_dispaly_image()
        self.grid_layout.addWidget(self.btn_take_photo, 3, 0)
        self.grid_layout.addWidget(self.btn_proceed_measure, 3, 1)
        self.grid_layout.addWidget(self.copy_right, 4,0, 1, 2, alignment=Qt.AlignCenter)

        self.btn_calibrate_camera.clicked.connect(self._open_calib_window)
        self.btn_take_photo.clicked.connect(self._open_take_photo_window)
        self.btn_proceed_measure.clicked.connect(self._open_view_measure_window)

    def _init_model_menu(self):
        # search and addItem
        from PIL import Image
        import numpy as np
        from PIL.ImageQt import ImageQt 
        from PySide6.QtGui import QPixmap
        numpy_image = np.zeros((10, 10, 3))
        PIL_image = Image.fromarray(numpy_image.astype('uint8'), 'RGB')
        icon = QPixmap.fromImage(ImageQt(PIL_image))

        self.model_selection.addItem(icon, "example model.npz")
        self.model_selection.addItem(icon, "example model2.npz")

    def _init_dispaly_image(self):
        # init dispaly region
        list_widget = QListWidget()
        list_widget.setViewMode(QListWidget.IconMode)
        list_widget.setResizeMode(QListWidget.Adjust)
        list_widget.setMovement(QListView.Static)

        # init display images
        test_folder = Path('icons')
        imgs = test_folder.glob("*.jpg")
        for img in imgs:
            path = str(img)
            item = QListWidgetItem(QIcon(path), path)
            list_widget.addItem(item)

        self.grid_layout.addWidget(list_widget, 2, 0, 1, 2)

    @QtCore.Slot()
    def _open_calib_window(self):
        self.calib_window = CalibWindow(self)
        self.calib_window.show()

    @QtCore.Slot()
    def _open_take_photo_window(self):
        self.take_photo_window = TakePhotoWindow(self)
        self.take_photo_window.show()

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