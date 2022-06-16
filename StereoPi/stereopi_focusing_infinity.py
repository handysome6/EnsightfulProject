import picamera
from picamera import PiCamera
import time
import cv2
import numpy as np
import os
from datetime import datetime


# File for captured image
filename = './scenes/photo.png'

# Camera settimgs
cam_width = 8112
cam_height = 3040

# Final image capture settings
scale_ratio = 0.1

# Camera resolution height must be dividable by 16, and width by 32
cam_width = int((cam_width+31)/32)*32
cam_height = int((cam_height+15)/16)*16
print ("Used camera resolution: "+str(cam_width)+" x "+str(cam_height))

# Buffer for captured image settings
img_width = int (cam_width * scale_ratio)
img_height = int (cam_height * scale_ratio)
capture = np.zeros((img_height, img_width, 4), dtype=np.uint8)
print ("Scaled image resolution: "+str(img_width)+" x "+str(img_height))

# Initialize the camera
camera = PiCamera(stereo_mode='side-by-side',stereo_decimate=False)
camera.resolution=(cam_width, cam_height)
camera.framerate = 20
camera.hflip = True

def Laplacian(img):
    '''
    :param img:narray 二维灰度图像
    :return: float 图像约清晰越大
    '''
    return cv2.Laplacian(img,cv2.CV_64F).var()

midL = [cam_width // 4, cam_height // 2]
midR = [cam_width // 4 * 3, cam_height // 2]
d = 200
print("\tLeft\tRight")

t2 = datetime.now()
counter = 0
avgtime = 0
# Capture frames from the camera
for frame in camera.capture_continuous(capture, format="bgra", use_video_port=True, resize=(img_width,img_height)):
    counter+=1
    t1 = datetime.now()
    timediff = t1-t2
    avgtime = avgtime + (timediff.total_seconds())
    cv2.imshow("pair", frame)
    key = cv2.waitKey(1) & 0xFF
    t2 = datetime.now()

    # show cropped
    cropL = frame[midL[0]-d:midL[0]+d, midL[1]-d:midL[1]+d]
    cropR = frame[midR[0]-d:midR[0]+d, midR[1]-d:midR[1]+d]
    # cv2.imshow("pair", np.hstack([cropL, cropR]))

    # calculate sharpness
    sharpnessL = Laplacian(cv2.cvtColor(cropL, cv2.COLOR_BGR2GRAY))
    sharpnessR = Laplacian(cv2.cvtColor(cropR, cv2.COLOR_BGR2GRAY))
    print(f"\r\t{sharpnessL}\t{sharpnessR}", end='')


    # if the `q` key was pressed, break from the loop and save last image
    if key == ord("q") :
        avgtime = avgtime/counter
        print ("Average time between frames: " + str(avgtime))
        print ("Average FPS: " + str(1/avgtime))
        # if (os.path.isdir("./scenes")==False):
        #     os.makedirs("./scenes")
        # cv2.imwrite(filename, frame)
        break