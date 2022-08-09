import sys

from PyQt5.QtWidgets import QWidget, QApplication, QHBoxLayout, QPushButton, QSizePolicy
from PyQt5.QtGui import QWindow

from gstreamer.gst_camera import CameraWithPreview, CameraNoPreview

class TakePhotoWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.showMaximized()
        
        # init camera
        self.camera_0 = CameraWithPreview(sensor_id=0)
        self.camera_1 = CameraNoPreview(sensor_id=1)
        # fetch embedded window handle
        preview_window_xid = self.camera_0.get_window_xid()
        # embed x11 window to qt widget
        embbed_preview_window = QWindow.fromWinId(preview_window_xid)
        embbed_preview_widget = QWidget.createWindowContainer(embbed_preview_window)

        # organize layout
        layout = QHBoxLayout(self)
        layout.addWidget(embbed_preview_widget)
        capture_button = QPushButton("capture")
        layout.addWidget(capture_button)
        #capture_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        capture_button.clicked.connect(self._slot_capture)
    
    def _slot_capture(self):
        """slot to take snapshot for both cameras"""
        frame0 = self.camera_0.capture()
        frame1 = self.camera_1.capture()
        print(frame0.shape, frame1.shape)

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
