import cv2
import numpy as np

class ClickImage():
    """
    Click image to get coord
    """
    def __init__(self, img, windowName) -> None:
        """
        img: image object read by cv2.imread
        windowName: pop up window name
        """
        self.mouseX = 0
        self.mouseY = 0
        self.init_x = 0
        self.init_y = 0
        self.init_drag_x = 0
        self.init_drag_y = 0
        self.coords = [(), ()]
        self.img = img
        self.flag = 0  # 1为单击后选点模式，0为大图显示模式
        self.show_big_img = 0
        self.windowName = windowName
    
    def click_event(self, event, x, y, flags, param):
        """
        Event triggered when click on the image
        """
        if self.flag == 0:
            self.showImg = self.img.copy()
            cv2.namedWindow(self.windowName, cv2.WINDOW_NORMAL)
            height, width = self.img.shape[:2]
            cv2.resizeWindow(self.windowName, int(width * 500 / height), 500)
            if self.coords[0] != ():
                cv2.circle(self.showImg, np.array(self.coords[0], dtype=np.int32), 15, (0, 0, 255), -1)
                cv2.putText(self.showImg, f" {1}", np.array(self.coords[0], dtype=np.int32),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 10, 0, 0)
            if self.coords[1] != ():
                cv2.circle(self.showImg, np.array(self.coords[1], dtype=np.int32), 15, (0, 0, 255), -1)
                cv2.putText(self.showImg, f" {2}", np.array(self.coords[1], dtype=np.int32),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 10, 0, 0)
            cv2.imshow(self.windowName, self.showImg)

        if event == cv2.EVENT_LBUTTONDOWN:
            if self.flag == 0:
                self.init_x, self.init_y = x, y
            if self.flag == 1:
                self.init_drag_x, self.init_drag_y = x, y


        if event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):
            self.flag = 1
            self.show_big_img = 0
            height, width = self.img.shape[:2]
            # ori_x, ori_y = x, y
            # scale = 25
            scale = max(cv2.getTrackbarPos('scale', self.windowName),1)
            # x = int(self.init_x - (x - self.init_x) / scale)
            # y = int(self.init_y - (y - self.init_y) / scale)
            x = int(self.init_x - (x - self.init_drag_x) / scale)
            y = int(self.init_y - (y - self.init_drag_y) / scale)
            x = max(1, min(x, width))
            y = max(1, min(y, height))
            # self.showImg = self.img.copy()
            # 固定选择区域大小 160*120
            # self.cut_img = self.img.copy()[max(0, y - 60): min(y + 60, height), max(x - 80, 0):min(x + 80, width)]
            x_range, y_range = int(width/scale/2), int(height/scale/2)
            x, y = min(max(x_range, x), width - x_range), min(max(y_range, y), height - y_range)
            # self.cut_img = self.img.copy()[max(0, y - y_range): min(y + y_range, height),
            #                max(x - x_range, 0):min(x + x_range, width)]
            self.cut_img = self.img.copy()[y - y_range: y + y_range, x - x_range:x + x_range]
            point_ID = cv2.getTrackbarPos('pick point', self.windowName)
            self.cut_img = cv2.resize(self.cut_img, (width, height))
            cv2.line(self.cut_img, (int(width / 2), 0), (int(width / 2), height), (0, 0, 255), 10, 1)  # 画面中间画竖线
            cv2.line(self.cut_img, (0, int(height / 2)), (width, int(height / 2)), (0, 0, 255), 10, 1)  # 画面中间画横线
            cv2.putText(self.cut_img, f"point {point_ID + 1}",
                        (int(width * 0.55), int(height * 0.45)),
                        cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 10, 0, 0)
            self.showImg = self.cut_img
            # cv2.circle(self.showImg, (x,y), 10, (0, 255, 255), -1)
            cv2.namedWindow(self.windowName, cv2.WINDOW_NORMAL)
            height, width = self.img.shape[:2]
            cv2.resizeWindow(self.windowName, int(width * 500 / height), 500)
            cv2.imshow(self.windowName, self.showImg)
        if event == cv2.EVENT_LBUTTONUP:
            if self.flag == 0:  # 如果当前没有在选点，进入选点模式
                self.show_big_img = 1
                self.flag = 1

            else:
                # scale = max(cv2.getTrackbarPos('scale', self.windowName),1)
                if self.show_big_img == 1:  # 如果单击后不拖拽直接再次单点，返回大图继续选点
                    self.show_big_img = 0
                self.flag = 0
                scale = max(cv2.getTrackbarPos('scale', self.windowName),1)
                # 计算真实坐标
                height, width = self.img.shape[:2]
                x_range, y_range = int(width / scale / 2), int(height / scale / 2)
                # self.mouseX, self.mouseY = int(self.init_x - (x - self.init_x) / scale), int(self.init_y - (y - self.init_y) / scale)
                self.mouseX, self.mouseY = int(self.init_x - (x - self.init_drag_x) / scale), int(
                    self.init_y - (y - self.init_drag_y) / scale)
                self.mouseX, self.mouseY = min(max(x_range, self.mouseX), width - x_range), min(max(y_range, self.mouseY), height - y_range)
                # self.mouseX, self.mouseY = max(1, min(self.mouseX, width)), max(1, min(self.mouseY, height))
                point_ID = cv2.getTrackbarPos('pick point', self.windowName)
                if (self.mouseX, self.mouseY) != (0, 0) and \
                            (self.mouseX, self.mouseY) not in self.coords:
                    # if self.mouseX > width/30:
                    if point_ID == 0:
                        self.coords[0] = (self.mouseX, self.mouseY)
                    elif point_ID == 1:
                        self.coords[1] = (self.mouseX, self.mouseY)

                    # else:
                    #     print("The point is too close to the boundary, please select again!")
                self.showImg = self.img.copy()
                cv2.namedWindow(self.windowName, cv2.WINDOW_NORMAL)
                height, width = self.img.shape[:2]
                cv2.resizeWindow(self.windowName, int(width * 500 / height), 500)
                if self.coords[0] != ():
                    cv2.circle(self.showImg, np.array(self.coords[0], dtype=np.int32), 15, (0, 0, 255), -1)
                    cv2.putText(self.showImg, f" {1}", np.array(self.coords[0], dtype=np.int32),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 10, 0, 0)

                if self.coords[1] != ():
                    cv2.circle(self.showImg, np.array(self.coords[1], dtype=np.int32), 15, (0, 0, 255), -1)
                    cv2.putText(self.showImg, f" {2}", np.array(self.coords[1], dtype=np.int32),
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 10, 0, 0)
                cv2.imshow(self.windowName, self.showImg)

    def click_coord(self, num=2):
        """
        Pop up window.
        Click TWO points and return its coord.
        """
        self.showImg = self.img.copy()
        cv2.namedWindow(self.windowName, cv2.WINDOW_NORMAL)
        height, width = self.img.shape[:2]
        cv2.resizeWindow(self.windowName, int(width*500/height), 500)       
        cv2.createTrackbar('scale', self.windowName, 16, 50, self.nothing)
        cv2.createTrackbar('pick point', self.windowName, 0, 2, self.point_ID)
        # cv2.createTrackbar('finish', self.windowName, 0, 1, self.nothing)
        cv2.setMouseCallback(self.windowName, self.click_event)
        while(1):
            # if self.coords[0] != ():
            #     cv2.circle(self.showImg, np.array(self.coords[0], dtype=np.int32), 15, (0, 0, 255), -1)
            #     cv2.putText(self.showImg, f" { 1}", np.array(self.coords[0], dtype=np.int32),
            #                 cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 10, 0, 0)
            # if self.coords[1] != ():
            #     cv2.circle(self.showImg, np.array(self.coords[1], dtype=np.int32), 15, (0, 0, 255), -1)
            #     cv2.putText(self.showImg, f" { 2}", np.array(self.coords[1], dtype=np.int32),
            #                 cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 10, 0, 0)
            cv2.imshow(self.windowName, self.showImg)
            k = cv2.waitKey(20) & 0xFF
            # finish = cv2.getTrackbarPos('finish', self.windowName)
            if self.show_big_img == 1:
                x, y = self.init_x, self.init_y
                height, width = self.img.shape[:2]
                # scale = 25
                scale = max(cv2.getTrackbarPos('scale', self.windowName), 1)
                # self.cut_img = self.img.copy()[max(0, y - 60): min(y + 60, height), max(x - 80, 0):min(x + 80, width)]
                x_range, y_range = int(width / scale / 2), int(height / scale / 2)
                x, y = min(max(x_range, x), width - x_range), min(max(y_range, y), height - y_range)
                # self.cut_img = self.img.copy()[max(0, y - y_range): min(y + y_range, height),
                #                max(x - x_range, 0):min(x + x_range, width)]
                self.cut_img = self.img.copy()[y - y_range: y + y_range, x - x_range:x + x_range]

                point_ID = cv2.getTrackbarPos('pick point', self.windowName)
                # cv2.line(self.cut_img, (80, 0), (80, 120), (0, 0, 255), 1, 1)
                # cv2.line(self.cut_img, (0, 60), (160, 60), (0, 0, 255), 1, 1)
                # cv2.line(self.cut_img, (x_range, 0), (x_range, y_range * 2), (0, 0, 255), 1, 1)  # 画面中间画竖线
                # cv2.line(self.cut_img, (0, y_range), (x_range * 2, y_range), (0, 0, 255), 1, 1)  # 画面中间画横线
                # cv2.putText(self.cut_img, f"point {point_ID + 1}",
                #             (int(width / 2 + x_range * 0.6), int(height / 2 - y_range * 0.8)),
                #             cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 10, 0, 0)
                self.cut_img = cv2.resize(self.cut_img, (width, height))
                cv2.line(self.cut_img, (int(width/2), 0), (int(width/2), height), (0, 0, 255), 10, 1)  # 画面中间画竖线
                cv2.line(self.cut_img, (0, int(height/2)), (width, int(height/2)), (0, 0, 255), 10, 1)  # 画面中间画横线
                cv2.putText(self.cut_img, f"point {point_ID + 1}",
                            (int(width*0.55), int(height*0.45)),
                            cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 10, 0, 0)
                self.showImg = self.cut_img
                # cv2.circle(self.showImg, (x,y), 10, (0, 255, 255), -1)
                cv2.namedWindow(self.windowName, cv2.WINDOW_NORMAL)
                height, width = self.img.shape[:2]
                cv2.resizeWindow(self.windowName, int(width * 500 / height), 500)
                cv2.imshow(self.windowName, self.showImg)
            elif self.flag == 0:
                self.showImg = self.img.copy()
                cv2.namedWindow(self.windowName, cv2.WINDOW_NORMAL)
                height, width = self.img.shape[:2]
                cv2.resizeWindow(self.windowName, int(width * 500 / height), 500)
                if self.coords[0] != ():
                    cv2.circle(self.showImg, np.array(self.coords[0], dtype=np.int32), 15, (0, 0, 255), -1)
                    cv2.putText(self.showImg, f" {1}", np.array(self.coords[0], dtype=np.int32),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 10, 0, 0)
                if self.coords[1] != ():
                    cv2.circle(self.showImg, np.array(self.coords[1], dtype=np.int32), 15, (0, 0, 255), -1)
                    cv2.putText(self.showImg, f" {2}", np.array(self.coords[1], dtype=np.int32),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 10, 0, 0)
                cv2.imshow(self.windowName, self.showImg)
            if cv2.getTrackbarPos('pick point', self.windowName) == 2:
                # if self.coords[0] == () or self.coords[1] == ():
                #     print("Please choose both points")
                #     cv2.setTrackbarPos('finish', self.windowName, 0)
                # else:
                # print(self.coords)
                break
        cv2.destroyWindow(self.windowName)
        # print(self.coords)
        return self.coords

    def point_ID(self, x):  # 回调函数,输出正在选择的点
        if x < 2:
            print(f"正在选择第{x+1}个点")

    def nothing(self, x):
        pass


if __name__ == '__main__':
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
