import os

import bpy

from src.main.GlobalStorage import GlobalStorage
from src.utility.Utility import Utility
import mathutils
import math

class CuteRendererUtility:

    @staticmethod
    def enable_roughness_output(output_dir, file_prefix="roughness_", output_key="roughness"):
        raise NotImplementedError

    @staticmethod
    def enable_metalness_output(output_dir, file_prefix="metalness_", output_key="metalness"):
        raise NotImplementedError

    @staticmethod
    def enable_diffuse_color_output(output_dir, file_prefix="diffuse_", output_key="diffse"):
        bpy.context.scene.render.use_compositing = True
        bpy.context.scene.use_nodes = True
        tree = bpy.context.scene.node_tree
        links = tree.links
        render_layer_node = Utility.get_the_one_node_with_type(tree.nodes, 'CompositorNodeRLayers')
        final_output = render_layer_node.outputs["DiffCol"]

        bpy.context.view_layer.use_pass_diffuse_color = True
        output_file = tree.nodes.new('CompositorNodeOutputFile')
        output_file.base_path = output_dir
        output_file.format.file_format = "PNG"
        output_file.file_slots.values()[0].path = file_prefix

        links.new(final_output, output_file.inputs['Image'])
        
        Utility.add_output_entry({
            "key": output_key,
            "path": os.path.join(output_dir, file_prefix) + "%04d" + ".exr",
            "version": "2.0.0"
        })