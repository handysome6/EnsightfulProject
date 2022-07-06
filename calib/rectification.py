import os
import cv2
import numpy as np
from tqdm import tqdm
from pathlib import Path

from utils.utils import imshow
from model.camera_model import CameraModel


class StereoRectify():
    def __init__(self, camera, operation_folder) -> None:
        """Construct rectifier.
        camera: calibrated CameraModel object
        operation_folder: Path object, folder containing 'scenes/'
        """
        self.camera = camera
        self.width = self.camera.image_size[0]
        self.height = self.camera.image_size[1]

        # folder Path object
        if operation_folder != None:
            self.operation_folder = operation_folder
            self.scenes_folder = self.operation_folder / 'scenes'
            self.rectify_folder = self.operation_folder / 'rectified'
            self.data_folder = self.operation_folder / 'calibration_data'
            self.camera_folder = self.operation_folder / 'camera_model'
            self.total_photos = len(list(self.scenes_folder.iterdir()))


    def rectify_camera(self, roi_ratio = 0, new_image_ratio = 1):
        """
        Switch to call diff rectify method 
        roi_ratio: Determine how much black edge is preserved
                    roi_ratio = 0: None black area is preserved
                    roi_ratio = 1: all black area is preserved
        new_image_ratio: Determine the new imagesize 
        """
        # rectify parameters
        roi_ratio = roi_ratio
        newImageSize = np.array(self.camera.image_size) * new_image_ratio
        newImageSize = np.array(newImageSize, dtype=np.int32)

        if not self.camera.is_calibrated():
            print("No calib_data found. \nPlease calib camera before rectify")
            exit()
        if self.camera.is_fisheye:
            self._stereo_rectify_fisheye(roi_ratio, newImageSize)
        else:
            self._stereo_rectify_vanilla(roi_ratio, newImageSize)


    def rectify_samples(self):
        """
        Rectify sample sbs images from "operation_folder / scenes"
        Save to "operation_folder / rectified"
        """
        # mkdir if folder not exist
        self.rectify_folder.mkdir(parents=False, exist_ok=True)

        # iterate all sbs images
        scenes_imgs = list(self.scenes_folder.iterdir())
        i = 0
        for img_path in tqdm(scenes_imgs, desc="Rectifying".ljust(10)):
            i += 1
            sbs_img = cv2.imread(str(img_path))
            imgL, imgR = self.rectify_image(sbs_img)
            left_name  = f"rectify_{str(i).zfill(2)}_left.jpg"
            right_name = f"rectify_{str(i).zfill(2)}_right.jpg"
            cv2.imwrite(str(self.rectify_folder / left_name), imgL)
            cv2.imwrite(str(self.rectify_folder / right_name), imgR)
        print("Rectify images done.")


    def rectify_image(self, sbs_img):
        """ 
        Rectify single sbs image using maps
        img_path: Path object to single sbs image
        """
        if not self.camera.is_rectified():
            raise Exception("Camera not rectified.")
            exit()
        
        # split
        imgL = sbs_img [:,          0:   self.width]
        imgR = sbs_img [:, self.width: 2*self.width]
        imgL = cv2.remap(imgL, self.camera.leftMapX, self.camera.leftMapY, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        imgR = cv2.remap(imgR, self.camera.rightMapX, self.camera.rightMapY, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        return imgL, imgR


    def _stereo_rectify_vanilla(self, alpha, newImageSize):  
        """
        Compute rectify map in Vanilla approach
        """
        # calculate rectify matrices using calibration param
        R1, R2, P1, P2, Q, ROI1, ROI2 = \
            cv2.stereoRectify(
                self.camera.cm1, self.camera.cd1, 
                self.camera.cm2, self.camera.cd2, 
                self.camera.image_size, 
                self.camera.R, self.camera.T,
                alpha=alpha,
                newImageSize=newImageSize,
            )
        
        # create map for rectification
        leftMapX, leftMapY  = cv2.initUndistortRectifyMap(self.camera.cm1, self.camera.cd1, R1, P1, newImageSize, cv2.CV_16SC2)
        rightMapX, rightMapY= cv2.initUndistortRectifyMap(self.camera.cm2, self.camera.cd2, R2, P2, newImageSize, cv2.CV_16SC2)
        print("Calculate map done.")

        # save updated camera model
        self.camera.update_maps(Q, leftMapX, leftMapY, rightMapX, rightMapY)
        npz_path = self.camera_folder / "camera_model.npz"
        self.camera.save_model(npz_path)


    def _stereo_rectify_fisheye(self, alpha, newImageSize):
        """
        Compute rectify map in Fisheye approach - TODO
        """
        pass


if __name__ == "__main__":
    operation_folder = '0610_IMX477_infinity_still'

    model_path = Path("datasets") / operation_folder / "calibration_data" / "camera_model.npz"
    camera = CameraModel.load_model(model_path)

    rectifier = StereoRectify(camera, operation_folder, )
    rectifier.rectify_camera()
    rectifier.rectify_samples()
    print()