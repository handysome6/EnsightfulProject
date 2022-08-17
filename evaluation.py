import sys
from PyQt5 import QtWidgets
from qt.qt_eval import Evaluation

app = QtWidgets.QApplication([])
widget = Evaluation()
widget.resize(800, 600)
widget.show()

sys.exit(app.exec())