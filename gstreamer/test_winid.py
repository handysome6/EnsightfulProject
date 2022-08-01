from PyQt5.QtWidgets import *
 
import sys
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import GObject, Gst, GstVideo

# I am thinking is wrong but have to admit I do not know much about
# it. Still global anything is generally a bad thing
Gst.init(sys.argv)

class GstDisplay(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.CntrPne = parent

        self.pipeline = Gst.parse_launch(
            'videotestsrc name=source ! videoconvert name=convert ! xvimagesink name=sink')  # xvimagesink, ximagesink
        self.source = self.pipeline.get_by_name("source")
        self.videoconvert = self.pipeline.get_by_name("convert")
        self.sink = self.pipeline.get_by_name("sink")

        self.WinId = self.winId()
        self.setup_pipeline()
        self.start_pipeline()

    def setup_pipeline(self):
        self.state = Gst.State.NULL
        self.source.set_property('pattern', 0)

        if not self.pipeline or not self.source or not self.videoconvert or not self.sink:
            print("ERROR: Not all elements could be created")
            sys.exit(1)

        # instruct the bus to emit signals for each received message
        # and connect to the interesting signals
        bus = self.pipeline.get_bus()

        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect('sync-message::element', self.on_sync_message)

    def on_sync_message(self, bus, msg):
        if msg.get_structure().get_name() == 'prepare-window-handle':
            msg.src.set_window_handle(self.WinId)

    def start_pipeline(self):
        self.pipeline.set_state(Gst.State.PLAYING)

class CentralPanel(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.MainWin = parent

        self.btnPush = QPushButton('Pusher')
        self.btnPush.clicked.connect(self.Pushed)
        
        HBox = QHBoxLayout()
        HBox.addWidget(self.btnPush)
        HBox.addStretch(1)

        self.GstDsply = GstDisplay(None)

        VBox = QVBoxLayout()
        VBox.addWidget(self.GstDsply)
        VBox.addLayout(HBox)
        
        self.setLayout(VBox)

    def Pushed(self):
        print('Quit pushing me down.')

class MainWindow(QMainWindow):
# Do not use Parent unless you are actually going to possibly 
# supply it and due to the nature of where you are calling this
# from that would never happen
#    def __init__(self, parent = None):
    def __init__(self):
# Do not use super( ) unless you fully understand the 3 issues it
# creates that you must protect against within your code further
# unless you need it for the very rare case it was created to fix
# then you are adding more issues to your program than you are 
# removing
#        super(MainWindow, self).__init__(parent)
        super().__init__(None)
        self.setWindowTitle("Prova Gst Qt5")
        Top = 100; Left = 100; Wdth = 640; Hght = 480
        self.setGeometry(Left, Top, Wdth, Hght)
        
        self.CenterPane = CentralPanel(None)
        self.setCentralWidget(self.CenterPane)

if __name__ == '__main__':
# If you are not going to use Command Line arguments then do not code 
# for them but IF you are then looking into the argparser library as 
# it handles Command Line arguments much more cleanly
    MainEvntHndlr = QApplication([])

    MainApp = MainWindow()
    MainApp.show()