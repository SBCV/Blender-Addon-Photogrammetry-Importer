import bpy

from bpy.props import (
    BoolProperty,
    EnumProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
)
from photogrammetry_importer.opengl.utility import draw_points
from photogrammetry_importer.importers.point_utility import (
    add_points_as_mesh_vertices,
    add_points_as_object_with_particle_system,
)
from photogrammetry_importer.types.point import Point


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
    center_points: BoolProperty(
        name="Center Data Around Origin",
        description="Center data by subtracting the centroid. Useful for las/"
        "laz files, which contain usually large offsets.",
        default=False,
    )
    # Option 1: Draw Points with GPU
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
    point_size: IntProperty(
        name="Initial Point Size",
        description="Initial Point Size",
        default=5,
    )

    # Option 2: Add Points as Mesh Object
    add_points_as_mesh_oject: BoolProperty(
        name="Add Points as Mesh Object",
        description="Use a mesh object to represent the point cloud with the "
        "vertex positions.",
        default=False,
    )
    add_mesh_to_point_geometry_nodes: BoolProperty(
        name="Add Geometry Nodes",
        description="Add Geometry Nodes to allow rendering of the point cloud "
        "with Blender's built-in renderers (Eevee / Cycles).",
        default=True,
    )
    point_radius: FloatProperty(
        name="Initial Point Radius",
        description="Initial point radius (can be changed in GUI).",
        default=0.05,
    )
    point_subdivisions: IntProperty(
        name="Initial Point Subdivisions",
        description="Initial point subdivisions (can be changed in GUI).",
        default=1,
    )
    add_color_as_custom_property: BoolProperty(
        name="Add Colors as Custom Property",
        description="Use a custom property (named colors) to store the point "
        "cloud colors.",
        default=True,
    )

    def draw_point_options(self, layout, draw_everything=False):
        """Draw point import options."""
        point_box = layout.box()
        point_box.prop(self, "import_points")
        point_box.prop(self, "point_cloud_display_sparsity")
        point_box.prop(self, "center_points")
        if self.import_points or draw_everything:
            opengl_box = point_box.box()
            opengl_box.prop(self, "draw_points_with_gpu")
            if self.draw_points_with_gpu or draw_everything:
                opengl_box.prop(self, "add_points_to_point_cloud_handle")
                opengl_box.prop(self, "point_size")
            mesh_box = point_box.box()
            mesh_box.prop(self, "add_points_as_mesh_oject")
            if self.add_points_as_mesh_oject:
                mesh_box.prop(self, "add_mesh_to_point_geometry_nodes")
                mesh_box.prop(self, "point_radius")
                mesh_box.prop(self, "point_subdivisions")
                mesh_box.prop(self, "add_color_as_custom_property")

    def import_photogrammetry_points(self, points, reconstruction_collection):
        """Import a point cloud using the properties of this class."""
        if self.import_points:
            if self.point_cloud_display_sparsity > 1:
                points = points[:: self.point_cloud_display_sparsity]

            if self.center_points:
                points = Point.get_centered_points(points)

            if self.draw_points_with_gpu:
                draw_points(
                    points,
                    self.point_size,
                    self.add_points_to_point_cloud_handle,
                    reconstruction_collection,
                    op=self,
                )

            if self.add_points_as_mesh_oject:
                add_points_as_mesh_vertices(
                    points,
                    reconstruction_collection,
                    self.add_mesh_to_point_geometry_nodes,
                    self.point_radius,
                    self.point_subdivisions,
                    self.add_color_as_custom_property,
                    op=self,
                )
