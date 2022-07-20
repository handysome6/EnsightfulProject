gst-launch-1.0 nvarguscamerasrc ! \
'video/x-raw(memory:NVMM), format=NV12, width=4056, height=3040, framerate=(fraction)20/1' ! \
tee name=t \
t. ! queue ! nvvidconv ! 'video/x-raw, width=1080, height=720' ! xvimagesink \
t. ! queue ! nvvidconv ! 'video/x-raw(memory:NVMM), width=1080, height=720' ! \
nvv4l2h264enc insert-sps-pps=true idrinterval=15 ! h264parse !  rtph264pay ! \
udpsink host=127.0.0.1 port=5005 sync=false
