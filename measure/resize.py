import cv2

class showimg():
    # 全局变量
    def __init__(self, imgsize, image) -> None:

        self.g_window_name = "img"  # 窗口名
        self.g_window_wh = imgsize  # 窗口宽高

        self.g_location_win = [0, 0]  # 相对于大图，窗口在图片中的位置
        self.location_win = [0, 0]  # 鼠标左键点击时，暂存g_location_win
        self.g_location_click, self.g_location_release = [0, 0], [0, 0]  # 相对于窗口，鼠标左键点击和释放的位置

        self.g_zoom, self.g_step = 1, 0.1  # 图片缩放比例和缩放系数
        self.g_image_original = image  # 原始图片，建议大于窗口宽高（800*600）
        self.g_image_zoom = self.g_image_original.copy()  # 缩放后的图片
        self.g_image_show = self.g_image_original[self.g_location_win[1]:self.g_location_win[1] + self.g_window_wh[1], self.g_location_win[0]:self.g_location_win[0] + self.g_window_wh[0]]  # 实际显示的图片


    # 矫正窗口在图片中的位置
    # img_wh:图片的宽高, win_wh:窗口的宽高, win_xy:窗口在图片的位置
    def check_location(img_wh, win_wh, win_xy):
        for i in range(2):
            if win_xy[i] < 0:
                win_xy[i] = 0
            elif win_xy[i] + win_wh[i] > img_wh[i] and img_wh[i] > win_wh[i]:
                win_xy[i] = img_wh[i] - win_wh[i]
            elif win_xy[i] + win_wh[i] > img_wh[i] and img_wh[i] < win_wh[i]:
                win_xy[i] = 0
        # print(img_wh, win_wh, win_xy)


    # 计算缩放倍数
    # flag：鼠标滚轮上移或下移的标识, step：缩放系数，滚轮每步缩放0.1, zoom：缩放倍数
    def count_zoom(flag, step, zoom):
        if flag > 0:  # 滚轮上移
            zoom += step
            if zoom > 1 + step * 20:  # 最多只能放大到3倍
                zoom = 1 + step * 20
        else:  # 滚轮下移
            zoom -= step
            if zoom < step:  # 最多只能缩小到0.1倍
                zoom = step
        zoom = round(zoom, 2)  # 取2位有效数字
        return zoom


    # OpenCV鼠标事件
    def mouse(event, x, y, flags, param):
        # global g_location_click, g_location_release, g_image_show, g_image_zoom, g_location_win, location_win, g_zoom
        if event == cv2.EVENT_LBUTTONDOWN:  # 左键点击
            showimg().g_location_click = [x, y]  # 左键点击时，鼠标相对于窗口的坐标
            showimg().location_win = [showimg().g_location_win[0], showimg().g_location_win[1]]  # 窗口相对于图片的坐标，不能写成location_win = g_location_win
        elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):  # 按住左键拖曳
            g_location_release = [x, y]  # 左键拖曳时，鼠标相对于窗口的坐标
            h1, w1 = showimg().g_image_zoom.shape[0:2]  # 缩放图片的宽高
            w2, h2 = showimg().g_window_wh  # 窗口的宽高
            show_wh = [0, 0]  # 实际显示图片的宽高
            if w1 < w2 and h1 < h2:  # 图片的宽高小于窗口宽高，无法移动
                show_wh = [w1, h1]
                showimg().g_location_win = [0, 0]
            elif w1 >= w2 and h1 < h2:  # 图片的宽度大于窗口的宽度，可左右移动
                show_wh = [w2, h1]
                showimg().g_location_win[0] = showimg().location_win[0] + showimg().g_location_click[0] - showimg().g_location_release[0]
            elif w1 < w2 and h1 >= h2:  # 图片的高度大于窗口的高度，可上下移动
                show_wh = [w1, h2]
                showimg().g_location_win[1] = showimg().location_win[1] + showimg().g_location_click[1] - showimg().g_location_release[1]
            else:  # 图片的宽高大于窗口宽高，可左右上下移动
                show_wh = [w2, h2]
                showimg().g_location_win[0] = showimg().location_win[0] + showimg().g_location_click[0] - showimg().g_location_release[0]
                showimg().g_location_win[1] = showimg().location_win[1] + showimg().g_location_click[1] - showimg().g_location_release[1]
            showimg().check_location([w1, h1], [w2, h2], showimg().g_location_win)  # 矫正窗口在图片中的位置
            showimg().g_image_show = showimg().g_image_zoom[showimg().g_location_win[1]:showimg().g_location_win[1] + show_wh[1], showimg().g_location_win[0]:showimg().g_location_win[0] + show_wh[0]]  # 实际显示的图片
        elif event == cv2.EVENT_MOUSEWHEEL:  # 滚轮
            z = showimg().g_zoom  # 缩放前的缩放倍数，用于计算缩放后窗口在图片中的位置
            showimg().g_zoom = showimg().count_zoom(flags, showimg().g_step, showimg().g_zoom)  # 计算缩放倍数
            w1, h1 = [int(showimg().g_image_original.shape[1] * showimg().g_zoom), int(showimg().g_image_original.shape[0] * showimg().g_zoom)]  # 缩放图片的宽高
            w2, h2 = showimg().g_window_wh  # 窗口的宽高
            g_image_zoom = cv2.resize(showimg().g_image_original, (w1, h1), interpolation=cv2.INTER_AREA)  # 图片缩放
            show_wh = [0, 0]  # 实际显示图片的宽高
            if w1 < w2 and h1 < h2:  # 缩放后，图片宽高小于窗口宽高
                show_wh = [w1, h1]
                cv2.resizeWindow(showimg().g_window_name, w1, h1)
            elif w1 >= w2 and h1 < h2:  # 缩放后，图片高度小于窗口高度
                show_wh = [w2, h1]
                cv2.resizeWindow(showimg().g_window_name, w2, h1)
            elif w1 < w2 and h1 >= h2:  # 缩放后，图片宽度小于窗口宽度
                show_wh = [w1, h2]
                cv2.resizeWindow(showimg().g_window_name, w1, h2)
            else:  # 缩放后，图片宽高大于窗口宽高
                show_wh = [w2, h2]
                cv2.resizeWindow(showimg().g_window_name, w2, h2)
            showimg().g_location_win = [int((showimg().g_location_win[0] + x) * showimg().g_zoom / z - x), int((showimg().g_location_win[1] + y) * showimg().g_zoom / z - y)]  # 缩放后，窗口在图片的位置
            showimg().check_location([w1, h1], [w2, h2], showimg().g_location_win)  # 矫正窗口在图片中的位置
            # print(g_location_win, show_wh)
            showimg().g_image_show = showimg().g_image_zoom[showimg().g_location_win[1]:showimg().g_location_win[1] + show_wh[1], showimg().g_location_win[0]:showimg().g_location_win[0] + show_wh[0]]  # 实际的显示图片
        cv2.imshow(showimg().g_window_name, showimg().g_image_show)


