import os
import bpy
from bpy.props import StringProperty

from photogrammetry_importer.operators.import_op import ImportOperator
from photogrammetry_importer.operators.general_options import GeneralOptions

from photogrammetry_importer.importers.camera_importer import CameraImporter
from photogrammetry_importer.importers.point_importer import PointImporter
from photogrammetry_importer.importers.mesh_importer import MeshImporter

from photogrammetry_importer.file_handlers.colmap_file_handler import (
    ColmapFileHandler,
)
from photogrammetry_importer.blender_utility.object_utility import (
    add_collection,
)
from photogrammetry_importer.blender_utility.logging_utility import log_report


class ImportColmapOperator(
    ImportOperator,
    CameraImporter,
    PointImporter,
    MeshImporter,
    GeneralOptions,
):
    """:code:`Blender` operator to import a :code:`Colmap` model/workspace."""

    bl_idname = "import_scene.colmap_model"
    bl_label = "Import Colmap Model Folder"
    bl_options = {"PRESET"}

    directory: StringProperty()
    # filter_folder : BoolProperty(default=True, options={'HIDDEN'})

    def execute(self, context):
        """Import a :code:`Colmap` model/workspace."""
        path = self.directory
        # Remove trailing slash
        path = os.path.dirname(path)
        log_report("INFO", "path: " + str(path), self)

        self.image_dp = self.get_default_image_path(path, self.image_dp)
        cameras, points, mesh_ifp = ColmapFileHandler.parse_colmap_folder(
            path,
            self.use_workspace_images,
            self.image_dp,
            self.image_fp_type,
            self.suppress_distortion_warnings,
            self,
        )

        log_report("INFO", "Number cameras: " + str(len(cameras)), self)
        log_report("INFO", "Number points: " + str(len(points)), self)
        log_report("INFO", "Mesh file path: " + str(mesh_ifp), self)

        reconstruction_collection = add_collection("Reconstruction Collection")
        self.import_photogrammetry_cameras(cameras, reconstruction_collection)
        self.import_photogrammetry_points(points, reconstruction_collection)
        self.import_photogrammetry_mesh(mesh_ifp, reconstruction_collection)
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
            layout, draw_workspace_image_usage=True, draw_depth_map_import=True
        )
        self.draw_point_options(layout)
        self.draw_mesh_options(layout)
        self.draw_general_options(layout)
