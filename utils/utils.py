import cv2
import numpy as np

def imshow(window_name, img):
    """
    Self-use function in replace of cv2.imshow.\n
    Showing window is resized to height = 1000.\n
    Press Esc to close window.
    """
    height, width = img.shape[:2]
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.imshow(window_name, img)
    #if height > 600:
    cv2.resizeWindow(window_name, int(width*500/height), 500)
    #else:
    #    cv2.resizeWindow(window_name, width, height)
    k = cv2.waitKey(0)
    if k == 27:
        cv2.destroyAllWindows()
    while True:
        if cv2.getWindowProperty(window_name,cv2.WND_PROP_VISIBLE) < 1:
            break
        cv2.waitKey(1)
    cv2.destroyAllWindows()


subpix_criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 50, 0.00001)
def snap_subpix_corner(img, coords):
    """
    img: cv2.imread image object
    coord: np.array containing one or more rough coords
    """
    coords = np.array(coords, dtype=np.float32)
    cv2.cornerSubPix(img,coords,(11,11),(-1,-1),subpix_criteria)
    return coords

