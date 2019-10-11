import bpy

from bpy.props import (BoolProperty, EnumProperty, FloatProperty)
from photogrammetry_importer.blender_animation_utils import add_animation
from photogrammetry_importer.blender_point_utils import add_points_as_mesh

class PointImportProperties():
    """ This class encapsulates Blender UI properties that are required to visualize the reconstructed points correctly. """
    import_points: BoolProperty(
        name="Import Points",
        description = "Import Points", 
        default=True)
    add_points_as_particle_system: BoolProperty(
        name="Add Points as Particle System",
        description="Use a particle system to represent vertex positions with objects",
        default=True)
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
        name="Add particle color emission",
        description = "Add particle color emission to increase the visibility of the individual objects of the particle system.", 
        default=True)
        
    def draw_point_options(self, layout):
        point_box = layout.box()
        point_box.prop(self, "import_points")
        if self.import_points:
            particle_box = point_box.box()
            particle_box.prop(self, "add_points_as_particle_system")
            if self.add_points_as_particle_system:
                particle_box.prop(self, "mesh_type")
                particle_box.prop(self, "add_particle_color_emission")
                particle_box.prop(self, "point_extent")
    

    def import_photogrammetry_points(self, points, reconstruction_collection, transformations_sorted=None):
        if self.import_points:
            point_cloud_obj_name = add_points_as_mesh(
                self, 
                points, 
                self.add_points_as_particle_system, 
                self.mesh_type, 
                self.point_extent,
                self.add_particle_color_emission,
                reconstruction_collection) 

            if transformations_sorted is not None:
                add_animation(
                    self,
                    point_cloud_obj_name,
                    transformations_sorted, 
                    number_interpolation_frames=1, 
                    interpolation_type=None,
                    remove_rotation_discontinuities=False)

