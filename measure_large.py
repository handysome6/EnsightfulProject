import sys
import cv2
import numpy as np
from pathlib import Path
from measure.matcher import MATCHER_TYPE

from model.camera_model import CameraModel
from calib.rectification import StereoRectify
from utils.utils import snap_subpix_corner, imshow
from measure.ruler import Ruler

# def findRT1(img1,img2):
#     # Detect keypoints and compute their descriptors
#     sift = cv2.xfeatures2d.SIFT_create()
#     kp1, des1 = sift.detectAndCompute(img1, None)
#     kp2, des2 = sift.detectAndCompute(img2, None)
#
#     # Match the keypoints and find the inliers
#     bf = cv2.BFMatcher()
#     matches = bf.match(des1, des2)
#     src_pts = np.array([kp1[m.queryIdx].pt for m in matches], dtype=np.float32)
#     dst_pts = np.array([kp2[m.trainIdx].pt for m in matches], dtype=np.float32)
#     F, inliers = cv2.findFundamentalMat(src_pts, dst_pts, cv2.RANSAC)
#
#     # Compute the essential matrix and decompose it to get the rotation and translation matrices
#     E = K.T @ F @ K
#     U, D, V = np.linalg.svd(E)
#     W = np.array([0, -1, 0, 1, 0, 0, 0, 0, 1]).reshape(3, 3)
#
#     R = U @ W @ V
#     T = U[:, 2]
#
#     # Form the 4x4 transformation matrix
#     transform = np.hstack((np.hstack((R, T.reshape(3, 1))), np.array([0, 0, 0, 1]).reshape(1, 4)))
def get_world_coord_Q(Q, img_coord_left, img_coord_right):
    world = []
    for left, right in zip(img_coord_left, img_coord_right):
        x, y = left
        d = left[0] - right[0]
        # print(x, y, d); exit(0)
        homg_coord = Q.dot(np.array([x, y, d, 1.0]))
        coord = homg_coord / homg_coord[3]
        world.append(coord[:-1])
        # print(coord[:-1])
    return world

def get_correspond_candidates(point):

    point = np.squeeze(point)
    coord_x, coord_y = point
    # remove empty axis
    half = 2
    pts = []
    # iterate through the region
    for i in range(coord_y - half, coord_y + half + 1):
        for j in range(max(coord_x - 600, 0), coord_x - 2 + 1):
            pts.append(np.array([j, i]))
    pts = np.array(pts, dtype=np.float32)
    keypoints = cv2.KeyPoint.convert(pts)
    # print("Got coorespond region for ", point)
    return keypoints

# using cv2.recoverPose to solve rotation and translation matrix
def findRT(img1, img2):
    # Detect and extract keypoints and descriptors from both images
    sift = cv2.xfeatures2d.SIFT_create()
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    # Match the keypoints between the two images using Brute-Force matcher
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)

    # Keep only good matches that satisfy the Lowe's ratio test
    good_matches = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good_matches.append(m)

    # Get the matched keypoints
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    # Camera matrix
    k = np.array([[2538.520201493674, 0.0, 2051.050760075861],
                [0.0, 2538.520201493674, 1506.8039266078001],
                [0.0, 0.0, 1.0]], dtype=np.float32)
    mat = cv2.Mat(k)

    # Normalize the image points
    src_pts = np.divide(src_pts, [2538.520201493674, 2538.520201493674])
    dst_pts = np.divide(dst_pts, [2538.520201493674, 2538.520201493674])
    # Compute the essential matrix using RANSAC method
    E, mask = cv2.findEssentialMat(src_pts, dst_pts, method=cv2.RANSAC, prob=0.999, threshold=1.0)
    # Decompose the essential matrix into rotation and translation matrices
    _, R, T, mask = cv2.recoverPose(E, src_pts, dst_pts, mat)
    # print("R ", R)
    T = T.reshape(1,3) * np.array([2538.520201493674, 2538.520201493674, 1])
    # print('T', T)
    M = np.zeros((4, 4))
    M[:3, :3] = R
    M[:3, 3] = T
    M[3, 3] = 1
    print('matrix  ',M)
    return M

# cv2.solvePnP use the matching 3d coordinate in world W and 2d coordinate in image1 to estimate camera1 pose in world
# W, similarly use the same point for camera2, this time the 3d coordinate in world W keep the same and the 2d
# coordinate is in image2, estimate camera2 pose in world W. we get both camera pose, and we can calculate the
# translation and rotation matrix of camera2 relative to camera1 (camera relative pose)

