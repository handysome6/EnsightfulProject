import ctypes
import sys
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
from gi.repository import Gtk, Gst

Gst.init()
Gtk.init()


class GtkEmbWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title = "x11")
        self.set_default_size(500, 400)
        self.connect("destroy", Gtk.main_quit)


        pipeline = Gst.parse_launch("videotestsrc ! video/x-raw,width=1280, height=720 ! gtksink name=gtksink")
        gtksink = pipeline.get_by_name("gtksink")
        video_widget = gtksink.get_property("widget")

        self.add(video_widget)
        video_widget.realize()

        self.show_all()
        pipeline.set_state(Gst.State.PLAYING)

        # print(self.get_window().get_xid())

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
