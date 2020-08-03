import os
import numpy as np
import bpy
import math

# from photogrammetry_importer.point import Point

from photogrammetry_importer.utility.blender_logging_utility import log_report
from photogrammetry_importer.utility.blender_utility import add_collection

from photogrammetry_importer.file_handlers.image_file_handler import ImageFileHandler
from photogrammetry_importer.file_handlers.colmap_file_handler import ColmapFileHandler
from photogrammetry_importer.file_handlers.meshroom_file_handler import MeshroomFileHandler
from photogrammetry_importer.file_handlers.mve_file_handler import MVEFileHandler
from photogrammetry_importer.file_handlers.nvm_file_handler import NVMFileHandler
from photogrammetry_importer.file_handlers.openmvg_json_file_handler import OpenMVGJSONFileHandler
from photogrammetry_importer.file_handlers.opensfm_json_file_handler import OpenSfMJSONFileHandler
from photogrammetry_importer.file_handlers.open3D_file_handler import Open3DFileHandler
from photogrammetry_importer.file_handlers.ply_file_handler import PLYFileHandler
from photogrammetry_importer.file_handlers.transformation_file_handler import TransformationFileHandler

from photogrammetry_importer.properties.camera_import_properties import CameraImportProperties
from photogrammetry_importer.properties.point_import_properties import PointImportProperties
from photogrammetry_importer.properties.mesh_import_properties import MeshImportProperties
from photogrammetry_importer.properties.transformation_import_properties import TransformationImportProperties

from photogrammetry_importer.types.camera import Camera

# Notes:
#   http://sinestesia.co/blog/tutorials/using-blenders-filebrowser-with-python/
#       Nice blender tutorial
#   https://blog.michelanders.nl/2014/07/inheritance-and-mixin-classes-vs_13.html
#       - The class that is actually used as operator must inherit from bpy.types.Operator and ImportHelper
#       - Properties defined in the parent class, which inherits from bpy.types.Operator and ImportHelper
#         are not considered  
# https://blender.stackexchange.com/questions/717/is-it-possible-to-print-to-the-report-window-in-the-info-view
#   The color depends on the type enum: INFO gets green, WARNING light red, and ERROR dark red

from bpy.props import (CollectionProperty,
                       StringProperty,
                       BoolProperty,
                       EnumProperty,
                       FloatProperty,
                       IntProperty
                       )

from bpy_extras.io_utils import (ImportHelper,
                                 ExportHelper,
                                 axis_conversion)

custom_property_types = [
    bpy.types.BoolProperty,
    bpy.types.IntProperty,
    bpy.types.FloatProperty,
    bpy.types.StringProperty,
    bpy.types.EnumProperty]

def is_custom_property(prop):
    return type(prop) in custom_property_types

def initialize_options(source, target):
    # Side note:
    #   "vars(my_obj)" does not work in Blender
    #   "dir(my_obj)" shows the attributes, but not the corresponding type
    #   "my_obj.rna_type.properties.items()" lists attribute names with corresponding types
    for name, prop in source.rna_type.properties.items():
        if name == 'bl_idname':
            continue
        if not is_custom_property(prop):
            continue
        if not hasattr(target, name):
            continue
        setattr(target, name, getattr(source, name))

def get_addon_name():
    return __name__.split('.')[0]

def get_default_image_path(reconstruction_fp, image_dp):
    if image_dp is None:
        return None
    elif image_dp == '':
        image_default_same_dp = os.path.dirname(reconstruction_fp)
        image_default_sub_dp = os.path.join(image_default_same_dp, 'images')
        if os.path.isdir(image_default_sub_dp):
            image_dp = image_default_sub_dp
        else:
            image_dp = image_default_same_dp
    return image_dp

