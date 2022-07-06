from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from PyQt5 import QtCore, QtWidgets, QtGui

class TakePhotoWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Take a photo")