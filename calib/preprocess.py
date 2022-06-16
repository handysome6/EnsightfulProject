import cv2
import numpy as np
from tqdm import tqdm
from pathlib import Path
from threading import Thread

# from showimg import imshow
from model.camera_model import CameraModel


class Preprocess():
    def __init__(self, camera, operation_folder, CHECKERBOARD=(8, 11), square_size=25) -> None:
        self.camera = camera
        self.width = self.camera.image_size[0]
        self.height = self.camera.image_size[1]
        
        # folder Path object
        self.operation_folder = Path(f'datasets/{operation_folder}')
        self.scenes_folder = self.operation_folder / 'scenes'
        self.data_folder = self.operation_folder / 'calibration_data'
        self.total_photos = len(list(self.scenes_folder.iterdir()))

        self.discard_list = []

        self.CHECKERBOARD = CHECKERBOARD
        self.square_size = square_size
        self.chessboard_flags = cv2.CALIB_CB_ADAPTIVE_THRESH+cv2.CALIB_CB_NORMALIZE_IMAGE+cv2.CALIB_CB_FAST_CHECK


    ##################################
    # Discard low quality photos
    ##################################
    def discard(self):
        # iterate through sbs image pairs
        scenes_imgs = list(self.scenes_folder.iterdir())
        for img_path in tqdm(scenes_imgs, desc="Discarding".ljust(10)):
            sbs_img = cv2.imread(str(img_path))
            # split
            imgL = sbs_img [:,          0:   self.width] 
            imgR = sbs_img [:, self.width: 2*self.width]
            grayL = cv2.cvtColor(imgL,cv2.COLOR_BGR2GRAY)
            grayR = cv2.cvtColor(imgR,cv2.COLOR_BGR2GRAY)

            # try find chess board corners
            def try_findchessboard(img):
                self.ret = False
                def _worker(img):
                    self.ret, _ = cv2.findChessboardCorners(img, self.CHECKERBOARD, flags=self.chessboard_flags)
                t = Thread(target=_worker, daemon=True, args=(img, ))
                t.start()
                t.join(5)
                return self.ret

            retL = try_findchessboard(grayL)
            retR = try_findchessboard(grayR)
            if not (retL and retR):
                print(f'\r{img_path.name}  NO')
                self.discard_list.append(img_path)
        
        # move to discard folder
        discard_folder = self.operation_folder / 'discarded'
        discard_folder.mkdir(parents=False, exist_ok=True)
        for file in self.discard_list:
            file.rename(discard_folder / file.name)

        # update total_photos number
        self.total_photos = len(list(self.scenes_folder.iterdir()))    


    ##################################
    # Rename to sbs_xx.jpg
    ##################################
    def rename(self):
        # renaming
        i = 0
        scenes_imgs = list(self.scenes_folder.iterdir())
        for file in scenes_imgs:
            i += 1
            file.rename(self.scenes_folder / f"sbs_{str(i).zfill(2)}.jpg")

    ##################################
    # Find chessboar corners
    ##################################
    def find_chessboard_corners(self):
        objpoints = []
        imgpointsLeft = []
        imgpointsRight = []

        subpix_criteria = (cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        CHECKERBOARD = self.CHECKERBOARD

        objp = np.zeros((CHECKERBOARD[0]*CHECKERBOARD[1],3), np.float32)
        objp[:,:2] = np.mgrid[0:CHECKERBOARD[0],0:CHECKERBOARD[1]].T.reshape(-1,2)
        objp *= self.square_size         # stereoCalibrate() export R and T in this scale

        # iterate through sbs images
        scenes_imgs = list(self.scenes_folder.iterdir())
        for img_path in tqdm(scenes_imgs, desc="Finding".ljust(10)):
            sbs_img = cv2.imread(str(img_path))
            # split
            imgL = sbs_img [:,          0:   self.width] 
            imgR = sbs_img [:, self.width: 2*self.width]
            grayL = cv2.cvtColor(imgL,cv2.COLOR_BGR2GRAY)
            grayR = cv2.cvtColor(imgR,cv2.COLOR_BGR2GRAY)

            # Find the chessboard corners
            retL, cornersL = cv2.findChessboardCorners(grayL, CHECKERBOARD, flags=self.chessboard_flags)
            retR, cornersR = cv2.findChessboardCorners(grayR, CHECKERBOARD, flags=self.chessboard_flags)

            # Refine corners and add to array for processing
            if retL and retR :
                cv2.cornerSubPix(grayL,cornersL,(11,11),(-1,-1),subpix_criteria)
                cv2.cornerSubPix(grayR,cornersR,(11,11),(-1,-1),subpix_criteria)
                objpoints.append(objp)
                imgpointsLeft.append(cornersL)
                imgpointsRight.append(cornersR)

        # save corner coordinates
        self.data_folder.mkdir(parents=False, exist_ok=True)
        save_path = self.data_folder / "chessboard.npz"
        np.savez(save_path,
            objpoints = objpoints, 
            imgpointsLeft = imgpointsLeft, 
            imgpointsRight = imgpointsRight,)
        print("Saved chessboard corners to", save_path)




if __name__ == "__main__":
    CCD = 'IMX477'
    fisheye = False
    operation_folder = '0610_IMX477_infinity_still'
    rows = 8
    columns = 11
    CHECKERBOARD = (rows,columns)
    square_size = 25

    camera = CameraModel(CCD, fisheye)
    preprocess = Preprocess(camera, operation_folder)
    preprocess.discard()
    preprocess.rename()
    preprocess.find_chessboard_corners()
    print()
