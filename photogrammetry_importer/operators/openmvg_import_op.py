import os
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from photogrammetry_importer.operators.import_op import ImportOperator
from photogrammetry_importer.properties.camera_import_properties import CameraImportProperties
from photogrammetry_importer.properties.point_import_properties import PointImportProperties
from photogrammetry_importer.properties.general_import_properties import GeneralImportProperties

from photogrammetry_importer.file_handlers.openmvg_json_file_handler import OpenMVGJSONFileHandler
from photogrammetry_importer.utility.blender_utility import add_collection


class ImportOpenMVGOperator(ImportOperator,
                            CameraImportProperties, 
                            PointImportProperties,
                            GeneralImportProperties,
                            ImportHelper):

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
 
        self.image_dp = self.get_default_image_path(
            path, self.image_dp)
        self.report({'INFO'}, 'image_dp: ' + str(self.image_dp))
        
        cameras, points = OpenMVGJSONFileHandler.parse_openmvg_file(
            path, self.image_dp, self.image_fp_type, self.suppress_distortion_warnings, self)
        
        self.report({'INFO'}, 'Number cameras: ' + str(len(cameras)))
        self.report({'INFO'}, 'Number points: ' + str(len(points)))
        
        reconstruction_collection = add_collection('Reconstruction Collection')
        self.import_photogrammetry_cameras(cameras, reconstruction_collection)
        self.import_photogrammetry_points(points, reconstruction_collection)
        self.apply_general_options()

        return {'FINISHED'}

    def invoke(self, context, event):
        addon_name = self.get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[addon_name].preferences
        self.initialize_options(import_export_prefs)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        self.draw_camera_options(layout)
        self.draw_point_options(layout)
        self.draw_general_options(layout)
