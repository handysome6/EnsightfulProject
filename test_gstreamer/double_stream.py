import cv2

cap = cv2.VideoCapture("nvarguscamerasrc ! video/x-raw(memory:NVMM), width=(int)1920, height=(int)1080,format=(string)NV12, framerate=(fraction)30/1 ! nvvidconv ! video/x-raw, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! queue ! appsink drop=1", cv2.CAP_GSTREAMER)
if not cap.isOpened():
   print('Failed to open camera')
   exit

rtpudp1080 = cv2.VideoWriter("appsrc ! queue ! videoconvert ! video/x-raw,format=BGRx ! nvvidconv ! nvv4l2h264enc insert-sps-pps=1 insert-vui=1 ! rtph264pay ! udpsink host=127.0.0.1 port=5000", cv2.CAP_GSTREAMER, 0, 30.0, (1920,1080)) 
if not rtpudp1080.isOpened():
   print('Failed to open rtpudp1080')
   cap.release()
   exit

rtpudp320 = cv2.VideoWriter("appsrc ! queue ! videoconvert ! video/x-raw,format=BGRx ! nvvidconv ! video/x-raw(memory:NVMM),width=320,height=240 ! nvv4l2h264enc insert-sps-pps=1 insert-vui=1 ! rtph264pay ! udpsink host=127.0.0.1 port=5001", cv2.CAP_GSTREAMER, 0, 30.0, (1920,1080)) 
if not rtpudp320.isOpened():
   print('Failed to open rtpudp320')
   rtpudp1080.release()
   cap.release()
   exit


for i in range(300):
	ret_val, img = cap.read();
	if not ret_val:
		break

	rtpudp1080.write(img);
	rtpudp320.write(img);
	cv2.waitKey(1)



rtpudp320.release()
rtpudp1080.release()
cap.release()