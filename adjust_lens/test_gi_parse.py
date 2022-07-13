import numpy as np
# import cv2
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

# This doesn't seem to make any difference
#GObject.threads_init()

Gst.init(None)

# This works

pipe = Gst.parse_launch("""videotestsrc ! 
       appsink sync=false max-buffers=2 drop=true name=sink emit-signals=true""")

sink = pipe.get_by_name('sink')
pipe.set_state(Gst.State.PLAYING)

while True:
	print("Getting a sample")
	sample = sink.emit('pull-sample')
	print(sample.get_buffer().get_size())