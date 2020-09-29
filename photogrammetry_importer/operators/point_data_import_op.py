import os
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from photogrammetry_importer.operators.import_op import ImportOperator
from photogrammetry_importer.properties.point_import_properties import (
    PointImportProperties,
)
from photogrammetry_importer.properties.transformation_import_properties import (
    TransformationImportProperties,
)
from photogrammetry_importer.properties.general_import_properties import (
    GeneralImportProperties,
)

from photogrammetry_importer.file_handlers.point_data_file_handler import (
    PointDataFileHandler,
)
from photogrammetry_importer.file_handlers.transformation_file_handler import (
    TransformationFileHandler,
)
from photogrammetry_importer.utility.blender_utility import add_collection
from photogrammetry_importer.utility.blender_logging_utility import log_report


class ImportPointDataOperator(
    ImportOperator,
    PointImportProperties,
    TransformationImportProperties,
    GeneralImportProperties,
    ImportHelper,
):

    """Import point data (PLY file) as point cloud"""

    bl_idname = "import_scene.point_data"
    bl_label = "Import Point Data"
    bl_options = {"PRESET"}

    filepath: StringProperty(
        name="Point Data File Path",
        description="File path used for importing the point data file",
    )
    directory: StringProperty()
    filter_glob: StringProperty(
        default="*.ply;*.pcd;*.las;*.asc;*.pts;*.csv", options={"HIDDEN"}
    )

    def execute(self, context):
        path = os.path.join(self.directory, self.filepath)
        log_report("INFO", "path: " + str(path), self)

        points = PointDataFileHandler.parse_point_data_file(path, self)
        log_report("INFO", "Number points: " + str(len(points)), self)

        transformations_sorted = (
            TransformationFileHandler.parse_transformation_folder(
                self.path_to_transformations, self
            )
        )

        reconstruction_collection = add_collection("Reconstruction Collection")
        self.import_photogrammetry_points(
            points, reconstruction_collection, transformations_sorted
        )
        self.apply_general_options()

        return {"FINISHED"}

    def invoke(self, context, event):
        addon_name = self.get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[
            addon_name
        ].preferences
        self.initialize_options(import_export_prefs)
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        layout = self.layout
        self.draw_point_options(layout)
        self.draw_transformation_options(layout)
        self.draw_general_options(layout)
