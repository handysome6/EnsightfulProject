import sys
import subprocess
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from pathlib import Path
from PIL import Image
from PIL.ImageQt import ImageQt 
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (QWidget, QFileDialog, QGroupBox,
    QPushButton, QComboBox, QLabel, QTextEdit, QLineEdit, 
    QListWidget, QListWidgetItem, QListView, 
    QGridLayout, QVBoxLayout, QHBoxLayout, )

from qt.qt_calibrate import CalibWindow
from qt.qt_take_photo import TakePhotoWindow
from qt.qt_view_measure import ViewMeasureWindow

ICON_SIZE = QSize(266,200)
accepted_types = (".jpg",".tiff",".png",".exr",".psd")

class LoadPhotoThread(QThread):
    thum_loaded = pyqtSignal(QImage, Path)

    def __init__(self, parent, dir) -> None:
        """worker thread for loading photo thumbnails

        Args:
            dir (pathlib.Path): target directory of photos
        """
        super().__init__(parent)
        self.dir = dir
    
    def run(self):
        imgs = list(self.dir.glob("*.jpg"))
        for img_path in imgs:
            path = str(img_path)
            if path.endswith(accepted_types):
                with Image.open(path) as im:
                    width, height = im.size
                    new_width = width // 2
                    im = im.crop((0,0,new_width, height))
                    view = im.resize((266,200))
                    #view = im.transform((266,200), Image.Transform.EXTENT, data=(0,0,new_width, height))
                    view = view.convert("RGBA")
                    data = view.tobytes("raw","RGBA")
                    qim = QtGui.QImage(data, view.size[0], view.size[1], QtGui.QImage.Format_RGBA8888)
                    
                    self.thum_loaded.emit(qim, img_path)


