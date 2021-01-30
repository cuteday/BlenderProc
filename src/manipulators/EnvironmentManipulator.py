import bpy

from src.main.Module import Module
from src.utility.BlenderUtility import get_all_mesh_objects


class EnvironmentManipulator(Module):

    def __init__(self, config):
        Module.__init__(self, config)
        
    def run(self):
        pass