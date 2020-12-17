import os
import math
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from photogrammetry_importer.operators.import_op import ImportOperator
from photogrammetry_importer.operators.general_options import GeneralOptions
from photogrammetry_importer.operators.utility import (
    set_image_size_for_cameras,
)

from photogrammetry_importer.importers.camera_importer import CameraImporter
from photogrammetry_importer.importers.point_importer import PointImporter

from photogrammetry_importer.file_handlers.open3D_file_handler import (
    Open3DFileHandler,
)
from photogrammetry_importer.blender_utility.object_utility import (
    add_collection,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report

from photogrammetry_importer.types.camera import Camera


class ImportOpen3DOperator(
    ImportOperator,
    CameraImporter,
    PointImporter,
    GeneralOptions,
    ImportHelper,
):
    """Import an :code:`Open3D` LOG/JSON file"""

    bl_idname = "import_scene.open3d_log_json"
    bl_label = "Import Open3D LOG/JSON"
    bl_options = {"PRESET"}

    filepath: StringProperty(
        name="Open3D LOG/JSON File Path",
        description="File path used for importing the Open3D LOG/JSON file",
    )
    directory: StringProperty()
    filter_glob: StringProperty(default="*.log;*.json", options={"HIDDEN"})

    def set_intrinsics_of_cameras(self, cameras):
        """Enhances the imported cameras with intrinsic information.

        Overwrites the method in :code:`CameraImporter`.
        """
        intrinsic_missing = False
        for cam in cameras:
            if not cam.has_intrinsics():
                intrinsic_missing = True
                break

        if not intrinsic_missing:
            log_report("INFO", "Using intrinsics from file (.json).", self)
            return cameras, True
        else:
            log_report(
                "INFO",
                "Using intrinsics from user options, since not present in the"
                + " reconstruction file (.log).",
                self,
            )
            if math.isnan(self.default_focal_length):
                log_report(
                    "ERROR",
                    "User must provide the focal length using the import"
                    + " options.",
                    self,
                )
                return [], False

            if math.isnan(self.default_pp_x) or math.isnan(self.default_pp_y):
                log_report(
                    "WARNING",
                    "Setting the principal point to the image center.",
                    self,
                )

            for cam in cameras:
                if math.isnan(self.default_pp_x) or math.isnan(
                    self.default_pp_y
                ):
                    # If no images are provided, the user must provide a
                    # default principal point
                    assert cam.width is not None
                    # If no images are provided, the user must provide a
                    # default principal point
                    assert cam.height is not None
                    default_cx = cam.width / 2.0
                    default_cy = cam.height / 2.0
                else:
                    default_cx = self.default_pp_x
                    default_cy = self.default_pp_y

                intrinsics = Camera.compute_calibration_mat(
                    focal_length=self.default_focal_length,
                    cx=default_cx,
                    cy=default_cy,
                )
                cam.set_calibration_mat(intrinsics)
            return cameras, True

    def _image_size_initialized(self, cameras):
        missing_data = False
        for camera in cameras:
            if camera.width is None or camera.height is None:
                missing_data = True
                break
        is_initialized = not missing_data
        return is_initialized

    def set_image_size_of_cameras(self, cameras):
        """Enhance the imported cameras with image related information.

        Overwrites the method in :code:`CameraImporter`.
        """
        if not self._image_size_initialized(cameras):
            success = set_image_size_for_cameras(
                cameras, self.default_width, self.default_height, self
            )
        else:
            success = True
        return cameras, success

    def execute(self, context):
        """Import an :code:`Open3D` file."""
        path = os.path.join(self.directory, self.filepath)
        log_report("INFO", "path: " + str(path), self)

        self.image_dp = self.get_default_image_path(path, self.image_dp)
        log_report("INFO", "image_dp: " + str(self.image_dp), self)

        cameras = Open3DFileHandler.parse_open3d_file(
            path, self.image_dp, self.image_fp_type, self
        )

        log_report("INFO", "Number cameras: " + str(len(cameras)), self)

        reconstruction_collection = add_collection("Reconstruction Collection")
        self.import_photogrammetry_cameras(cameras, reconstruction_collection)
        self.apply_general_options()

        return {"FINISHED"}

    def invoke(self, context, event):
        """Set the default import options before running the operator."""
        self.initialize_options_from_addon_preferences()
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        """Draw the import options corresponding to this operator."""
        layout = self.layout
        self.draw_camera_options(
            layout,
            draw_image_size=True,
            draw_principal_point=True,
            draw_focal_length=True,
        )
        self.draw_general_options(layout)
