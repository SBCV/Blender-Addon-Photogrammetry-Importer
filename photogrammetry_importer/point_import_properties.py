import bpy

from bpy.props import (BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty)
from photogrammetry_importer.utils.blender_animation_utils import add_transformation_animation
from photogrammetry_importer.utils.blender_point_utils import add_points_as_mesh
from photogrammetry_importer.opengl.visualization_utils import draw_points

class PointImportProperties():
    """ This class encapsulates Blender UI properties that are required to visualize the reconstructed points correctly. """
    import_points: BoolProperty(
        name="Import Points",
        description = "Import Points", 
        default=True)
    draw_points_with_gpu : BoolProperty(
       name="Draw Points in the 3D View with OpenGL.",
        description="Draw Points in the 3D View. Allows to visualize point clouds with many elements. These are not visible in eevee/cycles renderings.",
        default=True)
    add_points_as_particle_system: BoolProperty(
        name="Add Points as Particle System",
        description="Use a particle system to represent vertex positions with objects. Can be rendered with eevee/cycles.",
        default=False)
    mesh_items = [
        ("CUBE", "Cube", "", 1),
        ("SPHERE", "Sphere", "", 2),
        ("PLANE", "Plane", "", 3)
        ]
    mesh_type: EnumProperty(
        name="Mesh Type",
        description = "Select the vertex representation mesh type.", 
        items=mesh_items)
    point_extent: FloatProperty(
        name="Initial Point Extent (in Blender Units)", 
        description = "Initial Point Extent for meshes at vertex positions",
        default=0.01)
    add_particle_color_emission: BoolProperty(
        name="Add Particle Color Emission",
        description = "Add particle color emission to increase the visibility of the individual objects of the particle system.", 
        default=True)
    set_particle_color_flag: BoolProperty(
        name="Set Fixed Particle Color",
        description="Overwrite the colors in the file with a single color.", 
        default=False
    )
    particle_overwrite_color: FloatVectorProperty(
        name="Particle Color",
        description="Single fixed particle color.", 
        default=(0.0, 1.0, 0.0),
        min=0.0,
        max=1.0
    )

    def draw_point_options(self, layout):
        point_box = layout.box()
        point_box.prop(self, "import_points")
        if self.import_points:
            particle_box = point_box.box()
            particle_box.prop(self, "draw_points_with_gpu")
            particle_box.prop(self, "add_points_as_particle_system")
            if self.add_points_as_particle_system:
                particle_box.prop(self, "mesh_type")
                particle_box.prop(self, "add_particle_color_emission")
                particle_box.prop(self, "point_extent")
                particle_box.prop(self, "set_particle_color_flag")
                if self.set_particle_color_flag:
                    particle_box.prop(self, "particle_overwrite_color")
                    

    def import_photogrammetry_points(self, points, reconstruction_collection, transformations_sorted=None):
        if self.import_points:

            if self.draw_points_with_gpu:
                draw_points(self, points)

            point_cloud_obj_name = add_points_as_mesh(
                self, 
                points, 
                self.add_points_as_particle_system, 
                self.mesh_type, 
                self.point_extent,
                self.add_particle_color_emission,
                reconstruction_collection,
                self.set_particle_color_flag,
                self.particle_overwrite_color) 

            if transformations_sorted is not None:
                add_transformation_animation(
                    self,
                    point_cloud_obj_name,
                    transformations_sorted, 
                    number_interpolation_frames=1, 
                    interpolation_type=None,
                    remove_rotation_discontinuities=False)