# for world coordinate, currently use the same workflow as before but calculate the coordinate for all the matching
# point in image1 and image2, doing so the algorithm is very slow because the candidate keypoint and descriptor are
# calculated many times. test the algorithm accuracy, if it's satisfactory, store all the descriptors of imageL2 to
# reduce time
def BAfindRT(img1, img2, imgR, Q):
    # Detect keypoints and extract features in both images
    sift = cv2.xfeatures2d.SIFT_create()
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    # Match features between the two images
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)

    # Filter matches using the Lowe's ratio test
    good = []
    # pts1 and pts2 are the matching points of two left images, in this function we want the translation and rotation
    # matrix of these two camera, so we can translate the world coordinate in left image2 to left image1 to measure
    # large object
    pts1 = []
    pts2 = []
    for m, n in matches:
        if m.distance < 0.5 * n.distance:  #0.75 default, lower value, higher similarity and less matching
            good.append([m])
            pts2.append(kp2[m.trainIdx].pt)
            pts1.append(kp1[m.queryIdx].pt)

    # Convert the lists to numpy arrays
    pts2 = np.array(pts2, dtype=np.float32)
    K = np.array([[2538.520201493674, 0.0, 2051.050760075861],
                  [0.0, 2538.520201493674, 1506.8039266078001],
                  [0.0, 0.0, 1.0]], dtype=np.float32)
    point_discriptor = cv2.SIFT_create()
    match_keypoints = []
    new_pts1 = []
    new_pts2 = []
    # Load the list of 2D points in the left image
    for point, point2 in zip(pts1,pts2):
        point = np.expand_dims(point, axis=0)
        assert len(point.shape) == 2
        ref_keypoints = cv2.KeyPoint.convert(np.array(point, dtype=np.float32))
        ref_keypoints, ref_descriptors = point_discriptor.compute(img1, ref_keypoints)
        # convert type to int
        point = np.array(point, dtype=np.int32)
        # compute candidates RIGHT
        candidates = get_correspond_candidates(point[0])
        if len(candidates) > 1:
            corr_keypoints, corr_descriptors = point_discriptor.compute(imgR, candidates)

            # select point feature
            feature = ref_descriptors[0]
            # compare with corr features
            distances = []
            for corr_f in corr_descriptors:
                distances.append(cv2.norm(feature, corr_f, cv2.NORM_L1))
            # find nearest feature
            distances = np.array(distances)
            ind = np.argpartition(distances, 1)[0]
            match_keypoints.append(corr_keypoints[ind])
            # only keep the points which has more than one candidate, because we need the matching points in right
            # images to calculate the world coordinate
            new_pts2.append(point2)
            new_pts1.append(point)
    match_points = cv2.KeyPoint.convert(match_keypoints)
    new_pts1 = np.array(new_pts1,dtype=np.float32).reshape(-1, 2)
    pts1_nom = get_world_coord_Q(Q, new_pts1, match_points) #pts1_nom is the 3D world coordinate of the matching points
    pts1_nom = np.array(pts1_nom).reshape(-1,3)
    pts2 = np.array(new_pts2, dtype=np.float32)
    print(len(new_pts1),len(pts2))
    # Perform bundle adjustment using cv2.solvePnPRansac function
    pnp_result, rvec, tvec, inliers = cv2.solvePnPRansac(pts1_nom, pts2, K, distCoeffs=None)
    print("bundle adjustment result",pnp_result)
    # Convert the rotation vector to rotation matrix
    R, _ = cv2.Rodrigues(rvec)
    tvec = tvec.reshape(1, 3)
    # compose R and tvec to form 4*4 transformation matrix
    M = np.zeros((4, 4))
    M[:3, :3] = R
    M[:3, 3] = tvec
    M[3, 3] = 1
    print("BAmatrix", M)

    pnp_result1, rvec1, tvec1, inliers1 = cv2.solvePnPRansac(pts1_nom, new_pts1, K, distCoeffs=None)
    print("bundle adjustment result", pnp_result1)
    # Convert the rotation vector to rotation matrix
    R1, _ = cv2.Rodrigues(rvec1)
    tvec1 = tvec1.reshape(1, 3)
    M1 = np.zeros((4, 4))
    M1[:3, :3] = R1
    M1[:3, 3] = tvec1
    M1[3, 3] = 1
    print("BAmatrix1", M1)
    print(np.divide(R,R1), np.divide(R1,R), np.subtract(tvec1,tvec))
    # result = np.zeros((4,4))
    # result[:3, :3] = np.divide(R,R1)
    # result[:3, 3] = np.subtract(tvec1,tvec)
    # result[3, 3] = 1
    result1 = np.zeros((4, 4))
    result1[:3, :3] = np.divide(R1, R)
    result1[:3, 3] = np.subtract(tvec1, tvec)
    result1[3, 3] = 1
    # result2 = np.zeros((4, 4))
    # result2[:3, :3] = np.divide(R, R1)
    # result2[:3, 3] = np.subtract(tvec, tvec1)
    # result2[3, 3] = 1
    result3 = np.zeros((4, 4))
    result3[:3, :3] = np.divide(R1, R)
    result3[:3, 3] = np.subtract(tvec, tvec1)
    result3[3, 3] = 1
    return result1,result3

