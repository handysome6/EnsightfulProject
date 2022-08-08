import sys
import time
import ctypes
import threading
import traceback
import numpy as np
import typing as typ

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
from gi.repository import Gtk, Gst, GLib

RESOLUTION = (4032, 3040)

# Gst.init()
Gtk.init()

def extract_buffer(sample: Gst.Sample) -> np.ndarray:
    """Extracts Gst.Buffer from Gst.Sample and converts to np.ndarray"""

    buffer = sample.get_buffer()  # Gst.Buffer
    #print(buffer.pts, buffer.dts, buffer.offset)

    caps_format = sample.get_caps().get_structure(0)  # Gst.Structure
    w, h = caps_format.get_value('width'), caps_format.get_value('height')
    c = 3

    buffer_size = buffer.get_size()
    shape = (h, w, c) if (h * w * c == buffer_size) else buffer_size
    # print(shape)
    array = np.ndarray(shape=shape, buffer=buffer.extract_dup(0, buffer_size),
                       dtype=np.uint8)

    return np.squeeze(array)  # remove single dimension if exists


class GtkEmbWindow(Gtk.Window):
    def __init__(self, sensor_id=0):
        super().__init__(title = "x11")
        self.set_default_size(500, 400)
        self.connect("destroy", Gtk.main_quit)

        # params
        self.sensor_id = sensor_id
        self.preview_frame = None
        self.preview_readlock = threading.Lock()
        self.read_thread = None
        self.preview_thread = None
        self.capture_thread = None
        self.running = False
        self.FRAME_COUNT = 0
        self.capture_frame = None
        self.SINKPAD_RECEIVED = False
        self.MODE_CAPTURE = False

        
        if sensor_id==0:
            self._init_pipeline_with_preview(sensor_id)
            # get gtksink
            gtksink = self.pipeline.get_by_name("gtksink")
            # get GstGtkWidget from the gtksink's property, MUST
            video_widget = gtksink.get_property("widget")
            # add widget to self
            self.add(video_widget)
            video_widget.realize()

            # dispaly
            self.show_all()
            self.start()
        else:
            self._init_pipeline_no_preview(sensor_id)

    def _init_pipeline_with_preview(self, sensor_id):
        Gst.init(None)
        test_pipeline = f"nvarguscamerasrc sensor-id={sensor_id} ! \
video/x-raw(memory:NVMM), width={RESOLUTION[0]}, height={RESOLUTION[1]}, format=NV12, framerate=30/1 ! \
tee name=t \
t. ! queue ! valve drop=1 name=capture_valve ! \
    nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! video/x-raw,format=RGB ! \
    appsink name=capture_sink async=false emit-signals=1 \
t. ! queue ! nvtee ! \
    nvvidconv ! video/x-raw, width={RESOLUTION[0]//4}, height={RESOLUTION[1]//4}  ! \
    videoconvert ! video/x-raw, format=BGRx ! \
    gtksink name=gtksink"
        print(test_pipeline)
        self.pipeline = Gst.parse_launch(test_pipeline)
        self.capture_valve = self.pipeline.get_by_name("capture_valve")
        self.capture_sink = self.pipeline.get_by_name("capture_sink")
        # message handler
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self._on_message)
        print("init finished")

    def _init_pipeline_no_preview(self, sensor_id):
        Gst.init(None)
        test_pipeline = f"nvarguscamerasrc sensor-id={sensor_id} ! \
video/x-raw(memory:NVMM), width={RESOLUTION[0]}, height={RESOLUTION[1]}, format=NV12, framerate=30/1 ! \
tee name=t \
t. ! queue ! valve drop=1 name=capture_valve ! \
    nvvidconv ! video/x-raw, format=BGRx ! videoconvert ! video/x-raw,format=RGB ! \
    appsink name=capture_sink async=false emit-signals=1 \
t. ! queue ! \
    fakesink"
        # print(test_pipeline)
        self.pipeline = Gst.parse_launch(test_pipeline)
        self.capture_valve = self.pipeline.get_by_name("capture_valve")
        self.capture_sink = self.pipeline.get_by_name("capture_sink")
        # message handler
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self._on_message)
        print("init finished")



    def start(self):
        if self.running:
            print('Video capturing is already running')
            return None

        print("starting pipeline...")
        # start playing 
        self.pipeline.set_state(Gst.State.PLAYING)
        self.loop = GLib.MainLoop()
        # start running 
        self.running = True
        self.read_thread = threading.Thread(target=self._run_main_loop)
        self.read_thread.start()

        # add caputure sink handler
        self.capture_sink.connect("new-sample", self._capture_on_buffer, None)

    def capture(self):
        """open the valve, let buffer flow over"""
        self.capture_valve.set_property("drop", False)
        while self.capture_frame is None:
            time.sleep(0.2)
        capture_frame = self.capture_frame.copy()
        # reset capture_frame for next capture
        self.capture_frame = None
        return capture_frame
        

    def _capture_on_buffer(self, sink, data):
        """Callback serving capture function"""
        # Emit 'pull-sample' signal
        sample = sink.emit("pull-sample")  # Gst.Sample
        if isinstance(sample, Gst.Sample):
            self.capture_frame = extract_buffer(sample)
            print(f"\n\n>>> Captured {type(self.capture_frame)} "
                f"shape {self.capture_frame.shape} "
                f"type {self.capture_frame.dtype} <<<\n")
            # Once fetched a frame, turn down the valve
            self.capture_valve.set_property("drop", True)
            return Gst.FlowReturn.OK
        else:
            return Gst.FlowReturn.ERROR

    def _on_message(self, bus: Gst.Bus, message: Gst.Message):
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

    def read_preview(self):
        with self.preview_readlock:
            preview_frame = self.preview_frame
        return preview_frame

    def stop(self):
        self.running = False
        self.pipeline.set_state(Gst.State.NULL)
        self.loop.quit()
        self.preview_frame = None
        # Kill the thread
        self.read_thread.join()
        self.read_thread = None
        print("\nPipeline finished gracefully.")



    def get_window_handle(self):
        # The window handle must be retrieved first in GUI-thread and before
        # playing pipeline.
        video_window = self.get_property('window')
        if sys.platform == "win32":
            if not video_window.ensure_native():
                print("Error - video playback requires a native window")
            ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
            ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]
            drawingarea_gpointer = ctypes.pythonapi.PyCapsule_GetPointer(video_window.__gpointer__, None)
            gdkdll = ctypes.CDLL ("libgdk-3-0.dll")
            gdkdll.gdk_win32_window_get_handle.argtypes = [ctypes.c_void_p]
            self._video_window_handle = gdkdll.gdk_win32_window_get_handle(drawingarea_gpointer)
            print(self._video_window_handle)
            return self._video_window_handle
        else:
            print(self)
            print(video_window)
            print(video_window.get_xid())
            self._video_window_handle = video_window.get_xid()
            return self._video_window_handle




if __name__ == "__main__":
    win = GtkEmbWindow()
    # win.show_all()
    Gtk.main()
