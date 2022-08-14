import time
import threading
import traceback
import numpy as np

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
from gi.repository import Gtk, Gst, GLib

RESOLUTION = (4032, 3040)

def extract_buffer(sample: Gst.Sample) -> np.ndarray:
    """Extracts Gst.Buffer from Gst.Sample and converts to np.ndarray"""

    buffer = sample.get_buffer()  # Gst.Buffer
    #print(buffer.pts, buffer.dts, buffer.offset)

    caps_format = sample.get_caps().get_structure(0)  # Gst.Structure
    w, h = caps_format.get_value('width'), caps_format.get_value('height')
    c = 4

    buffer_size = buffer.get_size()
    shape = (h, w, c) if (h * w * c == buffer_size) else buffer_size
    # print(shape)
    array = np.ndarray(shape=shape, buffer=buffer.extract_dup(0, buffer_size),
                       dtype=np.uint8)

    return np.squeeze(array)  # remove single dimension if exists



class DualCameraWithPreview(Gtk.Window):
    """This init camera with preview using Gstreamer + gtksink.
    You can fetch the preview window's xid by get_window_xid(). 
    (Implemented using Gtk, for linux only)"""
    def __init__(self, sensor_id=0):
        super().__init__(title = f"camera {sensor_id} preview")
        Gtk.init()
        self.connect("destroy", Gtk.main_quit)

        # params
        self.sensor_id = sensor_id
        self.preview_frame = None
        self.read_thread = None
        self.running = False
        self.FRAME_COUNT = 0
        self.capture_frame = None

        # init pipeline, gtk winodw and start Gst pipeline
        self._init_pipeline_gtksink(sensor_id)
        self._init_x11_preview()
        self.start()

    def get_window_xid(self):
        # The window handle must be retrieved first in GUI-thread and before
        # playing pipeline.
        # Only works in Linux, which use X11
        preview_window_xid = self.get_window().get_xid()
        return preview_window_xid

    def _init_pipeline_gtksink(self, sensor_id):
        Gst.init(None)
        dual_pipeline = f"\
nvarguscamerasrc sensor-id={sensor_id} ! video/x-raw(memory:NVMM), width={RESOLUTION[0]}, height={RESOLUTION[1]}, format=NV12, framerate=30/1 ! \
tee name=t \
    t. ! \
        queue ! nvvidconv ! video/x-raw, width={RESOLUTION[0]//4}, height={RESOLUTION[1]//4} ! \
            gtksink name=gtksink\
    t. ! \
        valve drop=1 name=valve_0 ! nvvidconv ! video/x-raw, format=RGBA ! \
            mix.sink_0 \
\
nvarguscamerasrc sensor-id={1-sensor_id} ! video/x-raw(memory:NVMM), width={RESOLUTION[0]}, height={RESOLUTION[1]}, format=NV12, framerate=10/1 ! \
        valve drop=1 name=valve_1 ! nvvidconv ! video/x-raw, format=RGBA ! \
            mix.sink_1 \
\
compositor name=mix  sink_0::xpos=0 sink_0::ypos=0  sink_1::xpos=4032 sink_1::ypos=0 ! \
    video/x-raw,format=RGBA ! \
    appsink name=capture_sink async=false emit-signals=1 "
        
        # print(gtksink_pipeline)
        self.pipeline = Gst.parse_launch(dual_pipeline)
        self.valve_0 = self.pipeline.get_by_name("valve_0")
        self.valve_1 = self.pipeline.get_by_name("valve_1")
        self.capture_sink = self.pipeline.get_by_name("capture_sink")
        # message handler
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self._on_message)
        print("init pipeline with gtksink finished")

    def _init_x11_preview(self):
        # get gtksink
        gtksink = self.pipeline.get_by_name("gtksink")
        # get GstGtkWidget from the gtksink's property, MUST
        video_widget = gtksink.get_property("widget")
        # add widget to self
        self.add(video_widget)
        video_widget.realize()

        # dispaly
        self.show_all()

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
        self.valve_0.set_property("drop", False)
        self.valve_1.set_property("drop", False)
        while self.capture_frame is None:
            time.sleep(0.1)
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
            self.valve_0.set_property("drop", True)
            self.valve_1.set_property("drop", True)
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

    def pause(self):
        print("pausing pipeline...")
        self.pipeline.set_state(Gst.State.PAUSED)

    def resume(self):
        print("resuming pipeline...")
        self.pipeline.set_state(Gst.State.PLAYING)


    def stop(self):
        self.running = False
        self.pipeline.set_state(Gst.State.NULL)
        self.loop.quit()
        self.preview_frame = None
        # Kill the thread
        self.read_thread.join()
        self.read_thread = None
        print("\nPipeline finished gracefully.")





if __name__ == "__main__":
    cam = DualCameraWithPreview()
    # Gtk.main()
    time.sleep(2)
    cam.capture()
    time.sleep(2)
    cam.capture()
    time.sleep(1)
    cam.stop()
