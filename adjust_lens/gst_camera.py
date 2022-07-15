import sys
import threading
import traceback
import typing as typ
import time
import cv2

import numpy as np
from PIL import Image

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import GObject, Gst, GLib, GstApp, GstVideo

DEFAULT_PIPELINE = \
    "nvarguscamerasrc ! "\
    "video/x-raw(memory:NVMM), width=(int)1280, height=(int)720, framerate=(fraction)24/1 ! "\
    "nvvidconv flip-method=2 ! video/x-raw, format=(string)BGRx ! "\
    "videoconvert ! video/x-raw, format=(string)RGB ! "\
    "appsink name=preview emit-signals=True"


def extract_buffer(sample: Gst.Sample) -> np.ndarray:
    """Extracts Gst.Buffer from Gst.Sample and converts to np.ndarray"""

    buffer = sample.get_buffer()  # Gst.Buffer
    #print(buffer.pts, buffer.dts, buffer.offset)

    caps_format = sample.get_caps().get_structure(0)  # Gst.Structure
    w, h = caps_format.get_value('width'), caps_format.get_value('height')
    c = 3

    buffer_size = buffer.get_size()
    shape = (h, w, c) if (h * w * c == buffer_size) else buffer_size
    array = np.ndarray(shape=shape, buffer=buffer.extract_dup(0, buffer_size),
                       dtype=np.uint8)

    return np.squeeze(array)  # remove single dimension if exists


class GSTCamera():
    def __init__(self, command) -> None:
        self.command = command
        self.preview_frame = None
        self.preview_readlock = threading.Lock()

        self.read_thread = None
        self.preview_thread = None
        self.capture_thread = None
        self.running = False
    

    def start(self):
        if self.running:
            print('Video capturing is already running')
            return None

        # launch pipeline 
        self.pipeline = Gst.parse_launch(self.command)
        # start playing 
        self.pipeline.set_state(Gst.State.PLAYING)
        self.loop = GObject.MainLoop()
        # message handler
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self.on_message, self.loop)
        # start running 
        self.running = True
        self.read_thread = threading.Thread(target=self._run_main_loop)
        self.read_thread.start()
        # pull first frame
        self._on_buffer(self.preview_sink, None)
        print("First frame pulled")
        # get AppSink
        self.preview_sink = self.pipeline.get_by_name("preview")
        self.preview_sink.connect("new-sample", self._on_buffer, None)

    
    def on_message(self, bus: Gst.Bus, message: Gst.Message, loop: GObject.MainLoop):
        mtype = message.type
        if mtype == Gst.MessageType.EOS:
            print("End of stream")
            self.loop.quit()
        elif mtype == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(err, debug)
            self.loop.quit()
        elif mtype == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            print(err, debug)

        return True


    def _run_main_loop(self):
        try:
            self.loop.run()
        except Exception:
            traceback.print_exc()
            self.loop.quit()


    def _on_buffer(self, sink: GstApp.AppSink, data: typ.Any) -> Gst.FlowReturn:
        """Callback on 'new-sample' signal"""
        # Emit 'pull-sample' signal
        sample = sink.emit("pull-sample")  # Gst.Sample

        if isinstance(sample, Gst.Sample):
            frame = extract_buffer(sample)
            with self.preview_readlock:
                self.preview_frame = frame
            print(f"Received {type(frame)} with shape {frame.shape} of type {frame.dtype}")
            return Gst.FlowReturn.OK
        else:
            return Gst.FlowReturn.ERROR


    def read_preview(self):
        with self.preview_readlock:
            preview_frame = self.preview_frame.copy()
        return preview_frame


    def stop(self):
        self.running = False
        self.loop.quit()
        # Kill the thread
        self.read_thread.join()
        self.read_thread = None





camera = GSTCamera(DEFAULT_PIPELINE)
camera.start()

#time.sleep(1)
frame = camera.read_preview()
img = Image.fromarray(frame)
img.show()