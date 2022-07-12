gst-launch-1.0 nvarguscamerasrc ! \
'video/x-raw(memory:NVMM), format=NV12, width=4032, height=3040' ! \
tee name=t ! \
queue ! nvv4l2h264enc insert-sps-pps=true ! h264parse !  rtph264pay pt=96 ! \
udpsink host=127.0.0.1 port=5004 sync=false t. ! \
queue ! nvvidconv ! 'video/x-raw(memory:NVMM), width=640, height=480' ! \
nvv4l2h264enc insert-sps-pps=true ! h264parse !  rtph264pay pt=96 ! \
udpsink host=127.0.0.1 port=5005 sync=false