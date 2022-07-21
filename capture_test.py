from test_gstreamer.gst_camera import GSTCamera
import time

cam = GSTCamera(test=True)
cam.start_test()
time.sleep(1)
cam.capture()
# time.sleep(2)
# cam.stop()
#exit()
