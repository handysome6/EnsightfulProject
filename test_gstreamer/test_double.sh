gst-launch-1.0 udpsrc port=5005 ! \
'application/x-rtp,encoding-name=H264,payload=96' ! \
rtph264depay ! avdec_h264 ! xvimagesink sync=0