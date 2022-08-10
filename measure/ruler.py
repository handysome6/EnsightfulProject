import cv2
import numpy as np
from measure.click_coord import ClickImage
from measure.matcher import AutoMatcher, MATCHER_TYPE
from utils.utils import snap_subpix_corner, imshow


class Ruler():
    def __init__(self, Q, left_img, right_img) -> None:
        """Measure segment length using stereo images.
        """
        self.Q = Q
        self.endpoints = []
        self.point1_left_coord  = []
        self.point1_right_coord = []
        self.point2_left_coord  = []
        self.point2_right_coord = []

        self.left_img = left_img
        self.right_img = right_img
        self.left_gray = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
        self.right_gray = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)


    def measure_segment(self):
        """Measure a segment length by clicking points"""
        Q = self.Q

        # click to get segment
        point1, point2 = self.endpoints[-2:]
        world_coord1 = Ruler.get_world_coord_Q(Q, point1[0], point1[1])
        world_coord2 = Ruler.get_world_coord_Q(Q, point2[0], point2[1])

        self.segment_len = cv2.norm(world_coord1, world_coord2)
        return self.segment_len


    def click_segment(self, automatch=True, matcher = MATCHER_TYPE.VGG):
        """Click to get the segment endpoints
        
        automatch: if this flag is set, compute the corresponding endpoints on right image.
        """
        # hand pick endpoints - LEFT
        window_str = ' - AutoMatch - ON' if automatch else ''
        left_clicker = ClickImage(self.left_img, 'Please click segment'+window_str)
        img_point_left  = left_clicker.click_coord()
        # snap to corner - LEFT
        img_point_left = snap_subpix_corner(self.left_gray, img_point_left)
        width = self.left_img.shape[1]
        if automatch:
            # auto match endpoints - RIGHT
            img_point_right = []
            matcher = AutoMatcher(self.left_img, self.right_img, matcher=matcher)
            # image = np.concatenate([self.left_img, self.right_img], axis=1)
            image = self.right_img.copy()
            for point in img_point_left:
                _, top_kps = matcher.match(point, show_result=False)
                img_point_right.append(top_kps[0].pt)
            assert len(img_point_right) == 2
            # point_ID = 1
            # for point in img_point_left:
            #     cv2.circle(image, (point[0].astype(int), point[1].astype(int)), 15, (0, 0, 255), -1)
            #     cv2.putText(image, f" {point_ID}", (point[0].astype(int), point[1].astype(int)), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 10, 0, 0)
            #     point_ID += 1
            user_clicker = ClickImage(image, 'Please reselected the point if needed')
            user_clicker.coords = img_point_right
            # for i in range(len(img_point_right)):
            #     img_point_right[i] = (img_point_right[i][0] + width, img_point_right[i][1])
            img_point_right = user_clicker.click_coord()
            # for i in range(len(img_point_right)):
            #     img_point_right[i] = (img_point_right[i][0] - width, img_point_right[i][1])
        else:
            # hand pick endpoints - RIGHT
            left_clicker = ClickImage(self.right_img, 'Please click segment - Second View')
            img_point_right = left_clicker.click_coord()

        # snap to corner - RIGHT
        img_point_right = snap_subpix_corner(self.right_gray, img_point_right)

        self.endpoints.append([img_point_left[0], img_point_right[0]])
        self.endpoints.append([img_point_left[1], img_point_right[1]])

######################### TODO #########################
    def get_segment_endpoints(self, matcher = MATCHER_TYPE.VGG):
        # hand pick endpoints - LEFT
        self.click_coord()
        # snap to corner - LEFT
        img_point_left = snap_subpix_corner(self.left_gray, img_point_left)



    def click_event(self, event, x, y, flags, param):
        """
        Event triggered when clcik on the image
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            # cv2.circle(self.img,(x,y),10,(255,0,0),-1)
            self.mouseX, self.mouseY = x,y

    def click_coord(self):
        """
        Pop up window.
        Click TWO points and return its coord.
        """
        window_name = "Left Image"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window_name, self.click_event)
        while(1):
            cv2.imshow(window_name, self.img)
            cv2.moveWindow(window_name, 0, 0)
            height, width = self.img.shape[:2]
            cv2.resizeWindow(window_name, int(width*1000/height), 1000)
            k = cv2.waitKey(20) & 0xFF
            if  (self.mouseX, self.mouseY)!=(0,0) and \
                (self.mouseX, self.mouseY) not in self.coords:
                # print((self.mouseX, self.mouseY))
                self.coords.append((self.mouseX, self.mouseY))
            cv2.destroyWindow(window_name)
            return self.coords
            if k == 27:
                break
            # elif k == ord('a'):
            #     print(self.mouseX, self.mouseY)



    def show_result(self):
        point1, point2 = self.endpoints[-2:]
        point1 = point1[0].astype(np.int32)
        point2 = point2[0].astype(np.int32)

        line_thickness = 8
        show_img = self.left_img.copy()
        cv2.line(show_img, point1, point2, (0,255,0), thickness=line_thickness)
        cv2.putText(show_img, f"Length of segment: {self.segment_len:.2f}mm",
            (0,100), cv2.FONT_HERSHEY_SIMPLEX, 3, (0,255,0), 3)

        imshow('Image Result', show_img)




    def show_endpoints(self):
        """Show selected endpoints"""
        point1, point2 = self.endpoints[-2:]

        point1_left = Ruler.draw_line_crop(self.left_img, point1[0])
        point1_right = Ruler.draw_line_crop(self.right_img, point1[1])
        point2_left = Ruler.draw_line_crop(self.left_img, point2[0])
        point2_right = Ruler.draw_line_crop(self.right_img, point2[1])
        p1 = np.hstack([point1_left, point1_right])
        p2 = np.hstack([point2_left, point2_right])
        endpoints = np.vstack([p1, p2])
        endpoints = cv2.resize(endpoints, [600, 600])

        imshow('First row: point 1;     Second row: point 2', endpoints)



    @staticmethod
    def draw_line_crop(img, point):
        """Draw a corss around the corner"""
        d = 100
        line_thickness = 1
        point = (int(point[0]), int(point[1]))
        cv2.line(img, point, (point[0], 0), (0,0,0), thickness=line_thickness)
        cv2.line(img, point, (0, point[1]), (0,0,0), thickness=line_thickness)
        return \
            img[point[1]-d:point[1]+d,
                point[0]-d:point[0]+d,]


    @staticmethod
    def get_world_coord_Q(Q, img_coord_left, img_coord_right):
        """Compute world coordniate by the Q matrix
        
        img_coord_left:  segment endpoint coordinate on the  left image
        img_coord_right: segment endpoint coordinate on the right image
        """
        x, y = img_coord_left
        d = img_coord_left[0] - img_coord_right[0]
        # print(x, y, d); exit(0)
        homg_coord = Q.dot(np.array([x, y, d, 1.0]))
        coord = homg_coord / homg_coord[3]
        # print(coord[:-1])
        return coord[:-1]

