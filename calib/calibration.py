import os
import cv2
import numpy as np
from tqdm import tqdm
from pathlib import Path

# from showimg import imshow
from model.camera_model import CameraModel


class Calibrate():
    def __init__(self, camera, operation_folder, show_result = False) -> None:
        self.camera = camera

        # folder Path object
        self.operation_folder = Path(f'datasets/{operation_folder}')
        self.scenes_folder = self.operation_folder / 'scenes'
        self.data_folder = self.operation_folder / 'calibration_data'
        self.total_photos = len(list(self.scenes_folder.iterdir()))
        
        self.show_result = show_result
        try:
            npz_path = self.data_folder / "chessboard.npz"
            npz_file = np.load(npz_path)
            self.objpoints = npz_file['objpoints']
            self.imgpointsLeft = npz_file['imgpointsLeft']
            self.imgpointsRight = npz_file['imgpointsRight']
        except:
            print("No chessboard data found. \nPlease preprocess images before calibration")
            exit(1)


    def single_calibrate(self):
        if self.camera.is_fisheye:
            self._single_calibrate_fisheye()
        else:
            self._single_calibrate_vanilla()


    def stereo_calibrate(self):
        if self.camera.is_fisheye:
            self._stereo_calibrate_fisheye()
        else:
            self._stereo_calibrate_vanilla()
    

    #################################
    # calibrate SINGLE camera - Vanilla
    #################################
    def _single_calibrate_vanilla(self):
        print("Calibrating single camera - Vanilla...")
        objpoints = self.objpoints
        imgpointsLeft  = self.imgpointsLeft
        imgpointsRight = self.imgpointsRight

        ############# Filter outliers ###############
        outliers_id = []#1, 30,31,32]       # result of perViewError <- stereoCalibrateExtended()
        inliers =  [True if id not in outliers_id 
                    else False
                    for id in range(self.total_photos)]
        objpoints = objpoints[inliers]
        imgpointsLeft  = imgpointsLeft[inliers]
        imgpointsRight = imgpointsRight[inliers]

        #region #######Calibrate Single Camera######## 
        # ret               -> RMSE, Root Mean Square Error
        # cameraMatrix      -> K, Intrinsic Params including fx, fy, u0, v0
        # distCoeff         -> Distortion params
        # rvecs             -> Rotation Vectors, maps world coord to image coord
        # tvecs             -> Translation Vecs
        #endregion
        ret1, cm1, cd1, rvecs, tvecs = cv2.calibrateCamera(
                objpoints, imgpointsLeft, 
                self.camera.image_size, None, None
            )
        ret2, cm2, cd2, rvecs, tvecs = cv2.calibrateCamera(
                objpoints, imgpointsRight, 
                self.camera.image_size, None, None
            )
        self.camera.update_params(cm1,cd1,cm2,cd2, None, None)

        if self.show_result:
            print(f'''
=============== Single Camera Calib ===============
--------------Left Camera---------------
RMS (Root Mean Square Error): {ret1}
K (Intrinsic Params): \n{cm1}''', 
            end='')
            print(f'''
--------------Right Camera-------------
RMS (Root Mean Square Error): {ret2}
K (Intrinsic Params): \n{cm2}
            ''')
        else:
            print("Calibrate single camera done.")
    
    #################################
    # calibrate SINGLE camera - Fisheye - TODO
    #################################
    def _single_calibrate_fisheye(self):
        pass


    #################################
    # calibrate STEREO camera - Vanilla
    #################################
    def _stereo_calibrate_vanilla(self):
        print("Calibrating stereo camera - Vanilla...")
        objpoints = self.objpoints
        imgpointsLeft  = self.imgpointsLeft
        imgpointsRight = self.imgpointsRight

        #region #########Calibrate Dual Camera########## 
        # This can be replaced by ~Extended() function; pass R, T; get perViewError.
        # RMS -> error in pixel
        # cm1,2 -> camera matrix
        # cd1,2 -> camera distortion
        # R, T -> rotation and translation between two cameras
        # E, F -> esstential and fundamental matrix
        # perViewError -> RMS for every image pair
        #endregion
        calib_criteria = (cv2.TERM_CRITERIA_COUNT+cv2.TERM_CRITERIA_EPS, 100, 1e-5)
        flags = cv2.CALIB_USE_INTRINSIC_GUESS
        RMS, cm1, cd1, cm2, cd2, R, T, E, F,perViewError = \
            cv2.stereoCalibrateExtended(
                objpoints, 
                imgpointsLeft, imgpointsRight, 
                self.camera.cm1, self.camera.cd1, 
                self.camera.cm2, self.camera.cd2, 
                self.camera.image_size, 
                None, None, 
                criteria=calib_criteria, 
                flags=flags
            )
        self.camera.update_params(cm1, cd1, cm2, cd2, R, T)
        
        if self.show_result:
            print(f'''
================ Dual Camera Calib ================
RMS: {RMS}
----------Left Cam----------
K (Intrinsic Params): \n{cm1}
Distortion Coefficient:\n{cd1}
----------Right Cam---------
K (Intrinsic Params): \n{cm2}
Distortion Coefficient:\n{cd2}
------Extrinsic Params------
R: \n{R}
T: \n{T}''')
        else:
            print("Calibrate stereo camera done.")
        # print(perViewError)

        npz_path = self.data_folder / "camera_model.npz"
        self.camera.save_model(npz_path)


    #################################
    # calibrate STEREO camera - Fisheye - TODO
    #################################
    def _stereo_calibrate_fisheye(self):
        pass


if __name__ == "__main__":
    CCD = 'IMX477'
    fisheye = False
    operation_folder = '0610_IMX477_infinity_still'

    camera = CameraModel(CCD, fisheye)
    calibration = Calibrate(camera, operation_folder) #, show_result=False)
    calibration.single_calibrate()
    calibration.stereo_calibrate()
    print()
