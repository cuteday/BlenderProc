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
            stored as `.png` file, as material roughness are loaded using `.png` as well,
                using OPEN_EXR format will be unnecessary

            Edit 1: 
                it seems that some shader aov operations can only do on UI mode,
                the last solution is to replace all base color values with roughness maps
                then output the diffuse color pass.

            Edit 2:
                the add_aov scripting is avaliable
                maybe we can link it using its default name 'AOV' and type 'COLOR'
                let's just try it!

            Edit 3:
                the method in Edit #2 worked!
                and, since the registered AOV name could not duplicate
                only one property could be output through AOV 
            
            Edit 4:
                The path of aov is in bpy.context.scene.view_layers['View Layer'].cycles.aovs

        """
        bpy.context.scene.render.use_compositing = True
        bpy.context.scene.use_nodes = True
        render_layer_tree = bpy.context.scene.node_tree
        render_layer_links = render_layer_tree.links

        bpy.ops.cycles.add_aov()
        bpy.context.view_layer.cycles.aovs[-1].name = 'roughness'
        bpy.context.view_layer.cycles.aovs[-1].type = 'COLOR'

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
            aov_output.name = 'roughness'

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
        final_output = render_layer_node.outputs['roughness']
        
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
            elif p == "DiffCol":
                bpy.context.view_layer.use_pass_diffuse_color = True
            elif p == "GlossDir":
                bpy.context.view_layer.use_pass_glossy_direct = True
            elif p == "GlossInd":
                bpy.context.view_layer.use_pass_glossy_indirect = True
            elif p == "GlossCol":
                bpy.context.view_layer.use_pass_glossy_color = True
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
                "path": os.path.join(output_dir, file_name) + "%04d" + ".png",
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

        bpy.context.view_layer.cycles.denoising_store_passes = True
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

    @staticmethod
    def enable_point_light(base_light_energy = 120):
        """
            this randomly puts point light sources slightly below the ceiling
            
            Edit #1: 
                at the [center] of the ceiling, where center is the center of ceiling's AABB
            
            Edit #2: 
                now we try to optimize the light settings
                by putting a point light at the center of a triangle, every 2 triangles.
                The energy of this point light is dependent to the triangle's area.
                When there's odd number of triangles inside a ceiling, the last triangle will always have a point light.
        """

        def determine_light_energy(area,
                base_energy=50.0, base_area=10.0, area_factor=4.0, clamp_min=30.0, clamp_max=150.0):
            """ Heuristicly determines the energy of a light base on room area """
            augment_energy = area_factor * (area - base_area)
            energy = base_energy + augment_energy
            energy = min(max(clamp_min, energy), clamp_max)
            return energy

        ceilings = [obj for obj in bpy.data.objects if "ceiling" in obj.name.lower()]
        if len(ceilings) == 0:
            raise Exception('Adding point lights: No ceilings detected, no light sources added')

        for iceiling, ceiling in enumerate(ceilings):

            triangles = ceiling.data.polygons
            for iface, face in enumerate(triangles):
                if iface % 3 != 0:  # a point light for 2 triangle faces
                    continue
                area = face.area
                center = face.center
                if iface < len(triangles) - 1:
                    area += triangles[iface + 1].area
                    # center = (center + triangles[iface + 1].center) / 2
                
                bpy.ops.object.light_add(type='POINT', location=(center.x, center.y, center.z-0.1))
                light = bpy.context.object.data
                light.energy = determine_light_energy(area, base_light_energy)
                # If we want to render direct lighting with EEVEE + shadow mapping, this parameters should be carefully tuned
                light.use_shadow = False
                light.shadow_buffer_clip_start = 0.60
                light.shadow_buffer_bias = 0.20

            # xs = [v.co.x for v in ceiling.data.vertices]
            # ys = [v.co.y for v in ceiling.data.vertices]
            # zs = [v.co.z for v in ceiling.data.vertices]
            # x_min, x_max = min(xs), max(xs)
            # y_min, y_max = min(ys), max(ys)
            # x_center = (x_max + x_min) / 2
            # y_center = (y_max + y_min) / 2
            # z_center = min(zs) - 0.20
            # area = (x_max - x_min) * (y_max - y_min)

            # bpy.ops.object.light_add(type='POINT', location=(x_center, y_center, z_center))
            # light = bpy.context.object.data
            # light.energy = determine_light_energy(area, base_light_energy)
            # # If we want to render direct lighting with EEVEE + shadow mapping, this parameters should be carefully tuned
            # light.use_shadow = False
            # light.shadow_buffer_clip_start = 0.60
            # light.shadow_buffer_bias = 0.20
            