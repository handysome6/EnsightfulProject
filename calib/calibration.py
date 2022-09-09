from logging import info
import cv2
import numpy as np
from pathlib import Path

# from showimg import imshow
from model.camera_model import CameraModel


class Calibrate():
    def __init__(self, camera, operation_folder, CHECKERBOARD=(8, 11), square_size=25) -> None:
        self.camera = camera

        # folder Path object
        self.operation_folder = operation_folder
        self.scenes_folder = self.operation_folder / 'scenes'
        self.data_folder = self.operation_folder / 'calibration_data'
        self.camera_folder = self.operation_folder / 'camera_model'
        self.total_photos = len(sorted(self.scenes_folder.iterdir()))
        
        # init objp points cooord in single image
        self.objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1],3), np.float32)
        self.objp[:,:2] = np.mgrid[0:CHECKERBOARD[0],0:CHECKERBOARD[1]].T.reshape(-1,2)
        self.objp *= square_size         # stereoCalibrate() export R and T in this scale

        self.obj_points = None
        self.img_points_left = None
        self.img_points_right = None

        return 
        ############# Filter outliers ###############
        outliers_id = []#1, 30,31,32]       # result of perViewError <- stereoCalibrateExtended()
        inliers =  [True if id not in outliers_id 
                    else False
                    for id in range(self.total_photos)]
        obj_points = obj_points[inliers]
        img_points_left  = img_points_left[inliers]
        img_points_right = img_points_right[inliers]


    def calibrate_left_right(self, left_view_path = None, right_view_path = None):
        """
        Calibrate left and right camera intrinsic params.
        """
        if left_view_path is not None and right_view_path is not None:
            info("Using single view images to calib intrinsic")
            # seperate image points
            img_points_left = np.load(left_view_path)['corners']
            img_points_right = np.load(right_view_path)['corners']

            # seperate obj points
            left_num = img_points_left.shape[0]
            right_num = img_points_right.shape[0]
            objp = np.expand_dims(self.objp, axis=0)
            obj_points_left = np.repeat(objp, left_num, axis=0)
            obj_points_right = np.repeat(objp, right_num, axis=0)

            # seperate calibration
            rms1, cm1, cd1 = self._calibrate_single_swticher(obj_points_left, img_points_left, cam_num=0)
            rms2, cm2, cd2 = self._calibrate_single_swticher(obj_points_right, img_points_right, cam_num=1)

        else:
            info("Using sbs images to calib intrinsic")
            # load sbs points data
            npz_path = self.data_folder / "chessboard.npz"
            self.load_sbs_points(npz_path)
            rms1, cm1, cd1 = self._calibrate_single_swticher(self.obj_points, self.img_points_left, cam_num=0)
            rms2, cm2, cd2 = self._calibrate_single_swticher(self.obj_points, self.img_points_right, cam_num=1)
        
        self.camera.update_intrinsic(cm1,cd1,cm2,cd2)
        print(f'''=============== Single Camera Calib ===============
--------------Left Camera---------------
RMS: {rms1}
Camera Matrix: \n{cm1}
Camera Distortion: \n{cd1}
--------------Right Camera-------------
RMS: {rms2}
Camera Matrix: \n{cm2}
Camera Distortion: \n{cd2}''')
            
        info("Calibrate left and right camera intrinsic done.\n")


    def stereo_calibrate(self, **args):
        """
        Calibrate DUAL camera.
        Switcher function. 
        """
        if self.camera.is_fisheye:
            self._stereo_calibrate_fisheye(**args)
        else:
            self._stereo_calibrate_vanilla(**args)
    

    def _calibrate_single_swticher(self, *args, **kwargs):
        """
        Switcher function, fisheye or not. 
        """
        if self.camera.is_fisheye:
            retval = self._single_calibrate_fisheye(*args, **kwargs)
        else:
            retval = self._single_calibrate_vanilla(*args, **kwargs)
        return retval


    def _single_calibrate_vanilla(self, obj_points, img_points, cam_num = 0):
        """
        Calibrate SINGLE camera - Vanilla
        """
        print(f"Calibrating camera num {cam_num} - Vanilla...", end="")
        # rvecs             -> Rotation Vectors, maps world coord to image coord
        # tvecs             -> Translation Vecs
        # init cm 
        cm = np.array(
            [[4e3, 0, 2028],
             [0, 4e3, 1520],
             [0, 0, 1]], dtype=np.float32
        )
        flags = cv2.CALIB_USE_INTRINSIC_GUESS
        calib_criteria = (cv2.TERM_CRITERIA_COUNT+cv2.TERM_CRITERIA_EPS, 100, 1e-6)
        rms, cm, cd, rvecs, tvecs, _, _, perViewErrors = cv2.calibrateCameraExtended(
                obj_points, img_points, 
                self.camera.image_size, cm, None,
                # flags=flags,
                criteria=calib_criteria
            )
        print("\t Done!")
        return rms, cm, cd
    
    
    def __filter_outliers(self, obj_points, img_points):
        """
        Back up code for further implementation
        """
        delete_index = []
        mask = np.zeros(len(perViewErrors), dtype=bool)
        filter = np.ones(len(perViewErrors), dtype=bool)
        masked_list = np.ma.array(perViewErrors, mask=mask)
        while len(delete_index) < len(obj_points) / 5:
            id = np.argmax(masked_list)
            delete_index.append(id)
            mask[id] = True
            filter[id] = False
            masked_list = np.ma.array(masked_list, mask=mask)
        print(delete_index)
        print(perViewErrors[mask])
        print("Remaining image number:", len(img_points[filter]))
        print("Filter out outliers, re-calibrating...")
        flags = None,
        calib_criteria = None
        rms, cm, cd, rvecs, tvecs, _, _, perViewErrors = cv2.calibrateCameraExtended(
                obj_points[filter], img_points[filter], 
                self.camera.image_size, cm, None,
                flags=flags,
                criteria=calib_criteria
            )
    

    def _single_calibrate_fisheye(self):
        """
        Calibrate SINGLE camera - Fisheye - TODO
        """
        pass


    def _stereo_calibrate_vanilla(self, fix_intrinsic = True, show_pve=False):
        """
        Calibrate STEREO camera - Vanilla
        """
        info("Calibrating STEREO camera - Vanilla...")
        # load sbs points data
        npz_path = self.data_folder / "chessboard.npz"
        self.load_sbs_points(npz_path)
        obj_points = self.obj_points
        img_points_left  = self.img_points_left
        img_points_right = self.img_points_right

        calib_criteria = (cv2.TERM_CRITERIA_COUNT+cv2.TERM_CRITERIA_EPS, 100, 1e-6)
        if fix_intrinsic:
            flags = cv2.CALIB_FIX_INTRINSIC
        else:
            flags = cv2.CALIB_USE_INTRINSIC_GUESS 
            # + cv2.CALIB_SAME_FOCAL_LENGTH + cv2.CALIB_ZERO_TANGENT_DIST
        RMS, cm1, cd1, cm2, cd2, R, T, E, F, perViewError = \
            cv2.stereoCalibrateExtended(
                obj_points, 
                img_points_left, img_points_right, 
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
            print(f"Fixing intrinsic params.")
        print(f"""------Extrinsic Params------
R: \n{R}
T: \n{T}""")
        info("Calibrate stereo camera done.")
        if show_pve:
            print(perViewError)

        # update camera params
        if fix_intrinsic:
            self.camera.update_extrinsic(R, T)
        else:
            self.camera.update_intrinsic(cm1, cd1, cm2, cd2)
            self.camera.update_extrinsic(R, T)
        # save params
        json_path = self.camera_folder / "camera_model.json"
        self.camera.save_model(json_path)


    def _stereo_calibrate_fisheye(self):
        """
        Calibrate STEREO camera - Fisheye - TODO
        """
        pass


    def load_sbs_points(self, npz_path):
        """
        Load obj_points, img_points_left, img_points_right
        """
        try:
            npz_file = np.load(npz_path)
            self.obj_points = npz_file['objpoints']
            self.img_points_left = npz_file['imgpointsLeft']
            self.img_points_right = npz_file['imgpointsRight']
        except:
            raise("No chessboard data found. \nPlease preprocess images before calibration")


if __name__ == "__main__":
    CCD = 'IMX477'
    fisheye = False
    operation_folder = Path("datasets") / '0610_IMX477_infinity_still'

    camera = CameraModel(CCD, fisheye)
    calibration = Calibrate(camera, operation_folder)
    calibration.single_calibrate()
    calibration.stereo_calibrate()
    print()
