import os
import bpy
from bpy.props import StringProperty
from bpy.props import IntProperty
from bpy_extras.io_utils import ImportHelper

from photogrammetry_importer.operators.import_op import ImportOperator
from photogrammetry_importer.properties.camera_import_properties import CameraImportProperties
from photogrammetry_importer.properties.point_import_properties import PointImportProperties
from photogrammetry_importer.properties.general_import_properties import GeneralImportProperties

from photogrammetry_importer.file_handlers.opensfm_json_file_handler import OpenSfMJSONFileHandler
from photogrammetry_importer.utility.blender_utility import add_collection


class ImportOpenSfMOperator(ImportOperator,
                            CameraImportProperties, 
                            PointImportProperties,
                            GeneralImportProperties,
                            ImportHelper):

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
 
        self.image_dp = self.get_default_image_path(
            path, self.image_dp)
        self.report({'INFO'}, 'image_dp: ' + str(self.image_dp))
        
        cameras, points = OpenSfMJSONFileHandler.parse_opensfm_file(
            path, self.image_dp, self.image_fp_type, self.suppress_distortion_warnings, self.reconstruction_number, self)
        
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
        layout.prop(self, "reconstruction_number")
        self.draw_camera_options(layout)
        self.draw_point_options(layout)
        self.draw_general_options(layout)
