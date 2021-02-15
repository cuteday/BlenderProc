import os
import json

import bpy
import numpy as np

from src.camera.CameraInterface import CameraInterface
from src.utility.CameraUtility import CameraUtility
from src.utility.Config import Config

class CameraStateLoader(CameraInterface):
    """
    Loads camera poses from the folder path specified in configuration.
    The camera poses are generated and outputted by BlenderProc, in the form of campose%04d.npy.
    The camera intrinsics should be specified in the configuration, instead of using the camera intrinsic matrix in the campose file.
    """

    def __init__(self, config):
        CameraInterface.__init__(self, config)

    @staticmethod 
    def add_campose_from_file(file_path):
        """
        Loads a camera to world matrix in a .npy file, add it to a new frame at the end of current camera frames.
        """
        data = json.loads(np.load(file_path).item())[0]
        cam2world_matrix = data['cam2world_matrix']
        CameraUtility.add_camera_pose(cam2world_matrix, frame=None)


    def run(self):
        # set camera intrinsics in the form of blender parameters, specified in configuration,
        # if not, use default (see CameraInterface._set_cam_intrinsics).
        self._set_cam_intrinsics(bpy.context.scene.camera.data, Config(self.config.get_raw_dict("intrinsics", {})))
        
        self.path_cam_poses = self.config.get_string("path_cam_poses", "")
        if not os.path.exists(self.path_cam_poses) or not os.path.isdir(self.path_cam_poses):
            raise Exception("Specified camera poses path not exist!")
        
        print('Loading camera poses from {}'.format(self.path_cam_poses))
        if not os.path.isdir(self.path_cam_poses):
            self.add_campose_from_file(self.path_cam_poses)
        else:
            for f in sorted(os.listdir(self.path_cam_poses)):
                self.add_campose_from_file(os.path.join(self.path_cam_poses, f))
