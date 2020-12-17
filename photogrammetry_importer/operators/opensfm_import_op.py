import os
import bpy
from bpy.props import StringProperty, IntProperty
from bpy_extras.io_utils import ImportHelper

from photogrammetry_importer.operators.import_op import ImportOperator
from photogrammetry_importer.operators.general_options import GeneralOptions

from photogrammetry_importer.importers.camera_importer import CameraImporter
from photogrammetry_importer.importers.point_importer import PointImporter

from photogrammetry_importer.file_handlers.opensfm_json_file_handler import (
    OpenSfMJSONFileHandler,
)
from photogrammetry_importer.blender_utility.object_utility import (
    add_collection,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report


class ImportOpenSfMOperator(
    ImportOperator,
    CameraImporter,
    PointImporter,
    GeneralOptions,
    ImportHelper,
):
    """Import an :code:`OpenSfM` JSON file"""

    bl_idname = "import_scene.opensfm_json"
    bl_label = "Import OpenSfM JSON"
    bl_options = {"PRESET"}

    filepath: StringProperty(
        name="OpenSfM JSON File Path",
        description="File path used for importing the OpenSfM JSON file",
    )
    directory: StringProperty()
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    reconstruction_number: IntProperty(
        name="Reconstruction Number",
        description="If the input file contains multiple reconstructions, use"
        + " this property to select the desired reconstruction.",
        default=0,
    )

    def execute(self, context):
        """Import an :code:`OpenSfM` :code:`JSON` file."""
        path = os.path.join(self.directory, self.filepath)
        log_report("INFO", "path: " + str(path), self)

        self.image_dp = self.get_default_image_path(path, self.image_dp)
        log_report("INFO", "image_dp: " + str(self.image_dp), self)

        cameras, points = OpenSfMJSONFileHandler.parse_opensfm_file(
            path,
            self.image_dp,
            self.image_fp_type,
            self.reconstruction_number,
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
        layout.prop(self, "reconstruction_number")
        self.draw_camera_options(layout)
        self.draw_point_options(layout)
        self.draw_general_options(layout)
