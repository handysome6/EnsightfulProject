import sys
from PyQt5 import QtCore, QtWidgets
from qt.qt_main import MainWindow
from qt.qt_new import ProjectWindow

app = QtWidgets.QApplication([])
widget = ProjectWindow()
widget.resize(800, 600)
widget.show()

sys.exit(app.exec())