from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QProcess, QIODevice
import sys

app = QApplication([])
window = QWidget()
videoWidget = QVideoWidget()
layout = QVBoxLayout()
player = QMediaPlayer()
process = QProcess()

layout.addWidget(videoWidget)
window.setLayout(layout)
window.show()
player.setVideoOutput(videoWidget)

program = "gst-launch-1.0"
arguments = ["-v", "videotestsrc", "!", "video/x-raw,width=1280,height=720", "!", "x264enc", "!", "filesink", "location=/dev/stderr"]

process.start(program, arguments)
process.waitForReadyRead()
# print(process)
player.setMedia(QMediaContent(), process)
player.play()

sys.exit(app.exec())