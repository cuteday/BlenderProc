from src.main.Module import Module
import bpy
import json
import os
from mathutils import Matrix, Vector, Euler
import math
import csv

from src.utility.Utility import Utility


class SuncgLoader(Module):

    def __init__(self, config):
        Module.__init__(self, config)
        self.house_path = self.config.get_string("path")
        self.suncg_dir = self.config.get_string("suncg_path", os.path.join(os.path.dirname(self.house_path), "../.."))

    def run(self):
        with open(Utility.resolve_path(self.house_path), "r") as f:
            config = json.load(f)

        self._read_model_category_mapping('suncg/ModelCategoryMapping.csv')

        house_id = config["id"]

        for level in config["levels"]:
            # Build empty level object which acts as a parent for all rooms on the level
            level_obj = bpy.data.objects.new("Level#" + level["id"], None)
            level_obj["type"] = "Level"
            level_obj["bbox"] = self._correct_bbox_frame(level["bbox"])
            bpy.context.scene.objects.link(level_obj)

            room_per_object = {}

            for node in level["nodes"]:
                # Skip invalid nodes (This is the same behavior as in the SUNCG Toolbox)
                if "valid" in node and node["valid"] == 0:
                    continue

                # Metadata is directly stored in the objects custom data
                metadata = {
                    "type": node["type"]
                }

                if "modelId" in node:
                    metadata["modelId"] = node["modelId"]

                    if node["modelId"] in self.object_fine_grained_label_map:
                        metadata["fine_grained_class"] = self.object_fine_grained_label_map[node["modelId"]]
                        metadata["category_id"] = self._get_label_id(node["modelId"])

                if "bbox" in node:
                    metadata["bbox"] = self._correct_bbox_frame(node["bbox"])

                if "transform" in node:
                    transform = Matrix([node["transform"][i*4:(i+1)*4] for i in range(4)])
                    # Transpose, as given transform matrix was col-wise, but blender expects row-wise
                    transform.transpose()
                else:
                    transform = None

                if "materials" in node:
                    material_adjustments = node["materials"]
                else:
                    material_adjustments = []

                # Lookup if the object belongs to a room
                object_id = int(node["id"].split("_")[-1])
                if object_id in room_per_object:
                    parent = room_per_object[object_id]
                else:
                    parent = level_obj

                if node["type"] == "Room":
                    self._load_room(node, metadata, material_adjustments, transform, house_id, level_obj, room_per_object)
                elif node["type"] == "Ground":
                    self._load_ground(node, metadata, material_adjustments, transform, house_id, parent)
                elif node["type"] == "Object":
                    self._load_object(node, metadata, material_adjustments, transform, parent)
                elif node["type"] == "Box":
                    self._load_box(node, material_adjustments, transform, parent)

    def _load_room(self, node, metadata, material_adjustments, transform, house_id, parent, room_per_object):
        # Build empty room object which acts as a parent for all objects inside
        room_obj = bpy.data.objects.new("Room#" + node["id"], None)
        room_obj["type"] = "Room"
        room_obj["bbox"] = self._correct_bbox_frame(node["bbox"])
        room_obj["roomTypes"] = node["roomTypes"]
        room_obj.parent = parent
        bpy.context.scene.objects.link(room_obj)
        # Store indices of all contained objects in
        if "nodeIndices" in node:
            for child_id in node["nodeIndices"]:
                room_per_object[child_id] = room_obj

        if "hideFloor" not in node or node["hideFloor"] != 1:
            metadata["type"] = "Floor"
            metadata["category_id"] = self.label_index_map["floor"]
            metadata["fine_grained_class"] = "floor"
            self._load_obj(os.path.join(self.suncg_dir, "room", house_id, node["modelId"] + "f.obj"), metadata, material_adjustments, transform, room_obj)

        if "hideCeiling" not in node or node["hideCeiling"] != 1:
            metadata["type"] = "Ceiling"
            metadata["category_id"] = self.label_index_map["ceiling"]
            metadata["fine_grained_class"] = "ceiling"
            self._load_obj(os.path.join(self.suncg_dir, "room", house_id, node["modelId"] + "c.obj"), metadata, material_adjustments, transform, room_obj)

        if "hideWalls" not in node or node["hideWalls"] != 1:
            metadata["type"] = "Wall"
            metadata["category_id"] = self.label_index_map["wall"]
            metadata["fine_grained_class"] = "wall"
            self._load_obj(os.path.join(self.suncg_dir, "room", house_id, node["modelId"] + "w.obj"), metadata, material_adjustments, transform, room_obj)

    def _load_ground(self, node, metadata, material_adjustments, transform, house_id, parent):
        metadata["type"] = "Ground"
        metadata["category_id"] = self.label_index_map["floor"]
        metadata["fine_grained_class"] = "ground"
        self._load_obj(os.path.join(self.suncg_dir, "room", house_id, node["modelId"] + "f.obj"), metadata, material_adjustments, transform, parent)

    def _load_object(self, node, metadata, material_adjustments, transform, parent):
        if "state" not in node or node["state"] == 0:
            self._load_obj(os.path.join(self.suncg_dir, "object", node["modelId"], node["modelId"] + ".obj"), metadata, material_adjustments, transform, parent)
        else:
            self._load_obj(os.path.join(self.suncg_dir, "object", node["modelId"], node["modelId"] + "_0.obj"), metadata, material_adjustments, transform, parent)

    def _correct_bbox_frame(self, bbox):
        return {
            "min": [bbox["min"][0], -bbox["min"][2], bbox["min"][1]],
            "max": [bbox["max"][0], -bbox["max"][2], bbox["max"][1]]
        }

    def _load_box(self, node, material_adjustments, transform, parent):
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        box = bpy.context.object
        box.name = "Box#" + node["id"]
        # Rotate cube to match objects loaded from .obj
        box.matrix_world *= Matrix.Rotation(math.radians(90), 4, "X")
        # Scale the cube to the required dimensions
        box.matrix_world *= Matrix.Scale(node["dimensions"][0] / 2, 4, (1.0, 0.0, 0.0)) * Matrix.Scale(node["dimensions"][1] / 2, 4, (0.0, 1.0, 0.0)) * Matrix.Scale(node["dimensions"][2] / 2, 4, (0.0, 0.0, 1.0))

        # Create UV mapping (beforehand we apply the scaling from the previous step, such that the resulting uv mapping has the correct aspect)
        bpy.ops.object.transform_apply(scale=True)
        bpy.ops.object.editmode_toggle()
        bpy.ops.uv.cube_project()
        bpy.ops.object.editmode_toggle()

        # Create an empty material which is filled in the next step
        mat = bpy.data.materials.new(name="material_0")
        mat.use_nodes = True
        box.data.materials.append(mat)

        self._transform_and_colorize_object(box, material_adjustments, transform, parent)

    def _load_obj(self, path, metadata, material_adjustments, transform=None, parent=None):
        if not os.path.exists(path):
            print("Warning: " + path + " is missing")
        else:
            bpy.ops.import_scene.obj(filepath=path)

            # Go through all imported objects
            for object in bpy.context.selected_objects:
                for key in metadata.keys():
                    object[key] = metadata[key]

                self._transform_and_colorize_object(object, material_adjustments, transform, parent)

    def _transform_and_colorize_object(self, object, material_adjustments, transform=None, parent=None):
        if parent is not None:
            object.parent = parent

        if transform is not None:
            # Apply transformation
            object.matrix_world *= transform

        for mat_slot in object.material_slots:
            mat = mat_slot.material

            index = mat.name[mat.name.find("_") + 1:]
            if "." in index:
                index = index[:index.find(".")]
            index = int(index)

            force_texture = index < len(material_adjustments) and "texture" in material_adjustments[index]
            self._recreate_material_nodes(mat, force_texture)

            if index < len(material_adjustments):
                self._adjust_material_nodes(mat, material_adjustments[index])

    def _recreate_material_nodes(self, mat, force_texture):
        """ Remove all nodes and recreate a diffuse node, optionally with texture. """
        nodes = mat.node_tree.nodes
        for node in nodes:
            nodes.remove(node)
        links = mat.node_tree.links
        has_texture = (len(mat.texture_slots) > 0 and mat.texture_slots[0] is not None)

        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        diffuse_node = nodes.new(type='ShaderNodeBsdfDiffuse')
        if has_texture or force_texture:
            uv_node = nodes.new(type='ShaderNodeTexCoord')
            image_node = nodes.new(type='ShaderNodeTexImage')

        links.new(diffuse_node.outputs[0], output_node.inputs[0])
        if has_texture or force_texture:
            links.new(image_node.outputs[0], diffuse_node.inputs[0])
            links.new(uv_node.outputs[2], image_node.inputs[0])

        diffuse_node.inputs[0].default_value[:3] = mat.diffuse_color
        if has_texture:
            image_node.image = mat.texture_slots[0].texture.image

    def _adjust_material_nodes(self, mat, adjustments):
        nodes = mat.node_tree.nodes
        diffuse_node = nodes.get("Diffuse BSDF")
        image_node = nodes.get("Image Texture")

        if "diffuse" in adjustments:
            diffuse_node.inputs[0].default_value = Utility.hex_to_rgba(adjustments["diffuse"])

        if "texture" in adjustments:
            image_path = os.path.join(self.suncg_dir, "texture", adjustments["texture"])
            image_path = Utility.resolve_path(image_path)

            if os.path.exists(image_path + ".png"):
                image_path += ".png"
            else:
                image_path += ".jpg"

            if os.path.exists(image_path):
                image_node.image = bpy.data.images.load(image_path, check_existing=True)
            else:
                print("Warning: Cannot load texture, path does not exist: " + image_path)

    def _read_model_category_mapping(self, path):       
        self.labels = set()     
        self.windows = []       
        self.object_label_map = {}      
        self.object_fine_grained_label_map = {}     
        self.label_index_map = {}       
        
        with open(Utility.resolve_path(path), 'r') as csvfile:      
            reader = csv.DictReader(csvfile)        
            for row in reader:      
                self.labels.add(row["nyuv2_40class"])       
                self.object_label_map[row["model_id"]] = row["nyuv2_40class"]       
                self.object_fine_grained_label_map[row["model_id"]] = row["fine_grained_class"]     
        
        self.labels = sorted(list(self.labels))
        bpy.data.scenes["Scene"]["num_labels"] = len(self.labels)
        self.label_index_map = {self.labels[i]:i for i in range(len(self.labels))}      

    def _get_label_id(self, obj_id):        
        return self.label_index_map[self.object_label_map[obj_id]]