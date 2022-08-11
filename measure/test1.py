import cv2
import numpy as np
from pathlib import Path
from utils.utils import imshow, snap_subpix_corner
from measure.find_match import AutoMatcher
from measure.click_coord import ClickImage
from measure.zoomin import cut

left_path = 'rectify_02_left.jpg'
right_path = 'rectify_02_right.jpg'
left = cv2.imread(str(left_path))
right = cv2.imread(str(right_path))

img1, min_x, min_y = cut(left)
# click to get raw coord
clicker = ClickImage(img1, 'left')
coords = clicker.click_coord()
# snap to corner
coords = snap_subpix_corner(left, coords)
coords = np.array(coords, dtype=np.int32)
point1 = (coords[0][0] + min_x, coords[0][1] + min_y)

img2, min_x, min_y = cut(left)
# click to get raw coord
clicker = ClickImage(img2, 'right')
coords = clicker.click_coord()
# snap to corner
coords = snap_subpix_corner(left, coords)
coords = np.array(coords, dtype=np.int32)
point2 = (coords[0][0] + min_x, coords[0][1] + min_y)

# auto match point
matcher = AutoMatcher(left, right)
matcher.match((point1,point2), True)
# matcher.user_choose(coords)
