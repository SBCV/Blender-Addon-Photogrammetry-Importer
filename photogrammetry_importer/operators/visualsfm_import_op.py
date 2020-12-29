import os
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

from photogrammetry_importer.file_handlers.visualsfm_file_handler import (
    VisualSfMFileHandler,
)

from photogrammetry_importer.types.camera import Camera

from photogrammetry_importer.blender_utility.object_utility import (
    add_collection,
)

from photogrammetry_importer.blender_utility.logging_utility import log_report


class ImportVisualSfMOperator(
    ImportOperator,
    CameraImporter,
    PointImporter,
    GeneralOptions,
    ImportHelper,
):
    """Import a :code:`VisualSfM` NVM file."""

    bl_idname = "import_scene.visualsfm_nvm"
    bl_label = "Import NVM"
    bl_options = {"PRESET"}

    filepath: StringProperty(
        name="NVM File Path",
        description="File path used for importing the NVM file",
    )
    directory: StringProperty()
    filter_glob: StringProperty(default="*.nvm", options={"HIDDEN"})

    def set_image_size_of_cameras(self, cameras):
        """Enhance the imported cameras with image related information.

        Overwrites the method in :code:`CameraImporter`.
        """
        success = set_image_size_for_cameras(
            cameras, self.default_width, self.default_height, self
        )
        return cameras, success

    def execute(self, context):
        """Import an :code:`VisualSfM` file."""
        path = os.path.join(self.directory, self.filepath)
        log_report("INFO", "path: " + str(path), self)

        self.image_dp = self.get_default_image_path(path, self.image_dp)
        log_report("INFO", "image_dp: " + str(self.image_dp), self)

        cameras, points = VisualSfMFileHandler.parse_visualsfm_file(
            path,
            self.image_dp,
            self.image_fp_type,
            self.suppress_distortion_warnings,
            self,
        )
        log_report("INFO", "Number cameras: " + str(len(cameras)), self)
        log_report("INFO", "Number points: " + str(len(points)), self)

        reconstruction_collection = add_collection("Reconstruction Collection")
        self.import_photogrammetry_cameras(cameras, reconstruction_collection)
        self.import_photogrammetry_points(points, reconstruction_collection)
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
            layout, draw_image_size=True, draw_principal_point=True
        )
        self.draw_point_options(layout)
        self.draw_general_options(layout)
