import cv2
import numpy as np
from pathlib import Path
from utils.utils import imshow, snap_subpix_corner
from measure.matcher import MATCHER_TYPE, AutoMatcher
from measure.click_coord import ClickImage
from model.camera_model import CameraModel
from calib.rectification import StereoRectify

img_folder = Path('datasets') / '0617_IMX477_5000' 
left_path  = img_folder / 'rectify_02_left.jpg'
right_path = img_folder / 'rectify_02_right.jpg'
left = cv2.cvtColor(cv2.imread(str(left_path)), cv2.COLOR_BGR2GRAY)
right = cv2.cvtColor(cv2.imread(str(right_path)), cv2.COLOR_BGR2GRAY)
# left = cv2.imread(str(left_path))
# right = cv2.imread(str(right_path))



id = 2
# load camera model
operation_folder = Path("datasets") / '0617_IMX477_5000'
cam_path = operation_folder / "calibration_data" / "camera_model.npz"
camera = CameraModel.load_model(cam_path)

test_folder = operation_folder / 'scenes' 
test_folder = operation_folder / 'test' 
assert test_folder.is_dir()
img_path = list(test_folder.iterdir())[int(id)-1]
print("Measuring", img_path.name)

# rectify image
sbs_img = cv2.imread(str(img_path))
rectifier = StereoRectify(camera, operation_folder)
imgL, imgR = rectifier.rectify_image(sbs_img)
left = cv2.cvtColor(imgL,cv2.COLOR_BGR2GRAY)
right = cv2.cvtColor(imgR,cv2.COLOR_BGR2GRAY)



# click to get raw coord
clicker = ClickImage(left, 'left')
coords = clicker.click_coord(num=3)
coords = snap_subpix_corner(left, coords)
coords = np.array(coords, dtype=np.int32)
print(coords)



regions = []
kps = []
# auto match point
matcher = AutoMatcher(left, right, MATCHER_TYPE.SIFT)
for coord in coords:
    region, top_kps = matcher.match(coord, show_result=False)
    regions += region
    kps.append(top_kps)
regions = np.reshape(np.array(regions), -1)
# print(regions[0])
kps = np.reshape(np.array(kps), -1)

# Search region - Green
show_fig = cv2.drawKeypoints(right, regions, None, color = (0, 255, 0))
# Top keypoionts - Red
show_fig = cv2.drawKeypoints(show_fig, kps, None, color = (255, 0, 0), 
    flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
# cv2.imwrite('datasets/BOOST.jpg', show_fig)
imshow("Matching result", show_fig)
