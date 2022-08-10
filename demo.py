from PyQt5 import QtWidgets
from qt.qt_take_photo import TakePhotoWindow

import sys
import logging
logFormatter = logging.Formatter("[%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)



app = QtWidgets.QApplication([])
widget = TakePhotoWindow()
widget.show()


sys.exit(app.exec())