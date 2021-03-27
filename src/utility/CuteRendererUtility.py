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
            stored as `.png` file, as material roughness are loaded using `.png` as well...

            Edit 1: 
                it seems that some shader aov operations can only do on UI mode,
                the last solution is to replace all base color values with roughness maps
                then output the diffuse color pass.

            Edit 2:
                the add_aov scripting is avaliable
                maybe we can link it using its default name 'AOV' and type 'COLOR'
                let's just try it!

            Update:
                the method in Edit #2 worked!
                and, since the registered AOV name could not duplicate
                only one property could be output through AOV 
        """
        bpy.context.scene.render.use_compositing = True
        bpy.context.scene.use_nodes = True
        render_layer_tree = bpy.context.scene.node_tree
        render_layer_links = render_layer_tree.links

        bpy.ops.cycles.add_aov()

        for mat in bpy.data.materials:
            if not mat.use_nodes:
                continue
            material_tree = mat.node_tree
        # for object in [obj for obj in bpy.data.objects if hasattr(obj.data, 'materials')]:
        #     if len(object.data.materials) > 1:
        #         raise Exception("enable_roughness_output: the object %s has more than one material?! Ov0" % (object.name))
        #    material_tree = object.data.materials[0].node_tree
            material_nodes = material_tree.nodes
            material_links = material_tree.links

            aov_output = material_nodes.new('ShaderNodeOutputAOV')
            aov_output.name = 'AOV'

            principled_bsdf = material_nodes.get('Principled BSDF')
            assert principled_bsdf is not None
            
            roughness_socket = principled_bsdf.inputs['Roughness']
            if not roughness_socket.links:
                default_roughness = roughness_socket.default_value
                aov_output.inputs['Color'].default_value = [ 
                    default_roughness, default_roughness, default_roughness, 1.0]
            else:
                if len(roughness_socket.links) > 1:
                    raise Exception("enable_roughness_output: the roughness of bsdf node has more than one input?! Ov0")

                roughness_node_output = roughness_socket.links[0].from_socket
                material_links.new(roughness_node_output, aov_output.inputs['Color'])

        render_layer_node = Utility.get_the_one_node_with_type(render_layer_tree.nodes, 'CompositorNodeRLayers')
        final_output = render_layer_node.outputs['AOV']
        
        output_file = render_layer_tree.nodes.new('CompositorNodeOutputFile')
        output_file.base_path = output_dir
        output_file.format.file_format = "PNG"
        output_file.file_slots.values()[0].path = file_prefix
        render_layer_links.new(final_output, output_file.inputs['Image']) 

        Utility.add_output_entry({
            "key": output_key,
            "path": os.path.join(output_dir, file_prefix) + "%04d" + ".png",
            "version": "2.0.0"
        })

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
            elif p == "GlossInd":
                bpy.context.view_layer.use_pass_glossy_indirect = True
            else:
                raise Exception("The specified pass {} is not supported in light passes!" % (p))
            
            render_layer_node = Utility.get_the_one_node_with_type(tree.nodes, 'CompositorNodeRLayers')
            final_output = render_layer_node.outputs[p]

            output_file = tree.nodes.new('CompositorNodeOutputFile')
            output_file.base_path = output_dir
            output_file.format.file_format = "PNG"
            file_name = "{}{}_".format(file_prefix, p.lower())
            output_file.file_slots.values()[0].path = file_name
            links.new(final_output, output_file.inputs['Image'])

            Utility.add_output_entry({
                "key": "%s_%s" % (output_key, p.lower()),
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

    @staticmethod
    def enable_noisy_image_output(output_dir, file_prefix="noisy_", output_key="noisy"):
        bpy.context.scene.render.use_compositing = True
        bpy.context.scene.use_nodes = True
        tree = bpy.context.scene.node_tree
        links = tree.links

        bpy.context.view_layer.use_pass_diffuse_color = True
        render_layer_node = Utility.get_the_one_node_with_type(tree.nodes, 'CompositorNodeRLayers')
        final_output = render_layer_node.outputs["Noisy Image"]

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
