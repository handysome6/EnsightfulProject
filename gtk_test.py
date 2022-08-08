import ctypes
import sys
import gi
import time 
gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
gi.require_version('GstVideo', '1.0')
from gi.repository import Gtk, Gst, GstVideo

from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication, QVBoxLayout, QPushButton
from PyQt5.QtGui import QWindow

from gtksink import GtkEmbWindow
#from GtkWindowHandle import GTK_Main

class qtgtk(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.showMaximized()
        
        win = GtkEmbWindow()
        win_handle = win.get_window_handle()
        q_emb = QWindow.fromWinId(win_handle)
        q_emb = QWidget.createWindowContainer(q_emb)
        layout = QVBoxLayout(self)
        layout.addWidget(q_emb)
        layout.addWidget(QPushButton())



app = QApplication(sys.argv)
win = qtgtk()
win.show()
sys.exit(app.exec())
