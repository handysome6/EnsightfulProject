from PyQt5 import QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import sys
from pathlib import Path
from PIL import Image
from PIL.ImageQt import ImageQt 

app = QApplication([])

lw = QListWidget()
lw.setViewMode(QListWidget.IconMode)
lw.setResizeMode(QListWidget.Adjust)
lw.setMovement(QListView.Static)
lw.setIconSize(QSize(230,230))

# item = QListWidgetItem()
test_folder = Path('datasets/0617_IMX477_5000') / 'test'
imgs = list(test_folder.glob("*.jpg"))
for img_path in imgs[:2]:
    with Image.open(str(img_path)) as im:
        width, height = im.size
        new_width = width // 2
        view = im.transform((532,400), Image.Transform.EXTENT, data=(0,0,new_width, height))
        icon = QIcon(QPixmap.fromImage(ImageQt(view)))
        # icon = QIcon("qt/cam_model_icon.png")
        item = QListWidgetItem(icon, img_path.name, lw)
        # attach data to the list item
        item.setData(Qt.UserRole, img_path)
        lw.addItem(item)


lw.show()

sys.exit(app.exec())