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
        # print(point1, point2)
        # print('world')
        world_coord1 = Ruler.get_world_coord_Q(Q, point1[0], point1[1])
        world_coord2 = Ruler.get_world_coord_Q(Q, point2[0], point2[1])
        # dx, dy, dz = world_coord2[0] - world_coord1[0], world_coord2[1] - world_coord1[1], world_coord2[2] - world_coord1[2]
        # print(world_coord1, world_coord2)
        # print(f"dx: {dx:.2f}mm, dy: {dy:.2f}mm, dz: {dz:.2f}mm,")
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
        if img_point_left[0] == () or img_point_left[1] == ():
            return 0        
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
        return 1

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

    def clickExit(self,event,x,y,flags,para):
        if event == cv2.EVENT_LBUTTONUP:
            self.click=1

    def show_result(self):
        point1, point2 = self.endpoints[-2:]
        world_coord1 = Ruler.get_world_coord_Q(self.Q, point1[0], point1[1])
        world_coord2 = Ruler.get_world_coord_Q(self.Q, point2[0], point2[1])
        point1 = point1[0].astype(np.int32)
        point2 = point2[0].astype(np.int32)
        height, width = self.left_img.shape[:2]
        line_thickness = 8
        show_img = self.left_img.copy()
        # show segment length
        cv2.line(show_img, point1, point2, (0,255,0), thickness=line_thickness)
        cv2.putText(show_img, f"Length of segment: {self.segment_len:.1f}mm",
            (20,150), cv2.FONT_HERSHEY_SIMPLEX, 5, (0,255,0), 10)
        # show different x, y z
        dx, dy, dz = world_coord2[0] - world_coord1[0], world_coord2[1] - world_coord1[1], world_coord2[2] - \
                     world_coord1[2]
        cv2.putText(show_img, f"dx: {dx:.2f}mm, dy: {dy:.2f}mm, dz: {dz:.2f}mm,",
                    (20, 300), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 255, 0), 8)
        # show point coordinates
        x1, y1, z1 = world_coord1[0].astype(np.float32), world_coord1[1].astype(np.float32), world_coord1[2].astype(
            np.float32)
        x2, y2, z2 = world_coord2[0].astype(np.float32), world_coord2[1].astype(np.float32), world_coord2[2].astype(
            np.float32)
        cv2.putText(show_img, f"point1: ({x1:.1f}, {y1:.1f}, {z1:.1f})", (20, 450), cv2.FONT_HERSHEY_SIMPLEX, 5,
                    (0, 255, 0), 8)
        cv2.putText(show_img, f"point2: ({x2:.1f}, {y2:.1f}, {z2:.1f})", (20, 600), cv2.FONT_HERSHEY_SIMPLEX, 5,
                    (0, 255, 0), 8)
        cv2.putText(show_img, '1', (point1[0], point1[1] + 80), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 12)
        cv2.putText(show_img, '2', (point2[0], point2[1] + 80), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 12)
        # show end_points
        point1, point2 = self.endpoints[-2:]
        point1_left = Ruler.draw_line_crop(self.left_img, point1[0])
        point1_right = Ruler.draw_line_crop(self.right_img, point1[1])
        point2_left = Ruler.draw_line_crop(self.left_img, point2[0])
        point2_right = Ruler.draw_line_crop(self.right_img, point2[1])
        p1 = cv2.resize(np.vstack([point1_left, point1_right]), [250, 500])
        p2 = cv2.resize(np.vstack([point2_left, point2_right]), [250, 500])
        show_img = cv2.resize(show_img, [500, 500])
        result = np.concatenate([p1, show_img, p2], axis=1)
        imshow('Image Result', result)



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
        # endpoints = cv2.resize(endpoints, [600, 600])

        imshow('First row: point 1;     Second row: point 2', endpoints)



    @staticmethod
    def draw_line_crop(img, point):
        """Draw a corss around the corner"""
        d = 100
        line_thickness = 3
        point = (int(point[0]), int(point[1]))
        cv2.line(img, point, (point[0], 0), (0,0,255), thickness=line_thickness)
        cv2.line(img, point, (0, point[1]), (0,0,255), thickness=line_thickness)
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

