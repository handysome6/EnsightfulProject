import cv2
from utils.utils import imshow, snap_subpix_corner

global img, cutimg, point1, point2, finish, resize


# def on_mouse(event, x, y, flags, param):
#     global img, cutimg, point1, point2, finish, resize
#     img2 = img.copy()
#     if event == cv2.EVENT_LBUTTONDOWN:
#         point1 = (x, y)
#         cv2.circle(img2, point1, 10, (0, 255, 0), 5)
#         cv2.imshow('Click the image to select the point, or drag to zoom in and select', img2)
#     elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):
#         # cv2.rectangle(img2, point1, (x, y), (255, 0, 0), 5)
#         # cv2.imshow('Click the image to select the point, or drag to zoom in and select', img2)
#         img3 = img2.copy()
#         cut_img = img3[y - 50: y + 50, x - 50 :x + 50]
#         cv2.circle(cut_img, (50,50), 5, (0, 255, 0), -1)
#         cv2.namedWindow('zoomed image', cv2.WINDOW_NORMAL)
#         cv2.imshow('zoomed image', cut_img)
#     elif event == cv2.EVENT_LBUTTONUP:
#         point2 = (x, y)
#         cv2.rectangle(img2, point1, point2, (0, 0, 255), 5)
#         min_x = min(point1[0], point2[0])
#         min_y = min(point1[1], point2[1])
#         width = abs(point1[0] - point2[0])
#         height = abs(point1[1] - point2[1])
#         if width == 0:
#             resize = 1
#             cutimg = img2
#             cv2.destroyAllWindows()
#             finish = 1
#             resize = 0
#             return
#         cut_img = img[min_y:min_y + height, min_x:min_x + width]
#         cutimg = cut_img.copy()
#         cv2.destroyAllWindows()
#         finish = 1

def on_mouse(event, x, y, flags, param):
    global img, cutimg, point1, point2, finish, resize
    img2 = img.copy()
    if event == cv2.EVENT_LBUTTONDOWN:
        point1 = (x, y)
        cv2.circle(img2, point1, 10, (0, 255, 0), 5)
        cv2.imshow('Click the image to select the point, or drag to zoom in and select', img2)
    elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):
        img3 = img2.copy()
        cut_img = img3[y - 50: y + 50, x - 50 :x + 50]
        cv2.circle(cut_img, (50,50), 5, (0, 255, 0), -1)
        cv2.namedWindow('zoomed image', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('zoomed image', 200, 200)
        if(x > 2028):
            cv2.moveWindow("zoomed image", 100, 100)
        else:
            cv2.moveWindow("zoomed image", 1100, 100)
        cv2.imshow('zoomed image', cut_img)
    elif event == cv2.EVENT_LBUTTONUP:
        point2 = (x, y)
        cv2.destroyAllWindows()

# def cut(oriimg):
#     global img, cutimg, point1, point2
#     img = oriimg.copy()
#     cv2.namedWindow('image', cv2.WINDOW_NORMAL)
#     cv2.setMouseCallback('image', on_mouse)
#     imshow('image', img)
#     # cv2.imshow('image', img)
#     cv2.waitKey(0)
#     min_x = min(point1[0], point2[0])
#     min_y = min(point1[1], point2[1])
#     del point1, point2
#     return cutimg, min_x, min_y

def cut(oriimg):
    global img, cutimg, point1, point2, finish, resize
    finish = 0
    resize = 1
    x = ()
    img = oriimg.copy()
    cv2.namedWindow('Click the image to select the point, or drag to zoom in and select', cv2.WINDOW_NORMAL)
    cv2.setMouseCallback('Click the image to select the point, or drag to zoom in and select', on_mouse)
    height, width = img.shape[:2]
    cv2.imshow('Click the image to select the point, or drag to zoom in and select', img)
    cv2.resizeWindow('Click the image to select the point, or drag to zoom in and select', int(width * 1000 / height), 1000)
    cv2.waitKey(0)
    x = (point2[0], point2[1])
    del point2
    return x


