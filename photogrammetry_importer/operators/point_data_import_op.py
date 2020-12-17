import os
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from photogrammetry_importer.operators.import_op import ImportOperator
from photogrammetry_importer.operators.general_options import GeneralOptions

from photogrammetry_importer.importers.point_importer import PointImporter

from photogrammetry_importer.file_handlers.point_data_file_handler import (
    PointDataFileHandler,
)
from photogrammetry_importer.file_handlers.transformation_file_handler import (
    TransformationFileHandler,
)
from photogrammetry_importer.blender_utility.object_utility import (
    add_collection,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report


class ImportPointDataOperator(
    ImportOperator,
    PointImporter,
    GeneralOptions,
    ImportHelper,
):
    """Import point data (e.g. a :code:`PLY` file) as point cloud."""

    bl_idname = "import_scene.point_data"
    bl_label = "Import Point Data"
    bl_options = {"PRESET"}

    filepath: StringProperty(
        name="Point Data File Path",
        description="File path used for importing the point data file",
    )
    directory: StringProperty()
    filter_glob: StringProperty(
        default="*.ply;*.pcd;*.las;*.laz;*.asc;*.pts;*.csv", options={"HIDDEN"}
    )

    def execute(self, context):
        """Import a file with point data (e.g. :code:`PLY`)."""
        path = os.path.join(self.directory, self.filepath)
        log_report("INFO", "path: " + str(path), self)

        points = PointDataFileHandler.parse_point_data_file(path, self)
        log_report("INFO", "Number points: " + str(len(points)), self)

        reconstruction_collection = add_collection("Reconstruction Collection")
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
        self.draw_point_options(layout)
        self.draw_general_options(layout)
