gst-launch-1.0 nvarguscamerasrc ! 'video/x-raw(memory:NVMM)' !\
	tee name=t \
	t. ! queue ! nvvidconv ! 'video/x-raw, width=1080, height=720' ! xvimagesink \
	t. ! queue ! nvvidconv ! 'video/x-raw, width=640, height=480' ! ximagesink
