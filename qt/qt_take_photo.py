import sys
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimeLine
from PyQt5.QtWidgets import QWidget, QLabel, QSizePolicy, QPushButton, QGridLayout
from PyQt5 import QtCore, QtWidgets, QtGui
import cv2
import numpy as np
from gstreamer.gst_camera import GSTCamera
import time

class TakePhotoWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Take a photo")
        self._init_region()
        self._init_camera()
        self._init_timeline()
        self.FRAME_COUNT = 0

    def _init_region(self):
        self.preview_label = QLabel()
        self.stop_btn = QPushButton("Stop")
        self.capture_btn = QPushButton("Capture")
        self.stop_btn.clicked.connect(self._slot_stop_preview)
        self.capture_btn.clicked.connect(self._slot_capture_hd)
        #self.preview_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        #self.preview_label.setScaledContents(True)

        self.main_layout = QGridLayout(self)
        self.main_layout.addWidget(self.preview_label, 0, 0, 1, 2)
        self.main_layout.addWidget(self.stop_btn, 1, 0, 1, 1)
        self.main_layout.addWidget(self.capture_btn, 1, 1, 1, 1)

    def _init_camera(self):
        self.camera_0 = GSTCamera(sensor_id=0)
        self.camera_0.start()
        self.camera_1 = GSTCamera(sensor_id=1)
        self.camera_1.start()

    def _init_timeline(self):
        self.timeline = QTimeLine(duration=99999, parent=self)
        self.timeline.setFrameRange(0, 99999)
        self.timeline.setUpdateInterval(int(1000/30))
        self.timeline.frameChanged.connect(self._slot_update_frame)
        self.timeline.start()
        #time.sleep(1)
        #img_0 = self.camera_0.capture()

    def _slot_update_frame(self):
        frame = self.camera_0.read_preview()
        print(f"\rFetched {self.FRAME_COUNT}-th {type(frame)} frame with shape {frame.shape} of type {frame.dtype}", end="")
        self.FRAME_COUNT += 1
        height, width, channel = frame.shape
        bytesPerLine = 3 * width
        frame_qimg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888) 
        self.preview_label.setPixmap(QPixmap(frame_qimg))

    def _slot_stop_preview(self):
        self.timeline.stop()

    def _slot_capture_hd(self):
        img_0 = self.camera_0.capture()
        img_1 = self.camera_1.capture()
        img_sbs = np.concatenate([img_0, img_1], axis=1)
        cv2.imwrite("sbs_00.jpg", img_sbs)
        self.close()

    def closeEvent(self, event):
        print("Exiting take photo window...")
        self.timeline.stop()
        self.camera_0.stop()
        self.camera_1.stop()



if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = TakePhotoWindow()
    widget.show()

    sys.exit(app.exec())