def showing(imgsize, image):
    img = showimg(imgsize, image)
    cv2.namedWindow(img.g_window_name, cv2.WINDOW_NORMAL)
    # 设置窗口大小，只有当图片大于窗口时才能移动图片
    cv2.resizeWindow(img.g_window_name, img.g_window_wh[0], img.g_window_wh[1])
    cv2.moveWindow(img.g_window_name, 700, 100)  # 设置窗口在电脑屏幕中的位置
    # 鼠标事件的回调函数
    cv2.setMouseCallback(img.g_window_name, img.mouse)
    cv2.waitKey()  # 不可缺少，用于刷新图片，等待鼠标操作
    cv2.destroyAllWindows()

# 主函数
if __name__ == "__main__":
    # 设置窗口
    cv2.namedWindow(showimg().g_window_name, cv2.WINDOW_NORMAL)
    # 设置窗口大小，只有当图片大于窗口时才能移动图片
    cv2.resizeWindow(showimg().g_window_name, showimg().g_window_wh[0], showimg().g_window_wh[1])
    cv2.moveWindow(showimg().g_window_name, 700, 100)  # 设置窗口在电脑屏幕中的位置
    # 鼠标事件的回调函数
    cv2.setMouseCallback(showimg().g_window_name, showimg().mouse)
    cv2.waitKey()  # 不可缺少，用于刷新图片，等待鼠标操作
    cv2.destroyAllWindows()
