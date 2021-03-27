import math
import os

import bpy
import mathutils

from src.renderer.RendererInterface import RendererInterface
from src.utility.CuteRendererUtility import CuteRendererUtility
from src.utility.RendererUtility import RendererUtility
from src.utility.Utility import Utility

class EeveeRenderer(RendererInterface):
    """
        This should be put at the end of the rendering pipeline, especially after the CYCLES renderer module
        since it changes the scene parameters and the default renderer
    """

    def __init__(self, config):
        RendererInterface.__init__(self, config)
        self._use_headlight = config.get_bool("eevee_headlight", False)
        self._headlight_power = config.get_float("headlight_power", 500.0)
        self._taa_samples = config.get_int("taa_samples", 64)
        self._render_diffuse_color = config.get_bool("render_diffuse_color", False)
        self._render_roughness = config.get_bool("render_roughness", False)
        self._render_metalness = config.get_bool("render_metalness", False)
        self._render_panorama = config.get_bool("render_panorama", False)

    def _configure_eevee(self):
        bpy.context.scene.render.engine = 'BLENDER_EEVEE'
        bpy.context.scene.eevee.taa_render_samples = self._taa_samples

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

        bpy.context.scene.render.filepath = os.path.join(output_dir, file_prefix)

        Utility.add_output_entry({
            "key": self.config.get_string("eevee_output_key", "eevee"),
            "path": os.path.join(output_dir, file_prefix + "%04d" + ".png"),
            "version": "2.0.0",
        })  

        self._render_cute()
        
        if bpy.context.scene.frame_end != bpy.context.scene.frame_start:
            bpy.context.scene.frame_end -= 1
            bpy.ops.render.render(animation=True, write_still=True)

        # revert blender context to previous state
        # bpy.ops.object.delete()   # delete the ceiling area light
        # bpy.context.scene.render.engine = 'CYCLES'


