import os
import bpy
from bpy.props import (BoolProperty)

class MeshImportProperties():
    """ This class encapsulates Blender UI properties that are required to import a mesh. """
    import_mesh: BoolProperty(
        name="Import Mesh",
        description =   "Import mesh (if available)." + 
                        " Only relevant for files/folders referencing/containing mesh files" +
                        " (such as *.mg files of Meshroom or dense Colmap folders)." +
                        " Note that Blenders build-in ply- and obj-importer are quite slow.",
        default=False)

    def draw_mesh_options(self, layout):
        mesh_box = layout.box()
        mesh_box.prop(self, "import_mesh")
                    
    def import_photogrammetry_mesh(self, mesh_fp, reconstruction_collection):
        if self.import_mesh and mesh_fp is not None:
            self.report({'INFO'}, 'Importing mesh: ...')
            previous_collection = bpy.context.collection

            if os.path.splitext(mesh_fp)[1].lower() == '.obj':
                # https://docs.blender.org/api/current/bpy.ops.import_scene.html
                bpy.ops.import_scene.obj(filepath=mesh_fp, axis_forward='Y', axis_up='Z')
            elif os.path.splitext(mesh_fp)[1].lower() == '.ply':
                bpy.ops.import_mesh.ply(filepath=mesh_fp)
            else:
                assert False

            imported_object = bpy.context.selected_objects[-1]
            reconstruction_collection.objects.link(imported_object)
            previous_collection.objects.unlink(imported_object)
            self.report({'INFO'}, 'Importing mesh: Done')
