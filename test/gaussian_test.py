
from pathlib import Path
img_path = "datasets/0703_IMX477_6mm_newCalib/test/2.jpg"
import cv2
import numpy as np
from scipy.signal import convolve2d
from utils.utils import imshow

g1 = cv2.getGaussianKernel(5, 1)
g2 = np.outer(g1,g1)
print(g2)


def gauss2D(shape=(3,3),sigma=1.):
    """
    2D gaussian mask - should give the same result as MATLAB's
    fspecial('gaussian',[shape],[sigma])
    """
    m,n = [(ss-1.)/2. for ss in shape]
    y,x = np.ogrid[-m:m+1,-n:n+1]
    h = np.exp( -(x*x + y*y) / (2.*sigma*sigma) )
    h[ h < np.finfo(h.dtype).eps*h.max() ] = 0
    sumh = h.sum()
    if sumh != 0:
        h /= sumh
    return h

g2 = gauss2D(shape=(5,5), sigma=4)
print(g2)
img = cv2.imread(img_path, 0)
img = convolve2d(img, g2, mode='same')
imshow('res',np.absolute(img))
