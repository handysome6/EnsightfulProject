from logging import info
import cv2
import numpy as np
from tqdm import tqdm
from pathlib import Path
from threading import Thread

# from showimg import imshow
from model.camera_model import CameraModel


class Preprocess():
    def __init__(self, camera, operation_folder, CHECKERBOARD=(8, 11), square_size=25) -> None:
        """
        Initialize preprocesser with bare camera model, operattion folder
        """
        self.camera = camera
        self.width = self.camera.image_size[0]
        self.height = self.camera.image_size[1]
        
        # folder Path object
        self.operation_folder = operation_folder
        assert self.operation_folder.is_dir()
        self.scenes_folder = self.operation_folder / 'scenes'
        self.data_folder = self.operation_folder / 'calibration_data'
        self.discard_folder = self.operation_folder / 'discarded'

        # find chessboard corners params
        self.CHECKERBOARD = CHECKERBOARD
        self.chessboard_flags = cv2.CALIB_CB_ADAPTIVE_THRESH+cv2.CALIB_CB_NORMALIZE_IMAGE+cv2.CALIB_CB_FAST_CHECK

        # save params, sub pixel params
        self.objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1],3), np.float32)
        self.objp[:,:2] = np.mgrid[0:CHECKERBOARD[0],0:CHECKERBOARD[1]].T.reshape(-1,2)
        self.objp *= square_size         # stereoCalibrate() export R and T in this scale
        self.objpoints = []
        self.imgpointsLeft = []
        self.imgpointsRight = []
        self.subpix_criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)


    def preprocess_sbs(self):
        """
        Preprocess Side-By-Side images for stereo calibration.
        For all sbs images:
        1. Split
        2. Try find chessboard corners for L and R
        3. Discard timeout sbs images
        4. Save data and rename photos
        """
        scenes_imgs = sorted(self.scenes_folder.iterdir())
        for img_path in tqdm(scenes_imgs, desc="Discarding sbs"):
            sbs_img = cv2.imread(str(img_path))
            # 1. Split
            imgL = sbs_img [:,          0:   self.width] 
            imgR = sbs_img [:, self.width: 2*self.width]
            grayL = cv2.cvtColor(imgL, cv2.COLOR_BGR2GRAY)
            grayR = cv2.cvtColor(imgR, cv2.COLOR_BGR2GRAY)
            # 2. Try find chessboard corners for L/R
            retL, cornersL = self._try_find_chessboard(grayL)
            retR, cornersR = self._try_find_chessboard(grayR)
            if not (retL and retR):
                # 3. Discard timeout sbs images
                info(f'Discarded {img_path.name}')
                self.discard_folder.mkdir(parents=False, exist_ok=True)
                img_path.rename(self.discard_folder / img_path.name)
            else:
                cv2.cornerSubPix(grayL,cornersL,(11,11),(-1,-1), self.subpix_criteria)
                cv2.cornerSubPix(grayR,cornersR,(11,11),(-1,-1), self.subpix_criteria)
                self.objpoints.append(self.objp)
                self.imgpointsLeft.append(cornersL)
                self.imgpointsRight.append(cornersR)

        # 4. Save and rename 
        self.save_chessboard_data()
        # rename 
        i = 0
        scenes_imgs = sorted(self.scenes_folder.iterdir())
        for file in scenes_imgs:
            i += 1
            file.rename(self.scenes_folder / f"sbs_{str(i).zfill(2)}.jpg")


    def preprocess_single(self, input_folder, output_path):
        """
        Preprocess single L/R image for calibrate intrinsic
        """
        single_view_corners = []
        single_imgs = sorted(input_folder.iterdir())
        for img_path in tqdm(single_imgs, desc=f"Discarding {input_folder.name}"):
            img = cv2.imread(str(img_path))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, corners = self._try_find_chessboard(gray)
            if not ret:
                # Delete timeout sbs images
                img_path.unlink()
            else:
                cv2.cornerSubPix(gray,corners,(11,11),(-1,-1), self.subpix_criteria)
                single_view_corners.append(corners)
        # Save corners
        np.savez(output_path,
            corners = single_view_corners)
        info(f"Saved single corners to {output_path.name}")


    def save_chessboard_data(self):
        """
        Save found chessboard corners
        """
        # save corner coordinates
        self.data_folder.mkdir(parents=False, exist_ok=True)
        save_path = self.data_folder / "chessboard.npz"
        np.savez(save_path,
            objpoints = self.objpoints, 
            imgpointsLeft = self.imgpointsLeft, 
            imgpointsRight = self.imgpointsRight,
            objp = self.objp)
        info("Saved chessboard corners to " + str(save_path))


    def _try_find_chessboard(self, img):
        """
        Try find chessboard corners.
        """
        def _worker(img, result):
            result[0],result[1] = cv2.findChessboardCorners(img, self.CHECKERBOARD, flags=self.chessboard_flags)

        result = [None, None]
        t = Thread(target=_worker, args=(img, result), daemon=True)
        t.start()
        t.join(30)
        ret, corners = result
        return ret, corners

        

if __name__ == "__main__":
    import logging
    import sys
    logFormatter = logging.Formatter("[%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    CCD = 'IMX477'
    fisheye = False
    operation_folder = '0610_IMX477_infinity_still'
    rows = 8
    columns = 11
    CHECKERBOARD = (rows,columns)
    square_size = 25

    camera = CameraModel(CCD, fisheye)
    preprocess = Preprocess(camera, operation_folder)
    preprocess.preprocess_sbs()
    print()
