gst-launch-1.0 udpsrc port=5000 ! \
application/x-rtp,encoding-name=H264 ! \
rtph264depay ! h264parse ! nvv4l2decoder ! nvvidconv ! \
xvimagesink