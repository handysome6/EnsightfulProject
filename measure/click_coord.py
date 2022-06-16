import cv2
import numpy as np

class ClickImage():
    def __init__(self, img, windowName) -> None:
        self.mouseX = 0
        self.mouseY = 0
        self.coords = []
        self.img = img
        self.windowName = windowName
    
    def click_event(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # cv2.circle(self.img,(x,y),10,(255,0,0),-1)
            self.mouseX, self.mouseY = x,y
    
    def click_coord(self):
        cv2.namedWindow(self.windowName, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(self.windowName, self.click_event)
        while(1):
            cv2.imshow(self.windowName, self.img)
            cv2.moveWindow(self.windowName, 0, 0)
            height, width = self.img.shape[:2]
            cv2.resizeWindow(self.windowName, int(width*1000/height), 1000)
            k = cv2.waitKey(20) & 0xFF
            if  (self.mouseX, self.mouseY)!=(0,0) and \
                (self.mouseX, self.mouseY) not in self.coords:
                # print((self.mouseX, self.mouseY))
                self.coords.append((self.mouseX, self.mouseY))
            if len(self.coords) == 2:
                import time
                # time.sleep(1)
                cv2.destroyWindow(self.windowName)
                return np.array(self.coords, dtype=np.float32)
            if k == 27:
                break
            # elif k == ord('a'):
            #     print(self.mouseX, self.mouseY)


if __name__ == '__main__':
    # import os
    # os.chdir
    path = "../0607_fisheye_near+far/rectify_fisheye/rectify_19_left.jpg"
    img = cv2.imread(path)
    obj = ClickImage(img, 'left')
    img_coord_left = obj.click_coord()

    def draw_line_crop(img, point):
        line_thickness = 2
        point = (int(point[0]), int(point[1]))
        print(point)
        cv2.line(img, point, (point[0], 0), (0,255,0), thickness=line_thickness)
        cv2.line(img, point, (0, point[1]), (0,255,0), thickness=line_thickness)
        return \
            img[point[1]-150:point[1]+150,
                point[0]-150:point[0]+150,]
    
    cv2.imshow('l1', draw_line_crop(img, img_coord_left[0]))
    # cv2.imshow('img', img)
    cv2.waitKey(5000)
