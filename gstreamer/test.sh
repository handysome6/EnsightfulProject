gst-launch-1.0 nvarguscamerasrc ! \
'video/x-raw(memory:NVMM), width=4032, height=3040, format=NV12, framerate=30/1' ! \
nvvidconv flip-method=0 ! 'video/x-raw(memory:NVMM)' ! \
tee name=mytee ! \
queue ! nvvidconv ! video/x-raw, format=BGRx !  \
identity drop-allocation=1 ! v4l2sink device=/dev/video2 \
mytee. ! \
queue ! nvvidconv ! 'video/x-raw(memory:NVMM),width=640,height=480' ! \
nvvidconv ! video/x-raw, format=BGRx ! \
identity drop-allocation=1 ! v4l2sink device=/dev/video3