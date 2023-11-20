import os
from bpy.props import StringProperty

from photogrammetry_importer.operators.import_op import ImportOperator
from photogrammetry_importer.operators.general_options import GeneralOptions

from photogrammetry_importer.importers.camera_importer import CameraImporter

from photogrammetry_importer.file_handlers.instant_ngp_file_handler import (
    InstantNGPFileHandler,
)
from photogrammetry_importer.blender_utility.object_utility import (
    add_collection,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report


class ImportInstantNGPOperator(
    ImportOperator,
    CameraImporter,
    GeneralOptions,
):
    """:code:`Blender` operator to import a :code:`Instant-NGP` json file."""

    bl_idname = "import_scene.instant_ngp_json"
    bl_label = "Import Instant-NGP json file"
    bl_options = {"PRESET"}

    filepath: StringProperty(
        name="Instant-NGP JSON File Path",
        description="File path used for importing the Instant-NGP JSON file",
    )

    directory: StringProperty()
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        """Import an :code:`Instant-NGP` :code:`JSON` file."""
        path = os.path.join(self.directory, self.filepath)

        log_report("INFO", "path: " + str(path), self)

        self.image_dp = self.get_default_image_path(path, self.image_dp)
        cameras = InstantNGPFileHandler.parse_instant_ngp_json_file(
            path,
            self.image_dp,
            self.image_fp_type,
            self.suppress_distortion_warnings,
            self,
        )

        log_report("INFO", "Number cameras: " + str(len(cameras)), self)

        reconstruction_collection = add_collection("Reconstruction Collection")
        self.import_photogrammetry_cameras(cameras, reconstruction_collection)
        self.apply_general_options()

        return {"FINISHED"}

    def invoke(self, context, event):
        """Set the default import options before running the operator."""
        self.initialize_options_from_addon_preferences()
        # See:
        # https://blender.stackexchange.com/questions/14738/use-filemanager-to-select-directory-instead-of-file/14778
        # https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        """Draw the import options corresponding to this operator."""
        layout = self.layout
        self.draw_camera_options(
            layout,
            draw_workspace_image_usage=True,
        )
        self.draw_general_options(layout)
