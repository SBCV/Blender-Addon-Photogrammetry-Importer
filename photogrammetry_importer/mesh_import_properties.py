import bpy
from bpy.props import (BoolProperty)

class MeshImportProperties():
    """ This class encapsulates Blender UI properties that are required to import a mesh. """
    import_mesh: BoolProperty(
        name="Import Mesh",
        description =   "Import mesh (if available)." + 
                        " Only relevant for files/folders referencing/containing mesh files" +
                        " (such as *.mg files of Meshroom or dense Colmap folders).", 
        default=False)

    def draw_mesh_options(self, layout):
        mesh_box = layout.box()
        mesh_box.prop(self, "import_mesh")
                    
    def import_photogrammetry_mesh(self, mesh_fp, reconstruction_collection):
        if self.import_mesh:

            previous_collection = bpy.context.collection
            # https://docs.blender.org/api/current/bpy.ops.import_scene.html
            bpy.ops.import_scene.obj(filepath=mesh_fp, axis_forward='Y', axis_up='Z')
            imported_object = bpy.context.selected_objects[0]
            reconstruction_collection.objects.link(imported_object)
            previous_collection.objects.unlink(imported_object)
