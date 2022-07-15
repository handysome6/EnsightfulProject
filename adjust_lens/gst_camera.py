import sys
import threading
import traceback
import typing as typ
import time
import cv2

import numpy as np

from gstreamer import GstContext, GstPipeline, GstApp, Gst, GstVideo
import gstreamer.utils as utils

# Converts list of plugins to gst-launch string
DEFAULT_PIPELINE = utils.to_gst_string([
    "videotestsrc num-buffers=100",
    "capsfilter caps=video/x-raw,format=RGB,width=640,height=480",
    "queue",
    "appsink emit-signals=True"
])


def extract_buffer(sample: Gst.Sample) -> np.ndarray:
    """Extracts Gst.Buffer from Gst.Sample and converts to np.ndarray"""

    buffer = sample.get_buffer()  # Gst.Buffer

    print(buffer.pts, buffer.dts, buffer.offset)

    caps_format = sample.get_caps().get_structure(0)  # Gst.Structure

    # GstVideo.VideoFormat
    video_format = GstVideo.VideoFormat.from_string(
        caps_format.get_value('format'))

    w, h = caps_format.get_value('width'), caps_format.get_value('height')
    c = utils.get_num_channels(video_format)

    buffer_size = buffer.get_size()
    shape = (h, w, c) if (h * w * c == buffer_size) else buffer_size
    array = np.ndarray(shape=shape, buffer=buffer.extract_dup(0, buffer_size),
                       dtype=utils.get_np_dtype(video_format))

    return np.squeeze(array)  # remove single dimension if exists


class GSTCamera():
    def __init__(self) -> None:
        self.command = DEFAULT_PIPELINE
        self.preview_frame = None
        self.preview_readlock = threading.Lock()

        self.read_thread = None
        self.preview_thread = None
        self.capture_thread = None
        self.running = False
    
    def start_read(self):
        if self.running:
            print('Video capturing is already running')
            return None
        # create a thread to read the camera image
        if self.command != None:
            self.running = True
            self.read_thread = threading.Thread(target=self.update_camera)
            self.read_thread.start()
        return self

    def update_camera(self):
        with GstContext():  # create GstContext (hides MainLoop)
            with GstPipeline(command) as pipeline: # create GstPipeline (hides Gst.parse_launch)
                appsink = pipeline.get_by_cls(GstApp.AppSink)[0]  # get AppSink
                appsink.connect("new-sample", self.on_buffer, None)  # subscribe to <new-sample> signal
                while self.running:
                    time.sleep(.1)

    def on_buffer(self, sink: GstApp.AppSink, data: typ.Any) -> Gst.FlowReturn:
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
        # Kill the thread
        self.read_thread.join()
        self.read_thread = None

    def release(self):
        if self.read_thread != None:
            self.read_thread.join()






camera = GSTCamera()
camera.start_read()

time.sleep(5)
window_title = "preview"
cv2.namedWindow(window_title, cv2.WINDOW_AUTOSIZE)
while True:
    frame = camera.read_preview()
    # Check to see if the user closed the window
    if cv2.getWindowProperty(window_title, cv2.WND_PROP_AUTOSIZE) >= 0:
        cv2.imshow(window_title, frame)
    else:
        break

    keyCode = cv2.waitKey(30) & 0xFF
    if keyCode == 27:
        break
