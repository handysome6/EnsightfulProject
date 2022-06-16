import cv2

def imshow(window_name, img):
    height, width = img.shape[:2]
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.imshow(window_name, img)
    cv2.resizeWindow('left', int(width*1000/height), 1000)
    k = cv2.waitKey(0)
    if k == 27:
        exit()
