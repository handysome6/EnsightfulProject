from cgi import test
import os
import sys
import cv2
import numpy as np
from tqdm import tqdm
from pathlib import Path

# from showimg import imshow
from model.camera_model import CameraModel
from calib.preprocess import Preprocess
from calib.calibration import Calibrate
from calib.rectification import StereoRectify
from measure.click_coord import ClickImage
from utils.utils import snap_subpix_corner

# load camera model
operation_folder = '0610_IMX477_infinity_still'
operation_folder = '0617_IMX477_5000'
cam_path = Path("datasets") / operation_folder / "calibration_data" / "camera_model.npz"
# cam_path = Path("datasets") / 'calibration_data' / "0617_IMX477_5000.npz"
camera = CameraModel.load_model(cam_path)

# rename, only once
def rename(test_folder):
    # renaming
    i = 0
    scenes_imgs = list(test_folder.iterdir())
    for file in scenes_imgs:
        i += 1
        if file.name[:7] == 'rectify':
            continue
        file.rename(test_folder / f"{str(i).zfill(2)}.jpg")


# pick image
try:
    id = sys.argv[1]
except:
    id = 7

test_folder = Path('datasets') / operation_folder / 'scenes' 
test_folder = Path('datasets') / operation_folder / 'test' 
assert test_folder.is_dir()
# rename(test_folder)
img_path = list(test_folder.iterdir())[int(id)-1]
print("Measuring", img_path.name)


# rectify image
sbs_img = cv2.imread(str(img_path))
# width = 4056
# imgL = sbs_img [:,     0:   width]
# imgR = sbs_img [:, width: 2*width]
# sbs_img = np.hstack([imgR, imgL])
rectifier = StereoRectify(camera, operation_folder)
imgL, imgR = rectifier.rectify_image(sbs_img)
imgL = cv2.cvtColor(imgL,cv2.COLOR_BGR2GRAY)
imgR = cv2.cvtColor(imgR,cv2.COLOR_BGR2GRAY)

# save
left_name  = f"rectify_{str(id).zfill(2)}_left.jpg"
right_name = f"rectify_{str(id).zfill(2)}_right.jpg"
# cv2.imwrite(str(test_folder / left_name), imgL)
# cv2.imwrite(str(test_folder / right_name), imgR)


# measure click
# predetermined intrinsic param
cameraMatrix = camera.cm1
Q = camera.Q
T = camera.T
f = cameraMatrix[0][0]
u0 = cameraMatrix[0][2]
v0 = cameraMatrix[1][2]
b = cv2.norm(T)

def findWorldCoord(img_coord_left, img_coord_right):
    x, y = img_coord_left
    d = img_coord_left[0] - img_coord_right[0]
    # print(x, y, d); exit(0)
    homg_coord = Q.dot(np.array([x, y, d, 1.0]))
    coord = homg_coord / homg_coord[3]
    print(coord[:-1])
    return coord[:-1]

# By epipolar geometry
def findWorldCoord2(img_coord_left, img_coord_right):
    u1, v1 = img_coord_left
    u2, v2 = img_coord_right
    x = u1 - u0
    y = v1 - v0
    disp = u1-u2
    world_z = b * f / disp
    world_x = world_z / f * x
    world_y = world_z / f * y
    return np.array([world_x, world_y, world_z])




left  = ClickImage(imgL, 'left')
right = ClickImage(imgR, 'right')
img_coord_left  = left.click_coord()
img_coord_right = right.click_coord()
assert img_coord_left is not None
assert img_coord_right is not None

snap_subpix_corner(imgL, img_coord_left)
snap_subpix_corner(imgR, img_coord_right)
# print(img_coord_left)
# print(img_coord_right)


coord1 = findWorldCoord(img_coord_left[0], img_coord_right[0])
coord2 = findWorldCoord(img_coord_left[1], img_coord_right[1])

print(cv2.norm(coord1, coord2))


# display corner
def draw_line_crop(img, point):
    line_thickness = 1
    point = (int(point[0]), int(point[1]))
    cv2.line(img, point, (point[0], 0), (0,0,0), thickness=line_thickness)
    cv2.line(img, point, (0, point[1]), (0,0,0), thickness=line_thickness)
    return \
        img[point[1]-50:point[1]+50,
            point[0]-50:point[0]+50,]
            
l1 = draw_line_crop(imgL, img_coord_left[0])
l2 = draw_line_crop(imgL, img_coord_left[1])
r1 = draw_line_crop(imgR, img_coord_right[0])
r2 = draw_line_crop(imgR, img_coord_right[1])
l = np.hstack([l1,r1])
r = np.hstack([l2,r2])
crop = np.vstack([l,r])
crop = cv2.resize(crop, [400, 400])
cv2.imshow('crop', crop)
key = cv2.waitKey(0)
if key == 27:
   cv2.destroyAllWindows()
