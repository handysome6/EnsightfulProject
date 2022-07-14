import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst, GLib
   

GObject.threads_init()
Gst.init(None)


class Sender:
    def __init__(self):
        # Create GStreamer pipeline
        self.pipeline = Gst.parse_launch(
        "nvarguscamerasrc ! "
        "appsink sync=false max-buffers=2 drop=true name=preview emit-signals=true"
        )

        # Create bus to get events from GStreamer pipeline
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::error', self.on_error)

        self.preview_sink = self.pipeline.get_by_name("preview")
        print(type(self.pipeline))
        print(type(self.preview_sink))


    # run the program
    def run(self):
            self.pipeline.set_state(Gst.State.PLAYING)
            
            sample = self.preview_sink.emit('pull-sample')
            print(type(sample))
            print(type(sample.get_buffer()))
            GLib.MainLoop().run()

    def on_error(self, bus, msg):
            print('on_error():', msg.parse_error())


## START EVERYTHING
if __name__ == '__main__':
    sender = Sender()
    sender.run()