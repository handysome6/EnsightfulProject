import sys
from PyQt5 import QtCore, QtWidgets
from qt.qt_main import MainWindow
from qt.qt_new import ProjectWindow
import sys
import logging
from pathlib import Path
logFormatter = logging.Formatter("[%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)



app = QtWidgets.QApplication([])
widget = ProjectWindow()
widget.resize(800, 600)
widget.show()

sys.exit(app.exec())