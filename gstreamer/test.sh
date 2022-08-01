gst-launch-1.0 nvarguscamerasrc ! \
"video/x-raw(memory:NVMM),width=500,height=300,framerate=50/1"  !  tee name=t \
t. ! queue ! fakesink \
t. ! queue ! nvvidconv ! "video/x-raw" ! xvimagesink