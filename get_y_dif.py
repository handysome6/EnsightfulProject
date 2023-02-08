import sys
import cv2
from pathlib import Path
import statistics
from model.camera_model import CameraModel
from calib.rectification import StereoRectify
import matplotlib.pyplot as plt


# region
# pick image
folder_name = "1219"
operation_folder = Path("datasets") / folder_name
test_folder = Path("datasets/1219") / 'scenes'
assert test_folder.is_dir()
img_path = list(test_folder.iterdir())[:]
print("Measuring", img_path)

# load camera model
cam_path = Path(r"C:\Users\xtx23\EnsightfulProject_old\datasets\1219\camera_model") / "camera_model.json"
camera = CameraModel.load_model(cam_path)
num = 0
y_dif = []
for path in img_path:
# rectify image
    sbs_img = cv2.imread(str(path))
    rectifier = StereoRectify(camera, operation_folder)
    img1, img2 = rectifier.rectify_image(sbs_img=sbs_img)

    sift = cv2.xfeatures2d.SIFT_create()
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)
    bf =cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)
    dif_list = []
    matchesMask = [[0, 0] for i in range(len(matches))]
    dif = 0
    index = 0
    for i, (m1, m2) in enumerate(matches):
        if m1.distance < 0.5 * m2.distance:# 两个特征向量之间的欧氏距离，越小表明匹配度越高。
            matchesMask[i] = [1, 0]
            pt1 = kp1[m1.queryIdx].pt  # trainIdx    是匹配之后所对应关键点的序号，第一个载入图片的匹配关键点序号
            cv2.circle(img1, (int(pt1[0]),int(pt1[1])), 10, (0,0,255), -1)
            pt2 = kp2[m1.trainIdx].pt  # queryIdx  是匹配之后所对应关键点的序号，第二个载入图片的匹配关键点序号
            cv2.circle(img2, (int(pt2[0]),int(pt2[1])), 10, (0,0,255), -1)
            dif = pt1[1] - pt2[1]
            dif = dif
            dif_list.append(dif)
            index = index + 1
            # print(kpts1)
            # print(i, pt1, pt2)
    print(dif_list)
    meadif = statistics.median(dif_list)
    print(meadif)
    draw_params = dict(matchColor = (255, 255, 255),
            singlePointColor = None,
            matchesMask = matchesMask,
            flags = cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    img3 = cv2.drawMatchesKnn(img1, kp1, img2, kp2, matches, None, **draw_params)
    img3 = cv2.cvtColor(img3, cv2.COLOR_BGR2RGB)
    my_string = 'Matching points number: '
    my_string = my_string + str(index)
    my_string = my_string + ', median y coordinate difference is '
    my_string = my_string + str(round(meadif, 2))
    img3 = cv2.putText(img3, my_string, (50,150), cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 0, 0), 4, cv2.LINE_AA)
    # display the result
    # plt.rcParams['figure.dpi'] = 300
    # plt.imshow(img3, 'gray'), plt.show()
    # plt.hist(dif_list, bins = len(dif_list), range = (-5,5))
    # plt.xlabel('Y coordinate difference')
    # plt.ylabel('number of difference value')
    # plt.show()

    # save results
    cv2.imwrite('datasets/1219/y_dif_result/Image'+str(num)+'.jpg', img3)
    num +=1
    print(num)
    y_dif.append(meadif)
print(y_dif)
result = ' '.join(map(str, y_dif))
with open('datasets/1219/y_dif_result/y_dif_result.txt', 'w') as f:
    f.write(result)