gst-launch-1.0 nvarguscamerasrc ! \
"video/x-raw(memory:NVMM),width=4032,height=3040,framerate=30/1"  !  tee name=t \
t. ! queue ! fakesink \
t. ! queue ! nvvidconv ! "video/x-raw, width=1280,height=720" ! xvimagesink