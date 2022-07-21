from gstreamer.gst_camera import GSTCamera
import time

cam = GSTCamera()
cam.start()
time.sleep(1)
cam.capture()
time.sleep(2)
cam.stop()
#exit()
