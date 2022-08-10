import sys
import cv2
import numpy as np
from pathlib import Path
from time import strftime, localtime

from PyQt5.QtWidgets import (
    QWidget, QApplication, QPushButton, QSizePolicy, 
    QVBoxLayout, QHBoxLayout, QFileDialog
)
from PyQt5.QtGui import QWindow, QIcon
from PyQt5.QtCore import QSize, Qt

from gstreamer.gst_camera import CameraWithPreview, CameraNoPreview
from measure.matcher import MATCHER_TYPE
from measure.ruler import Ruler
from model.camera_model import CameraModel
from calib.rectification import StereoRectify

class TakePhotoWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.showMaximized()
        
        self._load_default_rectifier()
        self.captured_left = None
        self.captured_right = None

        # init camera
        self.camera_0 = CameraWithPreview(sensor_id=0)
        self.camera_1 = CameraNoPreview(sensor_id=1)

        # preview widget
        # fetch embedded window handle, embed x11 window to qt widget
        preview_window_xid = self.camera_0.get_window_xid()
        embbed_preview_window = QWindow.fromWinId(preview_window_xid)
        embbed_preview_widget = QWidget.createWindowContainer(embbed_preview_window)
        # embbed_preview_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._init_toolbar()

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(embbed_preview_widget)
        main_layout.addLayout(self.tool_layout)
    
    def _load_default_rectifier(self):
        """Load the default camera model from sample folder"""
        cam_path = Path("example") / "camera_model.npz"
        camera_model = CameraModel.load_model(cam_path)
        self.rectifier = StereoRectify(camera_model, None)

    def _init_toolbar(self):
        # camera button
        camera_button = QPushButton()
        icon = QIcon("qt/camera_icon.png")
        camera_button.setIcon(icon)
        camera_button.setIconSize(QSize(85, 85))
        camera_button.setFlat(True)
        sp = QSizePolicy()
        sp.setHorizontalStretch(True)
        camera_button.setSizePolicy(sp)
        camera_button.clicked.connect(self._slot_capture)

        # folder open images
        folder_button = QPushButton()
        icon = QIcon("qt/open_folder_icon.png")
        folder_button.setIcon(icon)
        folder_button.setIconSize(QSize(85, 85))
        folder_button.setFlat(True)
        folder_button.setSizePolicy(sp)
        folder_button.clicked.connect(self._slot_folder_select)

        # measure images
        measure_button = QPushButton()
        icon = QIcon("qt/ruler_icon.png")
        measure_button.setIcon(icon)
        measure_button.setIconSize(QSize(85, 85))
        measure_button.setFlat(True)
        measure_button.setSizePolicy(sp)
        measure_button.clicked.connect(self._slot_measure_captured)


        # organize layout
        self.tool_layout = QVBoxLayout()
        self.tool_layout.addWidget(folder_button)
        self.tool_layout.addWidget(camera_button, alignment=Qt.AlignHCenter)
        self.tool_layout.addWidget(measure_button)


    def _slot_capture(self):
        """slot to take snapshot for both cameras"""
        self.captured_left = self.camera_0.capture()
        self.captured_right = self.camera_1.capture()
        # self.captured_left = np.zeros((3040,4032,3), dtype=np.uint8)
        # self.captured_right = np.zeros((3040,4032,3), dtype=np.uint8)
        print(self.captured_left.shape, self.captured_right.shape)

        # save captured image
        timestamp = strftime("%H:%M:%S", localtime())
        print(f"Saving captured sbs image {timestamp}.jpg ...")
        sbs_captured = np.hstack([self.captured_left, self.captured_right])
        cv2.imwrite(f"datasets/test/{timestamp}.jpg", sbs_captured)

    def _slot_folder_select(self):
        str_path, _ = QFileDialog.getOpenFileName(self, "Select a sbs photo...", ".", "Images (*.png *.jpg)")
        if str_path != '':
            img_path = Path(str_path).relative_to(Path('.').resolve())
            print("Selected photo: " + str(img_path))
            sbs_img = cv2.imread(str(img_path))
            self._slot_measure_sbsfile(sbs_img)

    def _slot_measure_sbsfile(self, sbs_img):
        left_rect, right_rect = self.rectifier.rectify_image(sbs_img=sbs_img)
        self._open_measure_window(left_rect, right_rect)
        
    def _slot_measure_captured(self):
        left_rect, right_rect = self.rectifier.rectify_image(
            img_left=self.captured_left, img_right=self.captured_right)
        self._open_measure_window(left_rect, right_rect)

    def _open_measure_window(self, left_rect, right_rect):
        # measure
        ruler = Ruler(self.rectifier.Q, left_rect, right_rect)
        ruler.click_segment(automatch=True, matcher=MATCHER_TYPE.SIFT)
        len = ruler.measure_segment()
        print(len)
        ruler.show_result()


    def closeEvent(self, event):
        """overriding default close event for qt window"""
        print("Exiting take photo window...")
        self.camera_0.stop()
        self.camera_1.stop()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = TakePhotoWindow()
    widget.show()

    sys.exit(app.exec())
