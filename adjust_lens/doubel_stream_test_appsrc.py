import cv2
import threading
import numpy as np

class CSI_Camera:

    def __init__(self):
        """Initialize instance variables
        """        
        # OpenCV video capture element
        self.video_capture = None
        # The last captured image from the camera
        self.frame = None
        self.grabbed = False
        # The thread where the video capture runs
        self.read_thread = None
        self.read_lock = threading.Lock()
        self.running = False

    def open(self, gstreamer_pipeline_string):
        try:
            self.video_capture = cv2.VideoCapture(
                gstreamer_pipeline_string, cv2.CAP_GSTREAMER
            )
            # Grab the first frame to start the video capturing
            self.grabbed, self.frame = self.video_capture.read()

        except RuntimeError:
            self.video_capture = None
            print("Unable to open camera")
            print("Pipeline: " + gstreamer_pipeline_string)

    def start(self):
        if self.running:
            print('Video capturing is already running')
            return None
        # create a thread to read the camera image
        if self.video_capture != None:
            self.running = True
            self.read_thread = threading.Thread(target=self.updateCamera)
            self.read_thread.start()
        return self

    def stop(self):
        self.running = False
        # Kill the thread
        self.read_thread.join()
        self.read_thread = None

    def updateCamera(self):
        # This is the thread to read images from the camera
        while self.running:
            try:
                grabbed, frame = self.video_capture.read()
                with self.read_lock:
                    self.grabbed = grabbed
                    self.frame = frame
            except RuntimeError:
                print("Could not read image from camera")

    def read(self):
        with self.read_lock:
            frame = self.frame.copy()
            grabbed = self.grabbed
        return grabbed, frame

    def release(self):
        if self.video_capture != None:
            self.video_capture.release()
            self.video_capture = None
        # Now kill the thread
        if self.read_thread != None:
            self.read_thread.join()

# src_pipeline = "nvarguscamerasrc ! video/x-raw(memory:NVMM), width=(int)4056, height=(int)3040,format=(string)NV12, framerate=(fraction)30/1 ! nvvidconv ! video/x-raw, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! queue ! appsink drop=1"
# camera_src = CSI_Camera()
# camera_src.open(src_pipeline)
# camera_src.start()

preview_pipeline = "udpsrc port=5005 ! application/x-rtp,encoding-name=H264,payload=96 ! rtph264depay ! h264parse ! decodebin ! videoconvert ! appsink sync=0"
cam_preview = CSI_Camera()
cam_preview.open(preview_pipeline)
cam_preview.start()

window_title = "preview"
if cam_preview.video_capture.isOpened():
    cv2.namedWindow(window_title, cv2.WINDOW_AUTOSIZE)

    try:
        while True:
            _, preview_image = cam_preview.read()
            # Use numpy to place images next to each other
            # camera_images = np.hstack((left_image, right_image)) 
            if cv2.getWindowProperty(window_title, cv2.WND_PROP_AUTOSIZE) >= 0:
                cv2.imshow(window_title, preview_image)
            else:
                break

            # This also acts as
            keyCode = cv2.waitKey(30) & 0xFF
            # Stop the program on the ESC key
            if keyCode == 27:
                break
    finally:

        cam_preview.stop()
        cam_preview.release()
        # right_camera.stop()
        # right_camera.release()
    cv2.destroyAllWindows()
else:
    print("Error: Unable to open both cameras")
    cam_preview.stop()
    cam_preview.release()

