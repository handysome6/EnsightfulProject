import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GLib
   

GObject.threads_init()
Gst.init(None)


class Sender:
	def __init__(self):
		# Create GStreamer pipeline
		self.pipeline = Gst.Pipeline()

		# Create bus to get events from GStreamer pipeline
		self.bus = self.pipeline.get_bus()
		self.bus.add_signal_watch()
		self.bus.connect('message::error', self.on_error)


		# Create GStreamer elements
		# Video source device
		self.src = Gst.ElementFactory.make('nvcamerasrc', None)

		# conversion pipeline
		self.srccaps = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=(string)I420")
		self.nvoverlaysink = Gst.ElementFactory.make('nvoverlaysink', None)

		# Add elements to the pipeline
		self.pipeline.add(self.src)
		self.pipeline.add(self.nvoverlaysink)


		self.src.link_filtered(self.nvoverlaysink, self.srccaps)


	# run the program
	def run(self):
		self.pipeline.set_state(Gst.State.PLAYING)
		GLib.MainLoop().run()

	def on_error(self, bus, msg):
		print('on_error():', msg.parse_error())


## START EVERYTHING
if __name__ == '__main__':
	sender = Sender()
	sender.run()