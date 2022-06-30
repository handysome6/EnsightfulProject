from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from PySide6 import QtCore, QtWidgets, QtGui

class CalibWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Calibrate camera")