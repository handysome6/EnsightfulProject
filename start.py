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

# import os
# path ="//home/andyls/.local/lib/python3.8/site-packages/PyQt5/Qt5/plugins/platforms/"
# os.environ['QT_QPA_PLATFORM_PLUGIN_PATH']=path


app = QtWidgets.QApplication([])
widget = MainWindow()
# widget.resize(800, 600)
widget.show()

sys.exit(app.exec())