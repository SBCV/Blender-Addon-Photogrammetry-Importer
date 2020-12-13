import bpy

from bpy.props import (
    BoolProperty,
    EnumProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
)
from photogrammetry_importer.utility.blender_opengl_utility import draw_points
from photogrammetry_importer.utility.blender_point_utility import (
    add_points_as_mesh,
    add_points_as_particle_system,
)


class PointImporter:
    """Importer for points."""

    import_points: BoolProperty(
        name="Import Points", description="Import Points", default=True
    )
    point_cloud_display_sparsity: IntProperty(
        name="Point Cloud Display Sparsity",
        description="Adjust the sparsity of the point cloud. A value of n "
        "means that every n-th point in the point cloud is added",
        default=1,
        min=1,
    )
    draw_points_with_gpu: BoolProperty(
        name="Draw Points in the 3D View with OpenGL.",
        description="Draw Points in the 3D View. Allows to visualize point "
        "clouds with many elements. These are not visible in eevee/cycles "
        "renderings.",
        default=True,
    )
    add_points_to_point_cloud_handle: BoolProperty(
        name="Add point data to the point cloud handle.",
        description="This allows to draw the point cloud (again) with OpenGL "
        "after saving and reloading the blend file.",
        default=True,
    )
    add_points_as_particle_system: BoolProperty(
        name="Add Points as Particle System",
        description="Use a particle system to represent vertex positions with "
        "objects. Can be rendered with eevee/cycles.",
        default=False,
    )
    mesh_items = [
        ("CUBE", "Cube", "", 1),
        ("SPHERE", "Sphere", "", 2),
        ("PLANE", "Plane", "", 3),
    ]
    mesh_type: EnumProperty(
        name="Mesh Type",
        description="Select the vertex representation mesh type.",
        items=mesh_items,
    )
    point_extent: FloatProperty(
        name="Initial Point Extent (in Blender Units)",
        description="Initial Point Extent for meshes at vertex positions",
        default=0.01,
    )
    add_particle_color_emission: BoolProperty(
        name="Add Particle Color Emission",
        description="Add particle color emission to increase the visibility "
        "of the individual objects of the particle system.",
        default=True,
    )
    set_particle_color_flag: BoolProperty(
        name="Set Fixed Particle Color",
        description="Overwrite the colors in the file with a single color.",
        default=False,
    )
    particle_overwrite_color: FloatVectorProperty(
        name="Particle Color",
        description="Single fixed particle color.",
        subtype="COLOR",
        size=3,
        default=(0.0, 1.0, 0.0),
        min=0.0,
        max=1.0,
    )
    add_points_as_mesh_oject: BoolProperty(
        name="Add Points as Mesh Object",
        description="Use a mesh object to represent the point cloud with the "
        "vertex positions.",
        default=False,
    )

    def draw_point_options(self, layout, draw_everything=False):
        """Draw point import options."""
        point_box = layout.box()
        point_box.prop(self, "import_points")
        point_box.prop(self, "point_cloud_display_sparsity")
        if self.import_points or draw_everything:
            opengl_box = point_box.box()
            opengl_box.prop(self, "draw_points_with_gpu")
            if self.draw_points_with_gpu or draw_everything:
                opengl_box.prop(self, "add_points_to_point_cloud_handle")
            particle_box = point_box.box()
            particle_box.prop(self, "add_points_as_particle_system")
            if self.add_points_as_particle_system or draw_everything:
                particle_box.prop(self, "mesh_type")
                particle_box.prop(self, "add_particle_color_emission")
                particle_box.prop(self, "point_extent")
                particle_box.prop(self, "set_particle_color_flag")
                if self.set_particle_color_flag or draw_everything:
                    particle_box.prop(self, "particle_overwrite_color")
            mesh_box = point_box.box()
            mesh_box.prop(self, "add_points_as_mesh_oject")

    def import_photogrammetry_points(self, points, reconstruction_collection):
        """Import a point cloud using the properties of this class."""
        if self.import_points:
            if self.point_cloud_display_sparsity > 1:
                points = points[:: self.point_cloud_display_sparsity]

            if self.draw_points_with_gpu:
                draw_points(
                    points,
                    self.add_points_to_point_cloud_handle,
                    reconstruction_collection,
                    op=self,
                )

            if self.add_points_as_particle_system:
                if self.set_particle_color_flag:
                    particle_overwrite_color = self.particle_overwrite_color
                else:
                    particle_overwrite_color = None

                add_points_as_particle_system(
                    points,
                    self.mesh_type,
                    self.point_extent,
                    self.add_particle_color_emission,
                    reconstruction_collection,
                    particle_overwrite_color,
                    op=self,
                )

            if self.add_points_as_mesh_oject:
                add_points_as_mesh(
                    points,
                    reconstruction_collection,
                    op=self,
                )
