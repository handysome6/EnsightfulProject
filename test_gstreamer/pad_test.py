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


pipeline = \
    "nvarguscamerasrc ! tee name=t "\
    "t. ! nvoverlaysink"

def run():
    GLib.MainLoop().run()
def callback(pad, info, user_data):
    return Gst.PadProbeReturn.OK

Gst.init(None)
pipeline = Gst.parse_launch(pipeline)
tee = pipeline.get_by_name("t")
tee_pad = Gst.Element.get_static_pad("src")
pipeline.set_state(Gst.State.PLAYING)
threading.Thread(target=run).start()
time.sleep(5)
tee_pad.add_probe(Gst.PadProbeType.BLOCK_DOWNSTREAM, callback, None)