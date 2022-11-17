import numpy as np
from pathlib import Path
from json import JSONEncoder
import json


class NumpyArrayEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return JSONEncoder.default(self, obj)


class CameraModel():
    def __init__(self, image_size, is_fisheye) -> None:
        """
        Create camera model from init state.
        """
        self.image_size = image_size
        self.is_fisheye = is_fisheye

        # init params
        self.cm1 = self.cm2 = self.cd1 = self.cd2 = None
        self.R = self.T = None
        
    @classmethod
    def load_model(cls, cam_path) -> None:
        """
        Create camera model from a saved file.
        """
        # dummy camera instance
        camera = CameraModel('IMX477', False)
        print(f"Loading camera model at {cam_path}")

        if Path(cam_path).suffix == ".json":
            with open(cam_path, "r") as read_file:
                decodedArray = json.load(read_file)
                # make sure camera info exist, else raise Errors
                try:
                    camera.image_size = np.asarray(decodedArray["image_size"])
                    camera.is_fisheye = np.asarray(decodedArray['is_fisheye'])
                except:
                    raise Exception(f"No camera info found at {cam_path}")
                
                # modify dummy camera 
                try:
                    camera.cm1 = np.asarray(decodedArray['cm1'])
                    camera.cd1 = np.asarray(decodedArray['cd1'])
                    camera.cm2 = np.asarray(decodedArray['cm2'])
                    camera.cd2 = np.asarray(decodedArray['cd2'])
                    camera.R = np.asarray(decodedArray['R'])
                    camera.T = np.asarray(decodedArray['T'])
                except: # if encounter None object, then no assignment
                    pass
        else:
            # make sure camera info exist, else raise Errors
            params = np.load(cam_path)
            try:
                camera.image_size = params['image_size']
                camera.is_fisheye = params['is_fisheye']
            except:
                raise Exception(f"No camera info found at {cam_path}")
            
            # modify dummy camera 
            try:
                camera.cm1 = params['cm1']
                camera.cd1 = params['cd1']
                camera.cm2 = params['cm2']
                camera.cd2 = params['cd2']
                camera.R = params['R']
                camera.T = params['T']
            except: # if encounter None object, then no assignment
                pass

        print(camera)
        return camera


    def save_model(self, json_path):
        """
        Save this model to Path.
        """
        print(f"Saving camera model to {json_path}")
        # mkdir if folder not exist
        json_path.parent.mkdir(parents=True, exist_ok=True)

        # Serialization
        json_array = {"image_size": self.image_size, 
                     "is_fisheye": self.is_fisheye, 
                     "cm1": self.cm1, 
                     "cd1": self.cd1, 
                     "cm2": self.cm2, 
                     "cd2": self.cd2, 
                     "R": self.R, 
                     "T": self.T, 
                     }
        print("serialize NumPy array into JSON and write into a file")
        with open(json_path, "w") as write_file:
            json.dump(json_array, write_file, cls=NumpyArrayEncoder)
        print("Done writing serialized NumPy array into file")


    def is_calibrated(self):
        """
        Check if this model is calibrated.
        """
        if  self.cm1 is None or self.cd1 is None or self.cm2 is None or self.cd2 is None or \
            self.R is None or self.T is None:
            return False
        else:
            return True

    def update_intrinsic(self, cm1, cd1, cm2, cd2):
        """
        Update intrinsic parameters
        """
        self.cm1 = cm1
        self.cd1 = cd1
        self.cm2 = cm2
        self.cd2 = cd2

    def update_extrinsic(self, R, T):
        """
        Update extrinsic parameters
        """
        self.R = R
        self.T = T


    def __str__(self) -> str:
        """
        Camera info"""
        str = f"""
image_size = {self.image_size}
is_fisheye = {self.is_fisheye}
cm1: \n {self.cm1}
cd1: \n {self.cd1}
cm2: \n {self.cm2}
cd2: \n {self.cd2}
R: \n {self.R}
T: \n {self.T}"""
        return str
