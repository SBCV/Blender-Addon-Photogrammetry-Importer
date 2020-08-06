import os
import bpy
from bpy.props import StringProperty
from bpy.props import EnumProperty
from bpy.props import IntProperty
from bpy_extras.io_utils import ImportHelper

from photogrammetry_importer.operators.import_op import ImportOperator
from photogrammetry_importer.properties.camera_import_properties import CameraImportProperties
from photogrammetry_importer.properties.point_import_properties import PointImportProperties
from photogrammetry_importer.properties.mesh_import_properties import MeshImportProperties

from photogrammetry_importer.file_handlers.meshroom_file_handler import MeshroomFileHandler
from photogrammetry_importer.utility.blender_utility import add_collection


class ImportMeshroomOperator(   ImportOperator,
                                CameraImportProperties,
                                PointImportProperties,
                                MeshImportProperties,
                                ImportHelper):

    """Import a Meshroom MG/SfM/JSON file"""
    bl_idname = "import_scene.meshroom_sfm_json"
    bl_label = "Import Meshroom SfM/JSON/MG"
    bl_options = {'PRESET'}

    filepath: StringProperty(
        name="Meshroom JSON File Path",
        description="File path used for importing the Meshroom SfM/JSON/MG file")
    directory: StringProperty()
    filter_glob: StringProperty(default="*.sfm;*.json;*.mg", options={'HIDDEN'})

    # Structure From Motion Node
    sfm_node_items = [
        ("AUTOMATIC", "AUTOMATIC", "", 1),
        ("ConvertSfMFormatNode", "ConvertSfMFormatNode", "", 2),
        ("StructureFromMotionNode", "StructureFromMotionNode", "", 3)
        ]
    sfm_node_type: EnumProperty(
        name="Structure From Motion Node Type",
        description = "Use this property to select the node with the structure from motion results to import.", 
        items=sfm_node_items)
    sfm_node_number: IntProperty(
        name="ConvertSfMFormat Node Number",
        description = "Use this property to select the desired node." +
            "By default the node with the highest number is imported.",
        default=-1)

    # Mesh Node
    mesh_node_items = [
        ("AUTOMATIC", "AUTOMATIC", "", 1),
        ("Texturing", "Texturing", "", 2),
        ("MeshFiltering", "MeshFiltering", "", 3),
        ("Meshing", "Meshing", "", 4)
        ]
    mesh_node_type: EnumProperty(
        name="Mesh Node Type",
        description = "Use this property to select the node with the mesh results to import.", 
        items=mesh_node_items)

    mesh_node_number: IntProperty(
        name="Mesh Node Number",
        description = "Use this property to select the desired node." + 
            "By default the node with the highest number is imported.",
        default=-1)

    def execute(self, context):

        path = os.path.join(self.directory, self.filepath)
        self.report({'INFO'}, 'path: ' + str(path))

        self.image_dp = self.get_default_image_path(
            path, self.image_dp)
        self.report({'INFO'}, 'image_dp: ' + str(self.image_dp))
        
        cameras, points, mesh_fp = MeshroomFileHandler.parse_meshroom_file(
            path, self.image_dp, self.image_fp_type, self.suppress_distortion_warnings, 
            self.sfm_node_type, self.sfm_node_number, self.mesh_node_type, self.mesh_node_number, self)
        
        self.report({'INFO'}, 'Number cameras: ' + str(len(cameras)))
        self.report({'INFO'}, 'Number points: ' + str(len(points)))
        
        reconstruction_collection = add_collection('Reconstruction Collection')
        self.import_photogrammetry_cameras(cameras, reconstruction_collection)
        self.import_photogrammetry_points(points, reconstruction_collection)
        self.import_photogrammetry_mesh(mesh_fp, reconstruction_collection)

        return {'FINISHED'}

    def invoke(self, context, event):
        addon_name = self.get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[addon_name].preferences
        self.initialize_options(import_export_prefs)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        node_box = layout.box()
        node_box.prop(self, "sfm_node_type")
        node_box.prop(self, "sfm_node_number")
        node_box.prop(self, "mesh_node_type")
        node_box.prop(self, "mesh_node_number")
        self.draw_camera_options(layout)
        self.draw_point_options(layout)
        self.draw_mesh_options(layout)
