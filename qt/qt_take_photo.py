import sys

from PyQt5.QtWidgets import QWidget, QApplication, QHBoxLayout, QPushButton, QSizePolicy
from PyQt5.QtGui import QWindow, QIcon
from PyQt5.QtCore import QSize

from gstreamer.gst_camera import CameraWithPreview, CameraNoPreview

class TakePhotoWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.showMaximized()
        
        # init camera
        self.camera_0 = CameraWithPreview(sensor_id=0)
        self.camera_1 = CameraNoPreview(sensor_id=1)

        # preview widget
        # fetch embedded window handle, embed x11 window to qt widget
        preview_window_xid = self.camera_0.get_window_xid()
        embbed_preview_window = QWindow.fromWinId(preview_window_xid)
        embbed_preview_widget = QWidget.createWindowContainer(embbed_preview_window)
        # embbed_preview_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

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

        # organize layout
        layout = QHBoxLayout(self)
        layout.addWidget(embbed_preview_widget)
        layout.addWidget(camera_button)
    
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