def find_transformation_matrix(img1, img2):
    # Initiate SIFT detector
    sift = cv2.xfeatures2d.SIFT_create()

    # Find the keypoints and descriptors with SIFT
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    # Use BFMatcher to match the keypoints and descriptors
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)

    # Select the good matches using the ratio test
    good = []
    for m, n in matches:
        if m.distance < 0.7 * n.distance:
            good.append(m)

    # Find the homography matrix using the good matches
    if len(good) > 4:
        print(len(good))
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        print(H)
        return H
    return None


# pick image
operation_folder = Path(r"C:\Users\xtx23\EnsightfulProject_old\datasets\testBA\\")
assert operation_folder.is_dir()
img_path1, img_path2 = list(operation_folder.iterdir())[1:]
# load camera model
cam_path = Path(r"C:\Users\xtx23\EnsightfulProject_old\datasets\testBA") / "camera_model.json"
camera = CameraModel.load_model(cam_path)

# rectify image
sbs_img1 = cv2.imread(str(img_path1))
sbs_img2 = cv2.imread(str(img_path2))
rectifier = StereoRectify(camera, operation_folder)
imgL1, imgR1 = rectifier.rectify_image(sbs_img=sbs_img1)
imgL2, imgR2 = rectifier.rectify_image(sbs_img=sbs_img2)
# T12 = find_transformation_matrix(imgL1, imgL2)
# T21 = find_transformation_matrix(imgL2, imgL1)
M = findRT(imgL1, imgL2)
Mba1, Mba3 = BAfindRT(imgL1, imgL2, imgR1,rectifier.Q)
# Mba3[:3, 3] = np.zeros((1,3)) - M[:3, 3]
# M1 = findRT(imgL2, imgL1)
# Mba2 = BAfindRT(imgL2, imgL1, imgR2,rectifier.Q)
# M2 = findRT(imgL1, imgR1)
# M2 = findRT(imgR1, imgL1)
# M3 = findRT(imgL2, imgR2)
# M2 = findRT(imgR2, imgL2)


# measure
ruler1 = Ruler(rectifier.Q, imgL1, imgR1)
run1 = ruler1.click_segment(automatch=True, matcher=MATCHER_TYPE.SIFT)
if run1 == 1:
    pointL1, pointL2 = ruler1.get_endpoint()
    len = ruler1.measure_segment()
    print(len)
    print("image1 point ",pointL1)
else:
    print("Not enough points, program ends")

ruler2 = Ruler(rectifier.Q, imgL2, imgR2)
run2 = ruler2.click_segment(automatch=True, matcher=MATCHER_TYPE.SIFT)
if run2 == 1:
    pointR1, pointR2 = ruler2.get_endpoint()
    len = ruler2.measure_segment()
    print(len)
    print("image2 point ",pointR1)
else:
    print("Not enough points, program ends")
# add 1 to form 1*4 matrix to multiply with transformation matrix
P_A = np.array([pointR1[0], pointR1[1], pointR1[2], 1])
P_A1 = np.array([pointR2[0], pointR2[1], pointR2[2], 1])
# P_C = np.array([pointL1[0], pointL1[1], pointL1[2], 1])
P_B = np.dot(M, P_A)
P_B = P_B[:3] / P_B[3]

P_Bba1 = np.dot(Mba1, P_A)
P_Bba1 = P_Bba1[:3] / P_Bba1[3]

P_Bba3 = np.dot(Mba3, P_A)
P_Bba3 = P_Bba3[:3] / P_Bba3[3]

P_C = np.dot(M, P_A1)
P_C = P_C[:3] / P_C[3]

P_Cba1 = np.dot(Mba1, P_A1)
P_Cba1 = P_Cba1[:3] / P_Cba1[3]

P_Cba3 = np.dot(Mba3, P_A1)
P_Cba3 = P_Cba3[:3] / P_Cba3[3]


segment_len12 = cv2.norm(pointL1, P_B)
segment_len12ba1 = cv2.norm(pointL1, P_Bba1)
segment_len12ba3 = cv2.norm(pointL1, P_Bba3)
segment_len212 = cv2.norm(pointL2, P_C)
segment_len212ba1 = cv2.norm(pointL2, P_Cba1)
segment_len212ba3 = cv2.norm(pointL2, P_Cba3)
# segment_len12ba4 = cv2.norm(pointL1, P_Bba4)
# segment_len21ba = cv2.norm(pointL1, P_Bba1)
# segment_len23 = cv2.norm(pointR1, P_D)
# segment_len32 = cv2.norm(pointR1, P_D1)
# print(segment_len12,segment_len21,segment_len23,segment_len32)
print(segment_len12,segment_len12ba1,segment_len12ba3)
print(segment_len212,segment_len212ba1,segment_len212ba3)