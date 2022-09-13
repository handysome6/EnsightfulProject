import sys
import cv2
import numpy as np
from pathlib import Path
from measure.matcher import MATCHER_TYPE

from model.camera_model import CameraModel
from calib.rectification import StereoRectify
from utils.utils import snap_subpix_corner, imshow
from measure.ruler import Ruler

try:    id = sys.argv[1]
except: id = 1

# region
# pick image
folder_name = "0801_8mm_IMX477_jetson"
operation_folder = Path("datasets") / folder_name

# operation_folder = Path("datasets") / '0617_IMX477_5000'
# test_folder = operation_folder / 'scenes' 
test_folder = Path("datasets") / 'test' 
assert test_folder.is_dir()
img_path = list(test_folder.iterdir())[int(id)-1]
print("Measuring", img_path.name)

# load camera model
cam_path = Path("example") / "camera_model.json"
camera = CameraModel.load_model(cam_path)
#print(camera)

# rectify image
sbs_img = cv2.imread(str(img_path))
print(sbs_img.shape)
rectifier = StereoRectify(camera, operation_folder)
imgL, imgR = rectifier.rectify_image(sbs_img=sbs_img)
#endregion

# measure
ruler = Ruler(rectifier.Q, imgL, imgR)
run = ruler.click_segment(automatch=True, matcher=MATCHER_TYPE.SIFT)
if run == 1:
    len = ruler.measure_segment()
    print(len)
    ruler.show_result()	
else:
    print("Not enough points, program ends")