class ImportColmap(CameraImportProperties, PointImportProperties, MeshImportProperties, bpy.types.Operator):
    
    """Import a Colmap model (folder with .txt/.bin) or a Colmap workspace folder with dense point clouds and meshes."""
    bl_idname = "import_scene.colmap_model"
    bl_label = "Import Colmap Model Folder"
    bl_options = {'PRESET'}

    directory : StringProperty()
    #filter_folder : BoolProperty(default=True, options={'HIDDEN'})

    def execute(self, context):

        path = self.directory
        # Remove trailing slash
        path = os.path.dirname(path)
        self.report({'INFO'}, 'path: ' + str(path))

        self.image_dp = get_default_image_path(
            path, self.image_dp)
        self.report({'INFO'}, 'image_dp: ' + str(self.image_dp))
        
        cameras, points, mesh_ifp = ColmapFileHandler.parse_colmap_folder(
            path, self.image_dp, self.image_fp_type, self.suppress_distortion_warnings, self)

        self.report({'INFO'}, 'Number cameras: ' + str(len(cameras)))
        self.report({'INFO'}, 'Number points: ' + str(len(points)))
        self.report({'INFO'}, 'Mesh file path: ' + str(mesh_ifp))

        reconstruction_collection = add_collection('Reconstruction Collection')
        self.import_photogrammetry_cameras(cameras, reconstruction_collection)
        self.import_photogrammetry_points(points, reconstruction_collection)
        self.import_photogrammetry_mesh(mesh_ifp, reconstruction_collection)

        return {'FINISHED'}

    def invoke(self, context, event):

        addon_name = get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[addon_name].preferences
        initialize_options(import_export_prefs, self)
        # See: 
        # https://blender.stackexchange.com/questions/14738/use-filemanager-to-select-directory-instead-of-file/14778
        # https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        self.draw_camera_options(layout)
        self.draw_point_options(layout)
        self.draw_mesh_options(layout)


class ImportNVM(CameraImportProperties, PointImportProperties, bpy.types.Operator, ImportHelper):
    
    """Import a VisualSfM NVM file"""
    bl_idname = "import_scene.nvm"
    bl_label = "Import NVM"
    bl_options = {'PRESET'}

    filepath: StringProperty(
        name="NVM File Path",
        description="File path used for importing the NVM file")
    directory: StringProperty()
    filter_glob: StringProperty(default="*.nvm", options={'HIDDEN'})

    def enhance_camera_with_images(self, cameras):
        # Overwrites CameraImportProperties.enhance_camera_with_images()
        cameras, success = ImageFileHandler.parse_camera_image_files(
            cameras, self.default_width, self.default_height, self)
        return cameras, success

    def execute(self, context):

        path = os.path.join(self.directory, self.filepath)
        self.report({'INFO'}, 'path: ' + str(path))

        self.image_dp = get_default_image_path(
            path, self.image_dp)
        self.report({'INFO'}, 'image_dp: ' + str(self.image_dp))

        cameras, points = NVMFileHandler.parse_nvm_file(
            path, self.image_dp, self.image_fp_type, self.suppress_distortion_warnings, self)
        self.report({'INFO'}, 'Number cameras: ' + str(len(cameras)))
        self.report({'INFO'}, 'Number points: ' + str(len(points)))
        
        reconstruction_collection = add_collection('Reconstruction Collection')
        self.import_photogrammetry_cameras(cameras, reconstruction_collection)
        self.import_photogrammetry_points(points, reconstruction_collection)

        return {'FINISHED'}

    def invoke(self, context, event):
        addon_name = get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[addon_name].preferences
        initialize_options(import_export_prefs, self)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        self.draw_camera_options(layout, draw_size_and_pp=True)
        self.draw_point_options(layout)

    
class ImportOpenMVG(CameraImportProperties, PointImportProperties, bpy.types.Operator, ImportHelper):

    """Import an OpenMVG JSON file"""
    bl_idname = "import_scene.openmvg_json"
    bl_label = "Import OpenMVG JSON"
    bl_options = {'PRESET'}

    filepath: StringProperty(
        name="OpenMVG JSON File Path",
        description="File path used for importing the OpenMVG JSON file")
    directory: StringProperty()
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    def execute(self, context):

        path = os.path.join(self.directory, self.filepath)
        self.report({'INFO'}, 'path: ' + str(path))
 
        self.image_dp = get_default_image_path(
            path, self.image_dp)
        self.report({'INFO'}, 'image_dp: ' + str(self.image_dp))
        
        cameras, points = OpenMVGJSONFileHandler.parse_openmvg_file(
            path, self.image_dp, self.image_fp_type, self.suppress_distortion_warnings, self)
        
        self.report({'INFO'}, 'Number cameras: ' + str(len(cameras)))
        self.report({'INFO'}, 'Number points: ' + str(len(points)))
        
        reconstruction_collection = add_collection('Reconstruction Collection')
        self.import_photogrammetry_cameras(cameras, reconstruction_collection)
        self.import_photogrammetry_points(points, reconstruction_collection)

        return {'FINISHED'}

    def invoke(self, context, event):
        addon_name = get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[addon_name].preferences
        initialize_options(import_export_prefs, self)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        self.draw_camera_options(layout)
        self.draw_point_options(layout)


