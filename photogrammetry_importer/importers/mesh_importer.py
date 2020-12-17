import os
import bpy
from bpy.props import BoolProperty
from photogrammetry_importer.blender_utility.logging_utility import log_report
from photogrammetry_importer.importers.mesh_utility import (
    add_color_emission_to_material,
    add_mesh_vertex_color_material,
)


class MeshImporter:
    """Importer for meshes."""

    import_mesh: BoolProperty(
        name="Import Mesh",
        description="Import mesh (if available)."
        " Only relevant for files/folders referencing/containing mesh files"
        " (such as *.mg files of Meshroom or dense Colmap folders)."
        " Note that Blenders build-in ply- and obj-importer are quite slow",
        default=False,
    )

    add_mesh_color_emission: BoolProperty(
        name="Add Color Emission of Mesh",
        description="Enabling color emission improves the visibility of the"
        " mesh colors",
        default=True,
    )

    def draw_mesh_options(self, layout):
        """Draw mesh import options."""
        mesh_box = layout.box()
        mesh_box.prop(self, "import_mesh")
        if self.import_mesh:
            mesh_box.prop(self, "add_mesh_color_emission")

    def import_photogrammetry_mesh(self, mesh_fp, reconstruction_collection):
        """Import a mesh using the properties of this class."""
        if self.import_mesh and mesh_fp is not None:
            log_report("INFO", "Importing mesh: ...", self)
            previous_collection = bpy.context.collection

            if os.path.splitext(mesh_fp)[1].lower() == ".obj":
                # https://docs.blender.org/api/current/bpy.ops.import_scene.html
                bpy.ops.import_scene.obj(
                    filepath=mesh_fp, axis_forward="Y", axis_up="Z"
                )
            elif os.path.splitext(mesh_fp)[1].lower() == ".ply":
                # https://docs.blender.org/api/current/bpy.ops.import_mesh.html
                bpy.ops.import_mesh.ply(filepath=mesh_fp)
            else:
                assert False

            imported_object = bpy.context.selected_objects[-1]
            reconstruction_collection.objects.link(imported_object)
            previous_collection.objects.unlink(imported_object)

            mesh_has_texture = len(imported_object.data.materials) > 0
            mesh_has_vertex_color = "Col" in imported_object.data.vertex_colors

            if mesh_has_texture:
                if self.add_mesh_color_emission:
                    add_color_emission_to_material(imported_object)
            else:
                if mesh_has_vertex_color:
                    add_mesh_vertex_color_material(
                        imported_object,
                        "VertexColorMaterial",
                        add_mesh_color_emission=self.add_mesh_color_emission,
                    )

            log_report("INFO", "Importing mesh: Done", self)
