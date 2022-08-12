import numpy as np
import cv2
import os
from statistics import mean, stdev
from tqdm.auto import tqdm
from calib.rectification import StereoRectify

def findWorldCoord(img_coord_left, img_coord_right):
    u1, v1 = img_coord_left[0]
    u2, v2 = img_coord_right[0]
    x = u1 - u0
    y = v1 - v0
    disp = u1-u2
    world_z = b * f / disp
    world_x = world_z / f * x
    world_y = world_z / f * y
    return np.array([world_x, world_y, world_z])


rows = 8
columns = 11
CHECKERBOARD = (rows,columns)
subpix_criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)


for id in (range(10)):
    image_id = str(id+1).zfill(2)
    leftName = f'rectify_fisheye/rectify_{image_id}_left.jpg'
    rightName = f'rectify_fisheye/rectify_{image_id}_right.jpg'
    imgL = cv2.imread(leftName,1)
    grayL = cv2.cvtColor(imgL,cv2.COLOR_BGR2GRAY)
    imgR = cv2.imread(rightName,1)
    grayR = cv2.cvtColor(imgR,cv2.COLOR_BGR2GRAY)

    # Find the chessboard corners
    retL, cornersL = cv2.findChessboardCorners(grayL, CHECKERBOARD, None)
    retR, cornersR = cv2.findChessboardCorners(grayR, CHECKERBOARD, None)
    if ((retL == True) and (retR == True)):
        cv2.cornerSubPix(grayL,cornersL,(11,11),(-1,-1),subpix_criteria)
        cv2.cornerSubPix(grayR,cornersR,(11,11),(-1,-1),subpix_criteria)
    
    # find the 
    edges = []
    for i in range(7):
        # select two points
        point_id_1 = i
        point_id_2 = i+1

        img_coord_1 = [cornersL[point_id_1], cornersR[point_id_1]]
        img_coord_2 = [cornersL[point_id_2], cornersR[point_id_2]]


        coord1 = findWorldCoord(*img_coord_1)
        coord2 = findWorldCoord(*img_coord_2)

        distance = cv2.norm(coord1, coord2)
        if distance < 100:
            edges.append(distance)
    print(f"Pair {image_id}, Mean edge len: {mean(edges)}")
    
# print(f'''
# Over all performance:
# Max: {max(edges)}; Min: {min(edges)}
# Mean: {mean(edges)}; Stdev: {stdev(edges)}
# ''')


class Evaluation():
    def __init__(self, rectifier: StereoRectify, CHECKERBOARD) -> None:
        self.rectifier = rectifier
        self.CHECKERBOARD = CHECKERBOARD

    def evaluate_folder(self, folder):
        for sbs_path in folder.iterdir():
            sbs_img = cv2.imread(str(sbs_path))
            self.rectifier.rectify_image(sbs_img=sbs_img)
