import os

import bpy

from src.writer.WriterInterface import WriterInterface

class BlenderWriter(WriterInterface):

    def __init__(self, config):
        WriterInterface.__init__(self, config)

    def run(self):
        blend_path = os.path.join(self._determine_output_dir(False), "scene.blend")
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)