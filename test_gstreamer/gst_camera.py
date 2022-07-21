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
    "video/x-raw(memory:NVMM), width=(int)3840, height=(int)2160, framerate=(fraction)30/1 ! "\
    "nvvidconv flip-method=0 ! video/x-raw, width=(int)1280, height=(int)720, format=(string)BGRx ! "\
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


def _helper_add_many(pipeline, list):
    try:
        for element in list:
            pipeline.add(element)
    except:
        print("error when creating element:", element)
        raise


class GSTCamera():
    def __init__(self, test=False) -> None:
        if test == True:
            self._test_init()
        self.preview_frame = None
        self.preview_readlock = threading.Lock()
        self.read_thread = None
        self.preview_thread = None
        self.capture_thread = None
        self.running = False
        self.FRAME_COUNT = 0
        self.capture_frame = None
        self.SINKPAD_RECEIVED = False
        self.MODE_PREVIEW = True

    def _test_init(self):
        Gst.init(None)
        self.pipeline = Gst.Pipeline.new("test-pipeline")
        # create Gst.Element by plugin name 
        self.src = Gst.ElementFactory.make("videotestsrc") 
        src_cap = Gst.Caps.from_string("video/x-raw,format=YV12,width=320,height=240,framerate=30/1")
        self.queue = Gst.ElementFactory.make("queue")
        # test preview -- init
        self.convert = Gst.ElementFactory.make("videoconvert")
        convert_cap = Gst.Caps.from_string("video/x-raw, format=RGB")
        self.appsink = Gst.ElementFactory.make("appsink")
        self.appsink.set_property("emit-signals", True) 
        self.appsink.set_property("drop", True) 
        # test capture -- init
        self.convert2 = Gst.ElementFactory.make("videoconvert")
        self.appsink2 = Gst.ElementFactory.make("appsink")
        self.appsink2.set_property("emit-signals", True) 
        self.convert2.set_state(Gst.State.PLAYING)
        self.appsink2.set_state(Gst.State.PLAYING)

        _helper_add_many(self.pipeline, 
            [self.src, self.queue, self.convert, self.appsink, self.convert2, self.appsink2])
        # test preview -- link
        self.src.link_filtered(self.queue, src_cap)
        self.queue.link(self.convert)
        self.convert.link_filtered(self.appsink, convert_cap)
        self.convert2.link_filtered(self.appsink2, convert_cap)
        print("init finished")

    def start_test(self):
        if self.running:
            print('Video capturing is already running')
            return None
        
        # start playing 
        self.pipeline.set_state(Gst.State.PLAYING)
        self.loop = GObject.MainLoop()
        # message handler
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self._on_message, self.loop)
        # start running 
        self.running = True
        self.read_thread = threading.Thread(target=self._run_main_loop)
        self.read_thread.start()
        print("started thread")
        self._on_buffer(self.appsink, None)
        print("First frame pulled")
        self.appsink.connect("new-sample", self._on_buffer, None)

    def start(self):
        if self.running:
            print('Video capturing is already running')
            return None

        # launch pipeline 
        Gst.init(None)
        self.pipeline = Gst.parse_launch(self.command)
        # start playing 
        self.pipeline.set_state(Gst.State.PLAYING)
        self.loop = GObject.MainLoop()
        # message handler
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self._on_message, self.loop)
        # start running 
        self.running = True
        self.read_thread = threading.Thread(target=self._run_main_loop)
        self.read_thread.start()

        # get AppSink
        self.preview_sink = self.pipeline.get_by_name("preview")
        # pull first frame to avoid reading empty frame
        self._on_buffer(self.preview_sink, None)
        print("First frame pulled")
        self.preview_sink.connect("new-sample", self._on_buffer, None)

    def capture(self):
        target_pad = self.queue.get_static_pad("src")
        target_pad.add_probe(Gst.PadProbeType.BLOCK_DOWNSTREAM, self._capture_switch_cb, None)
        while self.capture_frame is None:
            time.sleep(.1)
        return self.capture_frame

    def _capture_switch_cb(self, pad, info, user_data):
        if self.SINKPAD_RECEIVED:
            # remain block state
            self._capture_on_buffer(self.appsink2, None)
            print("\nFirst capture pulled")
            return Gst.PadProbeReturn.OK
        else:
            if self.MODE_PREVIEW == True:
                # switch mode
                self.queue.unlink(self.convert)
                self.queue.link(self.convert2)
                print("\nMode switched to capture.")
                self.convert2.sync_state_with_parent()
                self.appsink2.sync_state_with_parent()
                self.MODE_PREVIEW = False
                # add buffer listen probe
                capture_pad = self.appsink2.get_static_pad("sink")
                capture_pad.add_probe(Gst.PadProbeType.BUFFER, self._sinkpad_listen_cb, None)
            # when no buffer received, let buffer pass 
            return Gst.PadProbeReturn.PASS

    def _sinkpad_listen_cb(self, pad, info, user_data):
        print("getting buffer")
        self.SINKPAD_RECEIVED = True
        return Gst.PadProbeReturn.OK

    def _capture_on_buffer(self, sink, data):
        """Callback on 'new-sample' signal"""
        # Emit 'pull-sample' signal
        print("pulling")
        sample = sink.emit("pull-sample")  # Gst.Sample
        if isinstance(sample, Gst.Sample):
            self.capture_frame = extract_buffer(sample)
            print(f"\rCaptured {type(self.capture_frame)} "
                f"shape {self.capture_frame.shape} "
                f"type {self.capture_frame.dtype}", end="")
            return Gst.FlowReturn.OK
        else:
            return Gst.FlowReturn.ERROR




    def _on_message(self, bus: Gst.Bus, message: Gst.Message, loop: GObject.MainLoop):
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

        if isinstance(sample, Gst.Sample) and self.running:
            frame = extract_buffer(sample)
            with self.preview_readlock:
                self.preview_frame = frame
            print(f"\rGenerated {self.FRAME_COUNT}-th {type(frame)} shape {frame.shape} type {frame.dtype}", end="")
            self.FRAME_COUNT += 1
            return Gst.FlowReturn.OK
        else:
            return Gst.FlowReturn.ERROR

    def read_preview(self):
        with self.preview_readlock:
            preview_frame = self.preview_frame.copy()
        return preview_frame

    def stop(self):
        self.running = False
        self.pipeline.set_state(Gst.State.NULL)
        self.loop.quit()
        self.preview_frame = None
        # Kill the thread
        self.read_thread.join()
        self.read_thread = None
        print("Pipeline finished gracefully.")





if __name__ == "__main__":
    camera = GSTCamera(DEFAULT_PIPELINE)
    camera.start()

    #time.sleep(1)
    frame = camera.read_preview()
    img = Image.fromarray(frame)
    img.show()
