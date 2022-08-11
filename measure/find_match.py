import cv2
import numpy as np
from pathlib import Path
from utils.utils import imshow, snap_subpix_corner
from measure.click_coord import ClickImage
from measure.resize import showing,showimg
from measure.zoomin import cut

class AutoMatcher():
    def __init__(self, left_img, right_img) -> None:
        """
        Using SIFT features to match
        """
        # self.alg = input("Choose an algorithm (sift, orb, brisk, freak): ")
        self.block_y = 3
        self.max_disp = 800
        self.min_disp = 50
        self.norm = cv2.NORM_L2
        self.leftBGR = left_img
        self.rightBGR = right_img
        self.left_img = cv2.cvtColor(self.leftBGR, cv2.COLOR_BGR2GRAY)
        self.right_img = cv2.cvtColor(self.rightBGR, cv2.COLOR_BGR2GRAY)
        # if self.alg == 'sift':
        #     self.point_discriptor = cv2.SIFT_create()
        #     dis = input("Choose an algorithm: L1 or L2: ")
        #     if dis == 'L1':
        #         self.norm = cv2.NORM_L1
        #     elif dis == 'L2':
        #         self.norm = cv2.NORM_L2
        # # elif alg == 'surf':
        # #     self.point_discriptor = cv2.xfeatures2d.SURF_create(800)
        # #     self.norm = cv2.NORM_L2
        # elif self.alg == 'orb':
        #     self.point_discriptor = cv2.ORB_create(400)
        #     self.norm = cv2.NORM_HAMMING
        # elif self.alg == 'freak':
        #     self.point_discriptor = cv2.xfeatures2d.FREAK_create()
        #     self.norm = cv2.NORM_HAMMING
        # elif self.alg == 'brisk':
        #     self.point_discriptor = cv2.BRISK_create()
        #     self.norm = cv2.NORM_HAMMING
        self.point_discriptor = cv2.xfeatures2d.FREAK_create()
        self.norm = cv2.NORM_HAMMING

    def user_choose(self, points):
        # cor = input("Is the matching correct? (input no to reselect) : ")
        cor = 'no'
        if cor == 'no':
            image = np.concatenate([self.leftBGR, self.rightBGR], axis=1)
            for i in range(2):
                point = points[i]
                point = np.array(point, dtype=np.int32)
                cv2.circle(image, point, 15, (0,0,255), -1)
            # imshow("Choose points", image)
            clicker = ClickImage(image, 'Please choose the corresponding points on the right image')
            coords = clicker.click_coord()
            # snap to corner
            coords = snap_subpix_corner(image, coords)
            coords = np.array(coords, dtype=np.int32)
            for i in range(2):
                match = coords[i]
                match = np.array(match, dtype=np.int32)
                point = points[i]
                point = np.array(point, dtype=np.int32)
                cv2.line(image, point, match, color=(255, 0, 0), thickness=10)
            imshow("Choose points", image)

    def match(self, points, show_result=False):
        """
        Find matching point in another image
        point: single reference point coord in left image.
               accepted shape: (2,) (1,2)
        """
        # convert type to int
        image = np.concatenate([self.leftBGR, self.rightBGR], axis=1)
        image1 = image.copy()

        width = self.left_img.shape[1]
        for i in range(2):
            point = points[i]
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
                distances.append(cv2.norm(feature, corr_f,self.norm))

            # find nearest feature
            distances = np.array(distances)
            ind = np.argpartition(distances, 1)[:1]
            top_keypoints = []

            for j in ind:
                dist = distances[j]
                print('distance between points ',dist)
                kp = corr_keypoints[j]
                kp.size = 30000 / dist
                top_keypoints.append(kp)
            top_keypoints = np.array(top_keypoints)

            if show_result:
                if i == 0:
                    x2 = top_keypoints[0].pt[0]
                    y2 = top_keypoints[0].pt[1]
                    match_point = (int(x2+width),int(y2))
                    # print(match_point)
                    # print(point)
                    cv2.line(image, point[0],match_point, color=(255, 0, 0), thickness=10)

                    clicker = ClickImage(image, 'keep clicking the right image to reselect the point, click the left image if no need')
                    coords = clicker.click_coord()
                    # snap to corner
                    coords = snap_subpix_corner(image, coords)
                    coords = np.array(coords, dtype=np.int32)

                    match = coords[0]
                    match = np.array(match, dtype=np.int32)

                    if match[0] > 4056:
                        cv2.circle(image1, point[0], 15, (0, 0, 255), -1)
                        point1 = cut(image1)
                        cv2.line(image1, point[0], point1, color=(0, 0, 255), thickness=10)
                        cv2.destroyAllWindows()
                        # img1, min_x, min_y, zoom = cut(image1)
                        # if zoom == 1:
                        #     clicker = ClickImage(img1, 'Click the image to select match point1')
                        #     coords = clicker.click_coord()
                        #     # snap to corner
                        #     coords = snap_subpix_corner(img1, coords)
                        #     coords = np.array(coords, dtype=np.int32)
                        #     point1 = (coords[0][0] + min_x, coords[0][1] + min_y)
                        #     cv2.line(image1, point[0], point1, color=(0, 0, 255), thickness=10)
                        #     cv2.destroyAllWindows()
                        # else:
                        #     point1 = (min_x, min_y)
                        #     cv2.line(image1, point[0], point1, color=(0, 0, 255), thickness=10)
                        #     cv2.destroyAllWindows()

                    else:
                        image1 = image.copy()
                if i == 1:
                    x2 = top_keypoints[0].pt[0]
                    y2 = top_keypoints[0].pt[1]
                    match_point = (int(x2 + width), int(y2))
                    # print(match_point)
                    # print(point)
                    image2 = image1.copy()
                    cv2.line(image1, point[0], match_point, color=(255, 0, 0), thickness=10)

                    clicker = ClickImage(image1, 'keep clicking the right image to reselect the point, click the left image if no need')
                    coords = clicker.click_coord()
                    # snap to corner
                    coords = snap_subpix_corner(image, coords)
                    coords = np.array(coords, dtype=np.int32)

                    match = coords[0]
                    match = np.array(match, dtype=np.int32)

                    if match[0] > 4056:
                        cv2.circle(image2, point[0], 15, (0, 0, 255), -1)
                        point2 = cut(image2)
                        cv2.line(image2, point[0], point2, color=(0, 0, 255), thickness=10)
                        cv2.destroyAllWindows()
                        # img1, min_x, min_y, zoom = cut(image2)
                        # if zoom == 1:
                        #     clicker = ClickImage(img1, 'Click the image to select match point2')
                        #     coords = clicker.click_coord()
                        #     # snap to corner
                        #     coords = snap_subpix_corner(img1, coords)
                        #     coords = np.array(coords, dtype=np.int32)
                        #     point2 = (coords[0][0] + min_x, coords[0][1] + min_y)
                        #     cv2.line(image2, point[0], point2, color=(0, 0, 255), thickness=10)
                        #     cv2.destroyAllWindows()
                        # else:
                        #     point2 = (min_x, min_y)
                        #     cv2.line(image2, point[0], point2, color=(0, 0, 255), thickness=10)
                        #     cv2.destroyAllWindows()

                    else:
                        image2 = image1.copy()
                    imshow('final matching result', image2)
                    # a = showimg([1000,400],image2)
                    # showimg.show(a)
                    # showing([1000,400],image2)


                # # Search region - Green
                # show_fig = cv2.drawKeypoints(self.right_img, corr_keypoints, None, color=(0, 255, 0))
                # # Top keypoionts - Red
                # show_fig = cv2.drawKeypoints(show_fig, top_keypoints, None, color=(0, 0, 255),
                #                              flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
                # imshow("Matching result", show_fig)
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
        for i in range(coord_y - half, coord_y + half + 1):
            for j in range(coord_x - self.max_disp, coord_x - self.min_disp + 1):
                pts.append(np.array([j, i]))
        pts = np.array(pts, dtype=np.float32)
        keypoints = cv2.KeyPoint.convert(pts)
        print("Got coorespond region for ", point)
        return keypoints


if __name__ == '__main__':
    # load image pair
    left_path = 'rectify_02_left.jpg'
    right_path = 'rectify_02_right.jpg'
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
    matcher.match(coords, True)
    # matcher.match(coords[0], show_region=True)
    # matcher.match(coords[1], show_region=True)

