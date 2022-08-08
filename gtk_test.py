import ctypes
import sys
import gi
import time 
gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
gi.require_version('GstVideo', '1.0')
from gi.repository import Gtk, Gst, GstVideo

from PyQt5.QtWidgets import QWidget, QApplication, QHBoxLayout, QPushButton, QSizePolicy
from PyQt5.QtGui import QWindow

from gtksink import GtkEmbWindow
#from GtkWindowHandle import GTK_Main

class TakePhotoWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.showMaximized()
        
        # init camera
        self.camera_0 = GtkEmbWindow(sensor_id=0)
        # self.camera_1 = GtkEmbWindow(sensor_id=1)
        # retrive embedded window handle
        win_handle = self.camera_0.get_window_handle()
        # build qt widget from emb window
        q_emb = QWindow.fromWinId(win_handle)
        q_emb = QWidget.createWindowContainer(q_emb)

        # organize layout
        layout = QHBoxLayout(self)
        layout.addWidget(q_emb)
        capture_button = QPushButton("capture")
        layout.addWidget(capture_button)
        #capture_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        capture_button.clicked.connect(self._slot_capture)
    
    def _slot_capture(self):
        frame0 = self.camera_0.capture()
        # frame1 = self.camera_1.capture()
        print(frame0.shape)

    def closeEvent(self, event):
        print("Exiting take photo window...")
        self.camera_0.stop()
        # self.camera_1.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TakePhotoWindow()
    win.show()
    sys.exit(app.exec())
