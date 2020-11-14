import os
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ExportHelper

from bpy.props import CollectionProperty

from photogrammetry_importer.file_handlers.nvm_file_handler import (
    NVMFileHandler,
)
from photogrammetry_importer.operators.export_op import ExportOperator


class ExportNVMOperator(ExportOperator, ExportHelper):
    """Export a NVM file"""

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
        assert len(self.files) == 1
        ofp = os.path.join(self.directory, self.files[0].name)

        cameras, points = self.export_selected_cameras_and_vertices_of_meshes(
            ""
        )
        for cam in cameras:
            assert cam.get_calibration_mat() is not None

        NVMFileHandler.write_nvm_file(ofp, cameras, points, op=self)

        return {"FINISHED"}
