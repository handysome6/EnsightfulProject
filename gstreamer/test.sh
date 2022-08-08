gst-launch-1.0 nvarguscamerasrc ! \
'video/x-raw(memory:NVMM), width=4032, height=3040, format=NV12, framerate=30/1' ! \
nvvidconv flip-method=0 ! 'video/x-raw(memory:NVMM)' ! \
nv