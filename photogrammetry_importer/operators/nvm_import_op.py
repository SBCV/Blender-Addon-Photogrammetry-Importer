import os
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from photogrammetry_importer.operators.import_op import ImportOperator
from photogrammetry_importer.properties.camera_import_properties import CameraImportProperties
from photogrammetry_importer.properties.point_import_properties import PointImportProperties
from photogrammetry_importer.properties.general_import_properties import GeneralImportProperties

from photogrammetry_importer.file_handlers.image_file_handler import ImageFileHandler
from photogrammetry_importer.file_handlers.nvm_file_handler import NVMFileHandler
from photogrammetry_importer.utility.blender_utility import add_collection
from photogrammetry_importer.utility.blender_logging_utility import log_report


class ImportNVMOperator(ImportOperator,
                        CameraImportProperties,
                        PointImportProperties,
                        GeneralImportProperties,
                        ImportHelper):
    
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
        log_report('INFO', 'path: ' + str(path), self)

        self.image_dp = self.get_default_image_path(
            path, self.image_dp)
        log_report('INFO', 'image_dp: ' + str(self.image_dp), self)

        cameras, points = NVMFileHandler.parse_nvm_file(
            path, self.image_dp, self.image_fp_type, self.suppress_distortion_warnings, self)
        log_report('INFO', 'Number cameras: ' + str(len(cameras)), self)
        log_report('INFO', 'Number points: ' + str(len(points)), self)
        
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
        self.draw_camera_options(layout, draw_image_size=True, draw_principal_point=True)
        self.draw_point_options(layout)
        self.draw_general_options(layout)