class ProjectWindow(QWidget):
    def __init__(self):
        """Main window starting the project.
        """        
        super().__init__()
        self.setWindowTitle('Ensightful Project')
        self.setFocus()

        # init major params
        self.datasets_folder = Path("datasets")
        # current selected project folder is stored here
        self.project_folder = None
        # use the QLineEdit text as target photo path
        self.selected_photo_path = QLineEdit()
        # current selected model is stored here
        self.current_model = None
        # use two lists to store camera models: autoloaded and selected 
        self.models = dict()
        self.models['extra'] = []
        self.models['project'] = []

        # init regions and groupboxes
        self._init_region_other()
        self._init_region_camera_calib()
        self._init_region_view_measure()

        # add regions to main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(self.project_folder_layout)
        self.main_layout.addWidget(self.groupbox_camera_calib)
        self.main_layout.addWidget(self.groupbox_view_measure)
        self.main_layout.addLayout(self.copyright_layout)
    
    def _init_region_other(self):
        """Defined other widgets on main window.\n
        Including: project folder line, copyright line
        """        
        # create project folder line
        project_folder_label = QLabel("Project folder:")
        self.project_folder_container = QLineEdit()
        project_folder_btn = QPushButton("Select")
        # init widgets
        if self.datasets_folder.is_dir():
            try:
                self.project_folder = list(self.datasets_folder.iterdir())[-1]
                self.project_folder_container.setText(str(self.project_folder))
                print("Loaded recent project: " + str(self.project_folder))
            except:
                print("No project folder found under ./datasets/")
        else:
            print("No datasets folder found. Please put project folder under ./datasets/")
        self.project_folder_container.editingFinished.connect(self._slot_enter_project_folder)
        project_folder_btn.clicked.connect(self._slot_select_project_folder)
        
        self.project_folder_layout = QHBoxLayout()
        self.project_folder_layout.addWidget(project_folder_label)
        self.project_folder_layout.addWidget(self.project_folder_container)
        self.project_folder_layout.addWidget(project_folder_btn)

        # copyright line
        copyright = QLabel("© Ensightful Ltd. All Rights Reserved.")
        copyright.setStyleSheet("color: gray;")

        self.copyright_layout = QHBoxLayout()
        self.copyright_layout.addWidget(copyright, alignment=Qt.AlignHCenter)

    def _init_region_camera_calib(self):
        """Initialize camera calibration region.
        """        
        btn_take_photo_left = QPushButton("Take Photos for Left")
        btn_take_photo_right = QPushButton("Take Photos for Right")
        btn_take_photo_sbs = QPushButton("Take Side-By-Side Photos")
        btn_calib_camera = QPushButton("Calibrate Camera...")
        # init widgets
        btn_take_photo_left.setEnabled(False)
        btn_take_photo_right.setEnabled(False)
        btn_take_photo_sbs.setEnabled(False)
        btn_calib_camera.clicked.connect(self._slot_open_calib_window)

        layout = QGridLayout()
        layout.addWidget(btn_take_photo_left, 0,0)
        layout.addWidget(btn_take_photo_right, 0,1)
        layout.addWidget(btn_take_photo_sbs, 1,0)
        layout.addWidget(btn_calib_camera, 1,1)

        self.groupbox_camera_calib = QGroupBox("Camera Calibration")
        self.groupbox_camera_calib.setLayout(layout)

    def _init_region_view_measure(self):
        """Initialize view and measure region
        """        
        camera_model_label = QLabel("Target Camera:")
        self.camera_model_combo = QComboBox()
        camera_model_btn = QPushButton("Add Camera")
        select_photo_label = QLabel("Target Photo:")
        self.selected_photo_path = QLineEdit()
        select_photo_btn = QPushButton("Select Photo")
        recent_photo_label = QLabel("Recent Photos:")
        new_photo_btn = QPushButton("Take a New Photo")
        view_measure_btn = QPushButton("View And \nMeasure")
        self.recent_photo_region = QListWidget()

        view_measure_btn.setMaximumHeight(200)
        view_measure_btn.clicked.connect(self._slot_open_view_measure_window)
        # init widgets - camera selection
        self._load_camera_model_combo()
        self.camera_model_combo.activated.connect(self._slot_select_camera_combo)
        camera_model_btn.clicked.connect(self._slot_add_camera_model)
        
        # init widgets - photo selection
        select_photo_btn.clicked.connect(self._slot_clcik_select_photo)
        # new_photo_btn.setEnabled(False)
        new_photo_btn.clicked.connect(self._slot_open_take_photo_window)
        self.recent_photo_region.itemClicked.connect(self._slot_select_photo_list)
        self.recent_photo_region.setViewMode(QListWidget.IconMode)
        self.recent_photo_region.setResizeMode(QListWidget.Adjust)
        self.recent_photo_region.setMovement(QListView.Static)
        self.recent_photo_region.setIconSize(QSize(180, 180))
        self._load_recent_photo_list()


        layout = QGridLayout()
        layout.addWidget(camera_model_label, 0, 0)
        layout.addWidget(self.camera_model_combo,  0, 1)
        layout.addWidget(camera_model_btn,   0, 2)
        layout.addWidget(select_photo_label, 1, 0)
        layout.addWidget(self.selected_photo_path,  1, 1)
        layout.addWidget(select_photo_btn,   1, 2)
        layout.addWidget(recent_photo_label, 2, 0)
        layout.addWidget(new_photo_btn,      2, 2)
        layout.addWidget(view_measure_btn,   0, 3, 3, 1)
        layout.addWidget(self.recent_photo_region,
                                             3, 0, 1, 4)

        self.groupbox_view_measure = QGroupBox("View And Measure")
        self.groupbox_view_measure.setLayout(layout)


    def _load_camera_model_combo(self):
        """Initialize the Camera Model Selection Menu
        """        
        # add camera model under {folder} to model menu
        self.camera_model_combo.clear()
        icon = QIcon("qt/cam_model_icon.png")
        try:
            model_folder = self.project_folder / 'camera_model'
            self.models['project'] = list(model_folder.glob('*.npz'))
        except:
            print("Camera model folder doesn't exist ./datasets/PROJECT_FOLDER/camera_model/")
        all_models = self.models['project'] + self.models['extra']
        for model in all_models:
            self.camera_model_combo.addItem(icon, str(model))
        # try set current selected model
        try:    
            self.camera_model_combo.setCurrentIndex(len(all_models)-1)
            self.current_model = all_models[-1]
            print("Loaded recent cam model: " + str(self.current_model))
        except: 
            print("No camera model found under ./datasets/PROJECT_FOLDER/camera_model/")
        
    def _load_recent_photo_list(self):
        """multithread load all images under {folder} to list
        """
        self.recent_photo_region.clear()
        try:
            test_folder = self.project_folder / 'test'
            load_photo_thread = LoadPhotoThread(self, test_folder)
            load_photo_thread.thum_loaded.connect(self._slot_load_single_photo_thum)
            load_photo_thread.start()
        except: pass


    @pyqtSlot(QImage, Path)
    def _slot_load_single_photo_thum(self, qim, img_path):
        icon = QIcon(QPixmap(qim))
        # generate list item
        item = QListWidgetItem(icon, img_path.name, self.recent_photo_region)
        # attach data to the list item
        item.setData(Qt.UserRole, img_path)
        self.recent_photo_region.addItem(item)

    @pyqtSlot()
    def _slot_enter_project_folder(self):
        self.project_folder = Path(self.project_folder_container.text())
        assert self.project_folder.is_dir(), "Project folder path incorrect"
        print("Selected project folder: " + str(self.project_folder))
        self._load_camera_model_combo()
        self._load_recent_photo_list()

    def _slot_select_project_folder(self):
        str_path = QFileDialog.getExistingDirectory(self, "Select project folder...", "datasets")
        if str_path != '':
            self.project_folder = Path(str_path).relative_to(Path('.').resolve())
            print("Selected project folder: " + str(self.project_folder))
            self.project_folder_container.setText(str(self.project_folder))
            self._load_camera_model_combo()
            self._load_recent_photo_list()

    def _slot_open_calib_window(self):
        self.calib_window = CalibWindow(self.project_folder, parent=self)
        self.calib_window.show()

    def _slot_select_camera_combo(self, index):
        all_models = self.models['project'] + self.models['extra']
        self.current_model = all_models[index]
        print("Selected camera model: " + str(self.current_model))

    def _slot_add_camera_model(self):
        str_path, _ = QFileDialog.getOpenFileName(self, "Select another camera model...", str(self.datasets_folder), "*.npz")
        if str_path != '':
            relative_path = Path(str_path).relative_to(Path('.').resolve())
            print("Added camera model: " + str(relative_path))
            self.models['extra'].append(relative_path)
            self._load_camera_model_combo()

    def _slot_clcik_select_photo(self):
        str_path, _ = QFileDialog.getOpenFileName(self, "Select a photo...", str(self.datasets_folder), "Images (*.png *.jpg)")
        if str_path != '':
            relative_path = Path(str_path).relative_to(Path('.').resolve())
            print("Selected photo: " + str(relative_path))
            self.selected_photo_path.setText(str(relative_path))

    def _slot_select_photo_list(self, current):
        current_image = current.data(Qt.UserRole)
        self.selected_photo_path.setText(str(current_image))
        print("Selected image: " + str(current_image))

    # def _slot_open_calib_window(self):
    #     self.calib_window = CalibWindow(parent=self)
    #     self.calib_window.show()

    def _slot_open_view_measure_window(self):
        assert self.current_model.is_file()
        current_image = Path(self.selected_photo_path.text())
        assert current_image.is_file()

        self.view_measure_window = ViewMeasureWindow(
            self.current_model, current_image, self.project_folder,
            parent=self)
        # self.view_measure_window.show()

    def _slot_open_take_photo_window(self):
        self.take_photo_window = TakePhotoWindow(self)
        self.take_photo_window.show()




if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = ProjectWindow()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())
