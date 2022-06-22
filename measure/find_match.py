import cv2
import numpy as np
from pathlib import Path
from utils.utils import imshow, snap_subpix_corner
from measure.click_coord import ClickImage

class AutoMatcher():
    def __init__(self, left_img, right_img) -> None:
        """
        Using SIFT features to match
        """
        self.point_discriptor = cv2.SIFT_create()
        self.block_y = 3
        self.max_disp = 800
        self.min_disp = 50

        self.left_img = left_img
        self.right_img = right_img


    def match(self, point, show_region=False):
        """
        Find matching point in another image
        point: single reference point coord in left image. 
               accepted shape: (2,) (1,2)
        """
        # convert type to int
        point = np.array(point, dtype=np.int32)
        # convert point to list, as required by cv2 functions
        if len(point.shape) == 1:
            point = np.expand_dims(point, axis=0)
            assert len(point.shape) == 2

        # compute reference LEFT
        ref_keypoints = cv2.KeyPoint.convert(np.array(point, dtype=np.float32))
        ref_keypoints, ref_descriptors = self.point_discriptor.compute(self.left_img, ref_keypoints)
        # compute candidates RIGHT
        candidates = self.get_correspond_candidates(point[0])
        corr_keypoints, corr_descriptors = self.point_discriptor.compute(self.right_img, candidates)

        # select point feature
        feature = ref_descriptors[0]
        # compare with corr features
        distances = []
        for corr_f in corr_descriptors:
            distances.append(cv2.norm(feature, corr_f))

        # find nearest feature
        distances = np.array(distances)
        ind = np.argpartition(distances, 10)[:10]
        top_keypoints = []
        for i in ind:
            dist = distances[i]
            print(dist)
            kp = corr_keypoints[i]
            kp.size = 30000 / dist
            top_keypoints.append(kp)

        if show_region:
            show_fig = cv2.drawKeypoints(self.right_img, corr_keypoints, None, color = (0, 255, 0))
            red_point = np.array(top_keypoints)
            show_fig = cv2.drawKeypoints(show_fig, red_point, None, color = (0, 0, 255), 
                flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
            imshow("Matching result", show_fig)
        return top_keypoints


    def get_correspond_candidates(self, point):
        """
        Input points, get candidates keypoints region in right image
        point: left image corner coord.
               accepted shape: (2,) (1,2)
        """
        # remove empty axis 
        point = np.squeeze(point)
        
        coord_x, coord_y = point
        half = self.block_y // 2
        pts = []
        # iterate through the region
        for i in range(coord_y-half, coord_y+half+1):
            for j in range(coord_x-self.max_disp, coord_x-self.min_disp+1):
                pts.append(np.array([j, i]) )
        pts = np.array(pts, dtype=np.float32)
        keypoints = cv2.KeyPoint.convert(pts)
        # print("Got coorespond region for ", point)
        return keypoints



if __name__ == '__main__':
    # load image pair
    img_folder = Path('datasets') / '0617_IMX477_5000' / 'rectified'
    left_path = img_folder / 'rectify_01_left.jpg'
    right_path = img_folder / 'rectify_01_right.jpg'
    left = cv2.cvtColor(cv2.imread(str(left_path)), cv2.COLOR_BGR2GRAY)
    right = cv2.cvtColor(cv2.imread(str(right_path)), cv2.COLOR_BGR2GRAY)
    
    # click to get raw coord
    clicker = ClickImage(left, 'left')
    coords = clicker.click_coord()

    # snap to corner - TODO
    coords = snap_subpix_corner(left, coords)
    coords = np.array(coords, dtype=np.int32)
    print(coords)

    matcher = AutoMatcher(left, right)
    matcher.match(coords[0], show_region=True)
    matcher.match(coords[1], show_region=True)

