import os
import bpy
from bpy.props import StringProperty

from photogrammetry_importer.operators.import_op import ImportOperator
from photogrammetry_importer.properties.camera_import_properties import CameraImportProperties
from photogrammetry_importer.properties.point_import_properties import PointImportProperties
from photogrammetry_importer.properties.mesh_import_properties import MeshImportProperties
from photogrammetry_importer.properties.general_import_properties import GeneralImportProperties

from photogrammetry_importer.file_handlers.colmap_file_handler import ColmapFileHandler
from photogrammetry_importer.utility.blender_utility import add_collection

class ImportColmapOperator( ImportOperator, 
                            CameraImportProperties,
                            PointImportProperties,
                            MeshImportProperties,
                            GeneralImportProperties):
    
    """Import a Colmap model (folder with .txt/.bin) or a Colmap workspace folder 
    with dense point clouds and meshes."""
    bl_idname = "import_scene.colmap_model"
    bl_label = "Import Colmap Model Folder"
    bl_options = {'PRESET'}

    directory : StringProperty()
    #filter_folder : BoolProperty(default=True, options={'HIDDEN'})

    def execute(self, context):

        path = self.directory
        # Remove trailing slash
        path = os.path.dirname(path)
        self.report({'INFO'}, 'path: ' + str(path))

        self.image_dp = self.get_default_image_path(
            path, self.image_dp)
        self.report({'INFO'}, 'image_dp: ' + str(self.image_dp))
        
        cameras, points, mesh_ifp = ColmapFileHandler.parse_colmap_folder(
            path, self.image_dp, self.image_fp_type, self.suppress_distortion_warnings, self)

        self.report({'INFO'}, 'Number cameras: ' + str(len(cameras)))
        self.report({'INFO'}, 'Number points: ' + str(len(points)))
        self.report({'INFO'}, 'Mesh file path: ' + str(mesh_ifp))

        reconstruction_collection = add_collection('Reconstruction Collection')
        self.import_photogrammetry_cameras(cameras, reconstruction_collection)
        self.import_photogrammetry_points(points, reconstruction_collection)
        self.import_photogrammetry_mesh(mesh_ifp, reconstruction_collection)
        self.apply_general_options()

        return {'FINISHED'}

    def invoke(self, context, event):

        addon_name = self.get_addon_name()
        import_export_prefs = bpy.context.preferences.addons[addon_name].preferences
        self.initialize_options(import_export_prefs)
        # See: 
        # https://blender.stackexchange.com/questions/14738/use-filemanager-to-select-directory-instead-of-file/14778
        # https://docs.blender.org/api/current/bpy.types.WindowManager.html#bpy.types.WindowManager.fileselect_add
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        self.draw_camera_options(layout, draw_depth_map_import=True)
        self.draw_point_options(layout)
        self.draw_mesh_options(layout)
        self.draw_general_options(layout)
