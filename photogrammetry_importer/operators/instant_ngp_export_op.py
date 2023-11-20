import os
import bpy
from bpy.props import StringProperty, CollectionProperty
from bpy_extras.io_utils import ExportHelper

from photogrammetry_importer.file_handlers.instant_ngp_file_handler import (
    InstantNGPFileHandler,
)
from photogrammetry_importer.operators.export_op import ExportOperator


class ExportInstantNGPOperator(ExportOperator, ExportHelper):
    """:code:`Blender` operator to export a :code:`Instant-NGP` json file."""

    bl_idname = "export_scene.instant_ngp"
    bl_label = "Export Instant-NGP"
    bl_options = {"PRESET"}

    # https://docs.blender.org/api/current/bpy.types.FileSelectParams.html
    directory: StringProperty()

    files: CollectionProperty(
        name="File Path",
        description="File path used for exporting the JSON file",
        type=bpy.types.OperatorFileListElement,
    )

    filename_ext = ".json"
    filter_glob: StringProperty(default="*.json", options={"HIDDEN"})

    def execute(self, context):
        """Export selected cameras as :code:`Instant-NGP` JSON file."""
        assert len(self.files) == 1
        ofp = os.path.join(self.directory, self.files[0].name)

        cameras, _ = self.get_selected_cameras_and_vertices_of_meshes(odp="")
        for cam in cameras:
            assert cam.get_calibration_mat() is not None

        InstantNGPFileHandler.write_instant_ngp_file(ofp, cameras, op=self)

        return {"FINISHED"}
