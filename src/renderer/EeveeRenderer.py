import math
import os

import bpy
import mathutils

from src.renderer.RendererInterface import RendererInterface
from src.utility.RendererUtility import RendererUtility
from src.utility.Utility import Utility

class EeveeRenderer(RendererInterface):

    def __init__(self, config):
        RendererInterface.__init__(self, config)
        self._use_headlight = config.get_bool("eevee_headlight", False)
        self._headlight_power = config.get_float("headlight_power", 450.0)

    def _configure_eevee(self):
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'

        if self._use_headlight:
            # create a headlight above all ceilings as the principle light source in the scene
            ceilings = [obj for obj in bpy.data.objects if "ceiling" in obj.name.lower()]
            
            if len(ceilings) == 0:
                raise Exception("No ceilings detected in the scene!")
            
            xs = [v.co.x for obj in ceilings for v in obj.data.vertices]
            ys = [v.co.y for obj in ceilings for v in obj.data.vertices]
            zs = [v.co.z for obj in ceilings for v in obj.data.vertices]

            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            z = max(zs)
            x = (x_max + x_min) / 2
            y = (y_max + y_min) / 2

            bpy.ops.object.light_add(type='AREA', location=(x, y, z))
            light = bpy.context.object.data
            light.shape = 'RECTANGLE'
            light.size = x_max - x_min
            light.size_y = y_max - y_min
            light.energy = self._headlight_power
            light.use_shadow = False       


    def run(self):
        self._configure_eevee()

        output_dir = self._determine_output_dir()
        file_prefix = self.config.get_string("eevee_output_file_prefix", "eevee_")
        output_key = self.config.get_string("eevee_output_key", "eevee")

        print(output_dir)
        print(file_prefix)
        bpy.context.scene.render.filepath = os.path.join(output_dir, file_prefix)

        if bpy.context.scene.frame_end != bpy.context.scene.frame_start:
            bpy.context.scene.frame_end -= 1
            bpy.ops.render.render(animation=True, write_still=True)

        # revert blender context to previous state
        # bpy.ops.object.delete()
        # bpy.context.scene.render.engine = 'CYCLES'

        if output_key is not None:
            Utility.add_output_entry({
                "key": output_key,
                "path": os.path.join(output_dir, file_prefix + "%04d" + ".png"),
                "version": "2.0.0",
            })  
