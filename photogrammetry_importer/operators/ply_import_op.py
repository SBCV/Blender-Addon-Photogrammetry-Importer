import os
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from photogrammetry_importer.operators.import_op import ImportOperator
from photogrammetry_importer.properties.point_import_properties import PointImportProperties
from photogrammetry_importer.properties.transformation_import_properties import TransformationImportProperties

from photogrammetry_importer.file_handlers.ply_file_handler import PLYFileHandler
from photogrammetry_importer.file_handlers.transformation_file_handler import TransformationFileHandler
from photogrammetry_importer.utility.blender_utility import add_collection


class ImportPLYOperator(ImportOperator,
                        PointImportProperties,
                        TransformationImportProperties,
                        ImportHelper):

    """Import a PLY file as point cloud"""
    bl_idname = "import_scene.ply"
    bl_label = "Import PLY"
    bl_options = {'PRESET'}

    filepath: StringProperty(
        name="PLY File Path",
        description="File path used for importing the PLY file")
    directory: StringProperty()
    filter_glob: StringProperty(default="*.ply", options={'HIDDEN'})

    def execute(self, context):
        path = os.path.join(self.directory, self.filepath)
        self.report({'INFO'}, 'path: ' + str(path))

        points = PLYFileHandler.parse_ply_file(path)
        self.report({'INFO'}, 'Number points: ' + str(len(points)))

        transformations_sorted = TransformationFileHandler.parse_transformation_folder(
            self.path_to_transformations, self)

        reconstruction_collection = add_collection('Reconstruction Collection')
        self.import_photogrammetry_points(points, reconstruction_collection, transformations_sorted)

        return {'FINISHED'}

    def invoke(self, context, event):
        addon_name = self.get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[addon_name].preferences
        self.initialize_options(import_export_prefs)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        self.draw_point_options(layout)
        self.draw_transformation_options(layout)
