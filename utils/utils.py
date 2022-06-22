import cv2
import numpy as np

def imshow(window_name, img):
    height, width = img.shape[:2]
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.imshow(window_name, img)
    cv2.resizeWindow(window_name, int(width*1000/height), 1000)
    k = cv2.waitKey(0)
    if k == 27:
        cv2.destroyAllWindows()


# show detected features
def show_keypoints(img, key_points, with_size=False):
    if with_size:
        keypoints_with_size = cv2.drawKeypoints(img, key_points, None, flags = cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        imshow('Train keypoints With Size', keypoints_with_size)
    else:
        keypoints_without_size = cv2.drawKeypoints(img, key_points, None, color = (0, 255, 0))
        imshow('Train keypoints Without Size', keypoints_without_size)




subpix_criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 50, 0.00001)
def snap_subpix_corner(img, coords):
    """
    img: cv2.imread image object
    coord: np.array containing one or more rough coords
    """
    coords = np.array(coords, dtype=np.float32)
    cv2.cornerSubPix(img,coords,(11,11),(-1,-1),subpix_criteria)
    return coords