class ImportOpenSfM(CameraImportProperties, PointImportProperties, bpy.types.Operator, ImportHelper):

    """Import an OpenSfM JSON file"""
    bl_idname = "import_scene.opensfm_json"
    bl_label = "Import OpenSfM JSON"
    bl_options = {'PRESET'}

    filepath: StringProperty(
        name="OpenSfM JSON File Path",
        description="File path used for importing the OpenSfM JSON file")
    directory: StringProperty()
    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})

    reconstruction_number: IntProperty(
        name="Reconstruction Number",
        description = "If the input file contains multiple reconstructions, use this property to select the desired reconstruction.", 
        default=0)

    def execute(self, context):

        path = os.path.join(self.directory, self.filepath)
        self.report({'INFO'}, 'path: ' + str(path))
 
        self.image_dp = get_default_image_path(
            path, self.image_dp)
        self.report({'INFO'}, 'image_dp: ' + str(self.image_dp))
        
        cameras, points = OpenSfMJSONFileHandler.parse_opensfm_file(
            path, self.image_dp, self.image_fp_type, self.suppress_distortion_warnings, self.reconstruction_number, self)
        
        self.report({'INFO'}, 'Number cameras: ' + str(len(cameras)))
        self.report({'INFO'}, 'Number points: ' + str(len(points)))
        
        reconstruction_collection = add_collection('Reconstruction Collection')
        self.import_photogrammetry_cameras(cameras, reconstruction_collection)
        self.import_photogrammetry_points(points, reconstruction_collection)

        return {'FINISHED'}

    def invoke(self, context, event):
        addon_name = get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[addon_name].preferences
        initialize_options(import_export_prefs, self)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "reconstruction_number")
        self.draw_camera_options(layout)
        self.draw_point_options(layout)


