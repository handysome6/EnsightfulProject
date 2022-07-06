import enum
import cv2
import numpy as np
from enum import Enum
from pathlib import Path
from utils.utils import imshow, snap_subpix_corner


class MATCHER_TYPE(Enum):
    """
    Descriptor Extractor Types
    Ranking: VGG 
    > FREAK / BRIEF 
    > DAISY 
    > SIFT / LATCH / BOOST 
    >> SURF > LUCID
    """
    SIFT = 1
    # SURF = 10
    BRIEF = 2
    LUCID = 3
    LATCH = 4
    DAISY = 5
    BOOST = 6
    VGG = 7
    BRISK = 8
    FREAK = 9


class AutoMatcher():
    def __init__(self, left_img, right_img, matcher = MATCHER_TYPE.VGG) -> None:
        """
        Using SIFT features to match
        left_img
        """
        self.left_img = left_img
        self.right_img = right_img
        self.block_y = 3
        self.max_disp = 600
        self.min_disp = 50
        self.matcher = matcher
        
        if matcher == MATCHER_TYPE.SIFT:
            self.point_discriptor = cv2.SIFT_create()
        elif matcher == MATCHER_TYPE.BRIEF:
            self.point_discriptor = cv2.xfeatures2d.BriefDescriptorExtractor_create(bytes=64)
        elif matcher == MATCHER_TYPE.LUCID:
            self.point_discriptor = cv2.xfeatures2d.LUCID_create()
        elif matcher == MATCHER_TYPE.LATCH:
            self.point_discriptor = cv2.xfeatures2d.LATCH_create(bytes=32, rotationInvariance=False)
        elif matcher == MATCHER_TYPE.DAISY:
            self.point_discriptor = cv2.xfeatures2d.DAISY_create(radius=30, use_orientation = False)
        elif matcher == MATCHER_TYPE.BOOST:
            self.point_discriptor = cv2.xfeatures2d.BoostDesc_create(use_scale_orientation=False, scale_factor=40.)
        elif matcher == MATCHER_TYPE.VGG:
            self.point_discriptor = cv2.xfeatures2d.VGG_create(use_scale_orientation=False, scale_factor=25.)
        elif matcher == MATCHER_TYPE.BRISK:
            self.point_discriptor = cv2.BRISK_create()
        elif matcher == MATCHER_TYPE.FREAK:
            self.point_discriptor = cv2.xfeatures2d.FREAK_create(orientationNormalized=False)


    def match(self, point, show_result=False):
        """
        Find matching point in another image
        point: single reference point coord in left image. 
               accepted shape: (2,) (1,2)
        """
        print("Finding matching point...")
        # convert point to list, as required by cv2 functions
        if len(point.shape) == 1:
            point = np.expand_dims(point, axis=0)
            assert len(point.shape) == 2

        # compute reference LEFT
        ref_keypoints = cv2.KeyPoint.convert(np.array(point, dtype=np.float32))
        ref_keypoints, ref_descriptors = self.point_discriptor.compute(self.left_img, ref_keypoints)
        # convert type to int
        point = np.array(point, dtype=np.int32)
        # compute candidates RIGHT
        candidates = self._get_correspond_candidates(point[0])
        corr_keypoints, corr_descriptors = self.point_discriptor.compute(self.right_img, candidates)

        # select point feature
        feature = ref_descriptors[0]
        # compare with corr features
        distances = []
        # print(len(feature))
        for corr_f in corr_descriptors:
            distances.append(cv2.norm(feature, corr_f, cv2.NORM_L1))

        # find nearest feature
        distances = np.array(distances)
        ind = np.argpartition(distances, 10)[:10]
        top_keypoints = []
        for i in ind:
            dist = distances[i]
            # print(dist, corr_keypoints[i].pt)
            kp = corr_keypoints[i]
            kp.size = self.kp_size(dist)
            # print(kp.size)
            top_keypoints.append(kp)
        top_keypoints = np.array(top_keypoints)

        if show_result:
            # Search region - Green
            show_fig = cv2.drawKeypoints(self.right_img, corr_keypoints, None, color = (0, 255, 0))
            # Top keypoionts - Red
            show_fig = cv2.drawKeypoints(show_fig, top_keypoints, None, color = (0, 0, 255), 
                flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
            imshow("Matching result", show_fig)
        return corr_keypoints, top_keypoints


    def kp_size(self, dist):
        if self.matcher == MATCHER_TYPE.SIFT:
            return 140000 / (dist+0.01)
        elif self.matcher == MATCHER_TYPE.BRIEF:
            return 280000 / (dist+0.01)
        elif self.matcher == MATCHER_TYPE.DAISY:
            return 70 / (dist+0.01)
        elif self.matcher == MATCHER_TYPE.VGG:
            return 1400 / (dist+0.01)
        elif self.matcher == MATCHER_TYPE.FREAK:
            return 280000 / (dist+0.01)
        
        return 140000 / (dist+0.01)


    def _get_correspond_candidates(self, point):
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
            for j in range(max(coord_x-self.max_disp, 0), coord_x-self.min_disp+1):
                pts.append(np.array([j, i]) )
        pts = np.array(pts, dtype=np.float32)
        keypoints = cv2.KeyPoint.convert(pts)
        # print("Got coorespond region for ", point)
        return keypoints


if __name__ == '__main__':
    import cv2
    import numpy as np
    from pathlib import Path
    from utils.utils import imshow, snap_subpix_corner
    from measure.matcher import AutoMatcher
    from measure.click_coord import ClickImage

    img_folder = Path('datasets') / '0617_IMX477_5000' / 'test'
    left_path  = img_folder / 'rectify_02_left.jpg'
    right_path = img_folder / 'rectify_02_right.jpg'
    left = cv2.cvtColor(cv2.imread(str(left_path)), cv2.COLOR_BGR2GRAY)
    right = cv2.cvtColor(cv2.imread(str(right_path)), cv2.COLOR_BGR2GRAY)
    # left = cv2.imread(str(left_path))
    # right = cv2.imread(str(right_path))


    # click to get raw coord
    # clicker = ClickImage(left, 'left')
    # coords = clicker.click_coord()
    # coords = snap_subpix_corner(left, coords)
    # coords = np.array(coords, dtype=np.int32)
    # print(coords)


    type1 = np.array([
    # no change in bg
        [2874.6624, 1297.6266], # paper corner
        [2260.2034, 1445.7456], # chessboard 6col, 2row corner
        [2140.5256, 1603.4136], # chessbaord 3col, 6row corner
        [2241.0977, 2342.463 ], # x shape up corner
        [ 497.4322, 1466.2269], # water dispenser top right corner

    # change in bg
        [872.34766, 1929.6948], # table botm left corner
        [ 3639.962, 1776.7246], # table top right corner

    # edge
        [ 3033.456, 2353.8894], # table leg right edge
        [2428.5632, 2452.3262], # x shape right corner
        [ 3631.404, 1914.6367], # table botm right corner
    ])
    type2 = np.array([
        [ 497.4322, 1466.2269], # water dispenser top right corner
    ])



    regions = []
    kps = []
    # auto match point
    matcher = AutoMatcher(left, right)
    for coord in type1:
        region, top_kps = matcher.match(coord, show_result=True)
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
    # cv2.imwrite('datasets/VGG.jpg', show_fig)
    imshow("Matching result", show_fig)
