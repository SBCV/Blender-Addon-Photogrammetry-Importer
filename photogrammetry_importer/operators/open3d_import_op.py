import os
import math
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from photogrammetry_importer.operators.import_op import ImportOperator
from photogrammetry_importer.properties.camera_import_properties import CameraImportProperties
from photogrammetry_importer.properties.point_import_properties import PointImportProperties
from photogrammetry_importer.properties.general_import_properties import GeneralImportProperties

from photogrammetry_importer.file_handlers.image_file_handler import ImageFileHandler
from photogrammetry_importer.file_handlers.open3D_file_handler import Open3DFileHandler
from photogrammetry_importer.utility.blender_utility import add_collection
from photogrammetry_importer.utility.blender_logging_utility import log_report

from photogrammetry_importer.types.camera import Camera

class ImportOpen3DOperator( ImportOperator,
                            CameraImportProperties, 
                            PointImportProperties,
                            GeneralImportProperties,
                            ImportHelper):

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
            log_report('INFO', 'Using intrinsics from file (.json).', self)
            return cameras, True
        else:
            log_report('INFO', 'Using intrinsics from user options, since not present in the reconstruction file (.log).', self)
            if math.isnan(self.default_focal_length):
                log_report('ERROR', 'User must provide the focal length using the import options.', self)
                return [], False 

            if math.isnan(self.default_pp_x) or math.isnan(self.default_pp_y):
                log_report('WARNING', 'Setting the principal point to the image center.', op)

            for cam in cameras:
                if math.isnan(self.default_pp_x) or math.isnan(self.default_pp_y):
                    # If no images are provided, the user must provide a default principal point
                    assert cam.width is not None
                    # If no images are provided, the user must provide a default principal point
                    assert cam.height is not None
                    default_cx = cam.width / 2.0
                    default_cy = cam.height / 2.0
                else:
                    default_cx = self.default_pp_x
                    default_cy = self.default_pp_y
                
                intrinsics = Camera.compute_calibration_mat(
                    focal_length=self.default_focal_length, cx=default_cx, cy=default_cy)
                cam.set_calibration_mat(intrinsics)
            return cameras, True

    def image_size_initialized(self, cameras):
        missing_data = False
        for camera in cameras:
            if camera.width is None or camera.height is None:
                missing_data = True
                break
        is_initialized = not missing_data 
        return is_initialized

    def enhance_camera_with_images(self, cameras):

        if not self.image_size_initialized(cameras):
            # Overwrites CameraImportProperties.enhance_camera_with_images()
            cameras, success = ImageFileHandler.parse_camera_image_files(
                cameras, self.default_width, self.default_height, self)
        else:
            success = True
        return cameras, success

    def execute(self, context):

        path = os.path.join(self.directory, self.filepath)
        log_report('INFO', 'path: ' + str(path), self)

        self.image_dp = self.get_default_image_path(
            path, self.image_dp)
        log_report('INFO', 'image_dp: ' + str(self.image_dp), self)
        
        cameras = Open3DFileHandler.parse_open3d_file(
            path, self.image_dp, self.image_fp_type, self)
        
        log_report('INFO', 'aaaaa ' + str(cameras[0].width), self)
        log_report('INFO', 'Number cameras: ' + str(len(cameras)), self)
        
        reconstruction_collection = add_collection('Reconstruction Collection')
        self.import_photogrammetry_cameras(cameras, reconstruction_collection)
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
        self.draw_camera_options(
            layout, 
            draw_image_size=True,
            draw_principal_point=True,
            draw_focal_length=True)
        self.draw_general_options(layout)