class ImportMeshroom(CameraImportProperties, PointImportProperties, MeshImportProperties, bpy.types.Operator, ImportHelper):

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

        self.image_dp = get_default_image_path(
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
        addon_name = get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[addon_name].preferences
        initialize_options(import_export_prefs, self)
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


class ImportMVE(CameraImportProperties, PointImportProperties, bpy.types.Operator):
    
    """Import a Multi-View Environment reconstruction folder."""
    bl_idname = "import_scene.mve_folder"
    bl_label = "Import MVE Folder"
    bl_options = {'PRESET'}

    directory : StringProperty()

    def execute(self, context):

        path = self.directory
        # Remove trailing slash
        path = os.path.dirname(path)
        self.report({'INFO'}, 'path: ' + str(path))
        
        cameras, points = MVEFileHandler.parse_mve_workspace(
            path, self.suppress_distortion_warnings, self)

        self.report({'INFO'}, 'Number cameras: ' + str(len(cameras)))
        self.report({'INFO'}, 'Number points: ' + str(len(points)))

        reconstruction_collection = add_collection('Reconstruction Collection')
        self.import_photogrammetry_cameras(cameras, reconstruction_collection)
        self.import_photogrammetry_points(points, reconstruction_collection)

        return {'FINISHED'}

    def invoke(self, context, event):

        addon_name = get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[addon_name].preferences
        initialize_options(import_export_prefs, self)
        # See: 
        # https://blender.stackexchange.com/questions/14738/use-filemanager-to-select-directory-instead-of-file/14778
        # https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        self.draw_camera_options(layout, draw_image_fp=False)
        self.draw_point_options(layout)


class ImportOpen3D(CameraImportProperties, PointImportProperties, bpy.types.Operator, ImportHelper):

    """Import an Open3D LOG/JSON file"""
    bl_idname = "import_scene.open3d_log_json"
    bl_label = "Import Open3D LOG/JSON"
    bl_options = {'PRESET'}

    filepath: StringProperty(
        name="Open3D LOG/JSON File Path",
        description="File path used for importing the Open3D LOG/JSON file")
    directory: StringProperty()
    filter_glob: StringProperty(default="*.log;*.json", options={'HIDDEN'})

    def enhance_camera_with_intrinsics(self, cameras):

        intrinsic_missing = False
        for cam in cameras:
            if not cam.has_intrinsics():
                intrinsic_missing = True
                break

        if not intrinsic_missing:
            self.report({'INFO'}, 'Using intrinsics from file (.json).')
            return cameras, True
        else:
            self.report({'INFO'}, 'Using intrinsics from user options, since not present in the reconstruction file (.log).')
            if math.isnan(self.default_focal_length):
                self.report({'ERROR'}, 'User must provide the focal length using the import options.')
                return [], False 

            if math.isnan(self.default_pp_x) or math.isnan(self.default_pp_y):
                self.report({'WARNING'}, 'Setting the principal point to the image center.')

            for cam in cameras:
                if math.isnan(self.default_pp_x) or math.isnan(self.default_pp_y):
                    assert cam.width is not None    # If no images are provided, the user must provide a default principal point
                    assert cam.height is not None   # If no images are provided, the user must provide a default principal point
                    default_cx = cam.width / 2.0
                    default_cy = cam.height / 2.0
                else:
                    default_cx = self.default_pp_x
                    default_cy = self.default_pp_y
                
                intrinsics = Camera.compute_calibration_mat(
                    focal_length=self.default_focal_length, cx=default_cx, cy=default_cy)
                cam.set_calibration_mat(intrinsics)
            return cameras, True

    def enhance_camera_with_images(self, cameras):
        # Overwrites CameraImportProperties.enhance_camera_with_images()
        cameras, success = ImageFileHandler.parse_camera_image_files(
            cameras, self.default_width, self.default_height, self)
        return cameras, success

    def execute(self, context):

        path = os.path.join(self.directory, self.filepath)
        self.report({'INFO'}, 'path: ' + str(path))

        self.image_dp = get_default_image_path(
            path, self.image_dp)
        self.report({'INFO'}, 'image_dp: ' + str(self.image_dp))
        
        cameras = Open3DFileHandler.parse_open3d_file(
            path, self.image_dp, self.image_fp_type, self)
        
        self.report({'INFO'}, 'Number cameras: ' + str(len(cameras)))
        
        reconstruction_collection = add_collection('Reconstruction Collection')
        self.import_photogrammetry_cameras(cameras, reconstruction_collection)

        return {'FINISHED'}

    def invoke(self, context, event):
        addon_name = get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[addon_name].preferences
        initialize_options(import_export_prefs, self)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        self.draw_camera_options(layout, draw_size_and_pp=True, draw_focal_length=True)

class ImportPLY(PointImportProperties, TransformationImportProperties, bpy.types.Operator, ImportHelper):

    """Import a PLY file as point cloud"""
    bl_idname = "import_scene.ply"
    bl_label = "Import PLY"
    bl_options = {'PRESET'}

    filepath: StringProperty(
        name="PLY File Path",
        description="File path used for importing the PLY file")
    directory: StringProperty()
    filter_glob: StringProperty(default="*.ply", options={'HIDDEN'})

    def execute(self, context):
        path = os.path.join(self.directory, self.filepath)
        self.report({'INFO'}, 'path: ' + str(path))

        points = PLYFileHandler.parse_ply_file(path)
        self.report({'INFO'}, 'Number points: ' + str(len(points)))

        transformations_sorted = TransformationFileHandler.parse_transformation_folder(
            self.path_to_transformations, self)

        reconstruction_collection = add_collection('Reconstruction Collection')
        self.import_photogrammetry_points(points, reconstruction_collection, transformations_sorted)

        return {'FINISHED'}

    def invoke(self, context, event):
        addon_name = get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[addon_name].preferences
        initialize_options(import_export_prefs, self)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        self.draw_point_options(layout)
        self.draw_transformation_options(layout)
