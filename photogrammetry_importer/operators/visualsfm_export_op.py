import os
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper

from bpy.props import CollectionProperty

from photogrammetry_importer.file_handlers.visualsfm_file_handler import (
    VisualSfMFileHandler,
)
from photogrammetry_importer.operators.export_op import ExportOperator


class ExportVisualSfMOperator(ExportOperator, ExportHelper):
    """Export a :code:`VisualSfM` file."""

    bl_idname = "export_scene.nvm"
    bl_label = "Export NVM"
    bl_options = {"PRESET"}

    directory: StringProperty()

    files: CollectionProperty(
        name="File Path",
        description="File path used for exporting the NVM file",
        type=bpy.types.OperatorFileListElement,
    )

    filename_ext = ".nvm"
    filter_glob: StringProperty(default="*.nvm", options={"HIDDEN"})

    def execute(self, context):
        """Export selected cameras and points as :code:`VisualSfM` file."""
        assert len(self.files) == 1
        ofp = os.path.join(self.directory, self.files[0].name)

        cameras, points = self.get_selected_cameras_and_vertices_of_meshes(
            odp=""
        )
        for cam in cameras:
            assert cam.get_calibration_mat() is not None

        VisualSfMFileHandler.write_visualsfm_file(
            ofp, cameras, points, op=self
        )

        return {"FINISHED"}
