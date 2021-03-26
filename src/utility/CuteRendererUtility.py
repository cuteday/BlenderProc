import os

import bpy

from src.main.GlobalStorage import GlobalStorage
from src.utility.Utility import Utility
import mathutils
import math

class CuteRendererUtility:
    

    @staticmethod
    def enable_roughness_output(output_dir, file_prefix="roughness_", output_key="roughness"):
        """
            output the roughness value of all textures
            using Shader AOV and composite passes
            stored as `.exr` file for better precision?

            Edit 1: 
                it seems that some shader aov operations can only do on UI mode,
                the last solution is to replace all base color values with roughness maps
                then output the diffuse color pass.

            Edit 2:
                the add_aov scripting is avaliable
                maybe we can link it using its default name 'AOV' and type 'COLOR'
                let's just try it!
        """
        bpy.context.scene.render.use_compositing = True
        bpy.context.scene.use_nodes = True
        render_layer_tree = bpy.context.scene.node_tree
        render_layer_links = render_layer_tree.links

        bpy.ops.cycles.add_aov()

        for object in [obj for obj in bpy.context.scene.objects if hasattr(obj.data, 'materials')]:
            if len(object.data.materials) > 1:
                raise Exception("enable_roughness_output: the object has more than one material?! Ov0")
            material_tree = object.data.materials[0]
            material_links = material_tree.links

    @staticmethod
    def enable_metalness_output(output_dir, file_prefix="metalness_", output_key="metalness"):
        raise NotImplementedError

    @staticmethod
    def enable_lighting_pass_output(output_dir, file_prefix="lighting_", output_key="lighting",
            enabled_passes=["DiffDir", "DiffInd", "GlossDir", "GlossInd"]):
        bpy.context.scene.render.use_compositing = True
        bpy.context.scene.use_nodes = True
        tree = bpy.context.scene.node_tree
        links = tree.links

        for p in enabled_passes:
            if p == "DiffDir":
                bpy.context.view_layer.use_pass_diffuse_direct = True
            elif p == "DiffInd":
                bpy.context.view_layer.use_pass_diffuse_indirect = True
            elif p == "GlossDir":
                bpy.context.view_layer.use_pass_glossy_direct = True
            elif p == "GlossIndir":
                bpy.context.view_layer.use_pass_glossy_indirect = True
            else:
                raise Exception("The specified pass {} is not supported in light passes!" % (p))
            
            render_layer_node = Utility.get_the_one_node_with_type(tree.nodes, 'CompositorNodeRLayers')
            final_output = render_layer_node.outputs[p]

            output_file = tree.nodes.new('CompositorNodeOutputFile')
            output_file.base_path = output_dir
            output_file.format.file_format = "PNG"
            file_name = "%s%s_".format(file_prefix, p.lower())
            output_file.file_slots.values()[0].path = file_name
            links.new(final_output, output_file.inputs['Image'])

            Utility.add_output_entry({
                "key": output_key,
                "path": file_name + "%04d" + ".png",
                "version": "2.0.0"
            })

    @staticmethod
    def enable_diffuse_color_output(output_dir, file_prefix="diffuse_", output_key="diffse"):
        bpy.context.scene.render.use_compositing = True
        bpy.context.scene.use_nodes = True
        tree = bpy.context.scene.node_tree
        links = tree.links

        bpy.context.view_layer.use_pass_diffuse_color = True
        render_layer_node = Utility.get_the_one_node_with_type(tree.nodes, 'CompositorNodeRLayers')
        final_output = render_layer_node.outputs["DiffCol"]

        output_file = tree.nodes.new('CompositorNodeOutputFile')
        output_file.base_path = output_dir
        output_file.format.file_format = "PNG"
        output_file.file_slots.values()[0].path = file_prefix
        links.new(final_output, output_file.inputs['Image'])
        
        Utility.add_output_entry({
            "key": output_key,
            "path": os.path.join(output_dir, file_prefix) + "%04d" + ".png",
            "version": "2.0.0"
        })