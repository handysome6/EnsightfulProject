from logging import info
import os
import cv2
import numpy as np
from tqdm import tqdm
from pathlib import Path

# from showimg import imshow
from model.camera_model import CameraModel


class Calibrate():
    def __init__(self, camera, operation_folder) -> None:
        self.camera = camera

        # folder Path object
        self.operation_folder = Path(f'datasets/{operation_folder}')
        self.scenes_folder = self.operation_folder / 'scenes'
        self.data_folder = self.operation_folder / 'calibration_data'
        self.total_photos = len(list(self.scenes_folder.iterdir()))
        
        try:
            npz_path = self.data_folder / "chessboard.npz"
            npz_file = np.load(npz_path)
            self.objpoints = npz_file['objpoints']
            self.imgpointsLeft = npz_file['imgpointsLeft']
            self.imgpointsRight = npz_file['imgpointsRight']
        except:
            raise("No chessboard data found. \nPlease preprocess images before calibration")

        return 
        ############# Filter outliers ###############
        outliers_id = []#1, 30,31,32]       # result of perViewError <- stereoCalibrateExtended()
        inliers =  [True if id not in outliers_id 
                    else False
                    for id in range(self.total_photos)]
        objpoints = objpoints[inliers]
        imgpointsLeft  = imgpointsLeft[inliers]
        imgpointsRight = imgpointsRight[inliers]


    def single_calibrate(self, **arg):
        """
        Calibrate SINGLE left and right camera.
        Switcher function. 
        """
        if self.camera.is_fisheye:
            self._single_calibrate_fisheye()
        else:
            self._single_calibrate_vanilla(**arg)


    def stereo_calibrate(self, **args):
        """
        Calibrate DUAL camera.
        Switcher function. 
        """
        if self.camera.is_fisheye:
            self._stereo_calibrate_fisheye(**args)
        else:
            self._stereo_calibrate_vanilla(**args)
    

    def _single_calibrate_vanilla(self, left_view_path = None, right_view_path = None):
        """
        Calibrate SINGLE camera - Vanilla
        """
        info("Calibrating SINGLE camera - Vanilla...")
        objpoints = self.objpoints
        imgpointsLeft  = self.imgpointsLeft
        imgpointsRight = self.imgpointsRight
        if left_view_path is not None and right_view_path is not None:
            info("Using single images to calib ")
            imgpointsLeft = np.load(left_view_path)['corners']
            imgpointsRight = np.load(right_view_path)['corners']

        # rvecs             -> Rotation Vectors, maps world coord to image coord
        # tvecs             -> Translation Vecs
        ret1, cm1, cd1, rvecs, tvecs = cv2.calibrateCamera(
                objpoints, imgpointsLeft, 
                self.camera.image_size, None, None
            )
        ret2, cm2, cd2, rvecs, tvecs = cv2.calibrateCamera(
                objpoints, imgpointsRight, 
                self.camera.image_size, None, None
            )
        self.camera.update_intrinsic(cm1,cd1,cm2,cd2)

        print(f'''=============== Single Camera Calib ===============
--------------Left Camera---------------
RMS: {ret1}
Camera Matrix: \n{cm1}
--------------Right Camera-------------
RMS: {ret2}
Camera Matrix: \n{cm2}''')
        info("Calibrate single camera done.\n")
    
    
    def _single_calibrate_fisheye(self):
        """
        Calibrate SINGLE camera - Fisheye - TODO
        """
        pass


    def _stereo_calibrate_vanilla(self, fix_intrinsic = True):
        print(fix_intrinsic)
        """
        Calibrate STEREO camera - Vanilla
        """
        info("Calibrating STEREO camera - Vanilla...")
        objpoints = self.objpoints
        imgpointsLeft  = self.imgpointsLeft
        imgpointsRight = self.imgpointsRight

        calib_criteria = (cv2.TERM_CRITERIA_COUNT+cv2.TERM_CRITERIA_EPS, 100, 1e-5)
        if fix_intrinsic:
            flags = cv2.CALIB_FIX_INTRINSIC
        else:
            flags = cv2.CALIB_USE_INTRINSIC_GUESS
        RMS, cm1, cd1, cm2, cd2, R, T, E, F, perViewError = \
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
        
        print(f"""================ Dual Camera Calib ================
RMS: {RMS}""")
        if not fix_intrinsic:
            print(f'''----------Left Cam----------
K (Intrinsic Params): \n{cm1}
Distortion Coefficient:\n{cd1}
----------Right Cam---------
K (Intrinsic Params): \n{cm2}
Distortion Coefficient:\n{cd2}''')
        else:
            print(f"""Fixing intrinsic params.
------Extrinsic Params------
R: \n{R}
T: \n{T}""")
        info("Calibrate stereo camera done.")
        # print(perViewError)

        # update camera params
        if fix_intrinsic:
            self.camera.update_extrinsic(R, T)
        else:
            self.camera.update_intrinsic(cm1, cd1, cm2, cd2)
            self.camera.update_extrinsic(R, T)
        # save params
        npz_path = self.data_folder / "camera_model.npz"
        self.camera.save_model(npz_path)


    def _stereo_calibrate_fisheye(self):
        """
        Calibrate STEREO camera - Fisheye - TODO
        """
        pass


if __name__ == "__main__":
    CCD = 'IMX477'
    fisheye = False
    operation_folder = '0610_IMX477_infinity_still'

    camera = CameraModel(CCD, fisheye)
    calibration = Calibrate(camera, operation_folder)
    calibration.single_calibrate()
    calibration.stereo_calibrate()
    print()
