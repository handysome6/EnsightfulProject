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
    "videotestsrc ! tee name=t "\
    "t. ! queue ! xvimagesink "\
    "t. ! queue ! videoconvert name=target ! xvimagesink "

def run():
    GLib.MainLoop().run()
def callback(pad, info, user_data):
    print("entered callback")
    time.sleep(3)
    print("probe id:", info.id)
    pad.remove_probe(info.id)
    print("sink flushed")
    return Gst.PadProbeReturn.REMOVE

Gst.init(None)
pipeline = Gst.parse_launch(pipeline)
target = pipeline.get_by_name("target")
target_pad = target.get_static_pad("sink")
if target_pad is None:
    print("pad not retrived, exiting"); exit(1)
pipeline.set_state(Gst.State.PLAYING)
threading.Thread(target=run).start()
print("main loop started")
time.sleep(3)
target_pad.add_probe(Gst.PadProbeType.BLOCK_DOWNSTREAM, callback, None)
print("sink blocked")
