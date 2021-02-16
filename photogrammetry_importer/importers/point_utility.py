import bpy
import numpy as np
from mathutils import Vector

from photogrammetry_importer.types.point import Point
from photogrammetry_importer.blender_utility.object_utility import (
    add_collection,
    add_obj,
)
from photogrammetry_importer.utility.timing_utility import StopWatch
from photogrammetry_importer.blender_utility.logging_utility import log_report


def _copy_values_to_image(value_tripplets, image_name):
    """ Copy values to image pixels. """
    image = bpy.data.images[image_name]
    # working on a copy of the pixels results in a MASSIVE performance speed
    local_pixels = list(image.pixels[:])
    for value_index, tripplet in enumerate(value_tripplets):
        column_offset = value_index * 4  # (R,G,B,A)
        # Order is R,G,B, opacity
        local_pixels[column_offset] = tripplet[0]
        local_pixels[column_offset + 1] = tripplet[1]
        local_pixels[column_offset + 2] = tripplet[2]
        # opacity (0 = transparent, 1 = opaque)
        # local_pixels[column_offset + 3] = 1.0    # already set by default
    image.pixels = local_pixels[:]


def _compute_particle_color_texture(colors, name="ParticleColor"):
    # To view the texture we set the height of the texture to vis_image_height
    image = bpy.data.images.new(name=name, width=len(colors), height=1)

    _copy_values_to_image(colors, image.name)
    image = bpy.data.images[image.name]
    # https://docs.blender.org/api/current/bpy.types.Image.html#bpy.types.Image.pack
    image.pack()
    return image


def _create_particle_color_nodes(
    node_tree, colors, particle_overwrite_color=None
):

    if particle_overwrite_color is not None:
        if "RGB" in node_tree.nodes:
            particle_color_node = node_tree.nodes["RGB"]
        else:
            particle_color_node = node_tree.nodes.new("ShaderNodeRGB")

        rgba_vec = Vector(particle_overwrite_color).to_4d()  # creates a copy
        particle_color_node.outputs["Color"].default_value = rgba_vec

    else:
        if "Image Texture" in node_tree.nodes:
            particle_color_node = node_tree.nodes["Image Texture"]
        else:
            particle_color_node = node_tree.nodes.new("ShaderNodeTexImage")

        particle_color_node.image = _compute_particle_color_texture(colors)
        texture_size = len(colors)
        particle_color_node.interpolation = "Closest"

        particle_info_node = node_tree.nodes.new("ShaderNodeParticleInfo")

        # Idea: we use the particle idx to compute a texture coordinate

        # Shift the un-normalized texture coordinate by a half pixel
        shift_half_pixel_node = node_tree.nodes.new("ShaderNodeMath")
        shift_half_pixel_node.operation = "ADD"
        node_tree.links.new(
            particle_info_node.outputs["Index"],
            shift_half_pixel_node.inputs[0],
        )
        shift_half_pixel_node.inputs[1].default_value = 0.5

        # Compute normalized texture coordinates (value between 0 and 1)
        # by dividing by the number of particles
        divide_node = node_tree.nodes.new("ShaderNodeMath")
        divide_node.operation = "DIVIDE"
        node_tree.links.new(
            shift_half_pixel_node.outputs["Value"],
            divide_node.inputs[0],
        )
        divide_node.inputs[1].default_value = texture_size

        # Compute texture coordinate (x axis corresponds to particle idx)
        shader_node_combine = node_tree.nodes.new("ShaderNodeCombineXYZ")
        node_tree.links.new(
            divide_node.outputs["Value"], shader_node_combine.inputs["X"]
        )
        node_tree.links.new(
            shader_node_combine.outputs["Vector"],
            particle_color_node.inputs["Vector"],
        )

    return particle_color_node


def _add_particle_obj(
    colors,
    particle_obj_name,
    particle_material_name,
    particle_overwrite_color,
    add_particle_color_emission,
    mesh_type,
    point_extent,
    reconstruction_collection,
):
    # The default size of elements added with
    #   primitive_cube_add, primitive_uv_sphere_add, etc. is (2,2,2)
    point_scale = point_extent * 0.5

    bpy.ops.object.select_all(action="DESELECT")
    if mesh_type == "PLANE":
        bpy.ops.mesh.primitive_plane_add(size=point_scale)
    elif mesh_type == "CUBE":
        bpy.ops.mesh.primitive_cube_add(size=point_scale)
    elif mesh_type == "SPHERE":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=point_scale)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=point_scale)
    particle_obj = bpy.context.object
    particle_obj.name = particle_obj_name
    reconstruction_collection.objects.link(particle_obj)
    bpy.context.collection.objects.unlink(particle_obj)

    _add_particle_material(
        colors,
        particle_obj,
        particle_material_name,
        particle_overwrite_color,
        add_particle_color_emission,
    )

    return particle_obj


def _add_particle_material(
    colors,
    particle_obj,
    particle_material_name,
    particle_overwrite_color,
    add_particle_color_emission,
):
    material = bpy.data.materials.new(name=particle_material_name)
    particle_obj.data.materials.append(material)

    # Enable cycles - otherwise the material has no nodes
    bpy.context.scene.render.engine = "CYCLES"
    material.use_nodes = True
    node_tree = material.node_tree

    # Print all available nodes with:
    # bpy.data.materials['particle_material_name'].node_tree.nodes.keys()

    if "Material Output" in node_tree.nodes:  # is created by default
        material_output_node = node_tree.nodes["Material Output"]
    else:
        material_output_node = node_tree.nodes.new("ShaderNodeOutputMaterial")

    if "Principled BSDF" in node_tree.nodes:  # is created by default
        principled_bsdf_node = node_tree.nodes["Principled BSDF"]
    else:
        principled_bsdf_node = node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    node_tree.links.new(
        principled_bsdf_node.outputs["BSDF"],
        material_output_node.inputs["Surface"],
    )

    particle_color_node = _create_particle_color_nodes(
        node_tree, colors, particle_overwrite_color
    )

    # Add links for base color and emission to improve color visibility
    node_tree.links.new(
        particle_color_node.outputs["Color"],
        principled_bsdf_node.inputs["Base Color"],
    )
    if add_particle_color_emission:
        node_tree.links.new(
            particle_color_node.outputs["Color"],
            principled_bsdf_node.inputs["Emission"],
        )


def _add_particle_system_obj(
    coords, particle_obj, point_cloud_obj_name, reconstruction_collection
):
    point_cloud_mesh = bpy.data.meshes.new(point_cloud_obj_name)
    point_cloud_mesh.update()
    point_cloud_mesh.validate()
    point_cloud_mesh.from_pydata(coords, [], [])
    point_cloud_obj = add_obj(
        point_cloud_mesh, point_cloud_obj_name, reconstruction_collection
    )

    if len(point_cloud_obj.particle_systems) == 0:
        point_cloud_obj.modifiers.new("particle sys", type="PARTICLE_SYSTEM")
        particle_sys = point_cloud_obj.particle_systems[0]
        settings = particle_sys.settings
        settings.type = "HAIR"
        settings.use_advanced_hair = True
        settings.emit_from = "VERT"
        settings.count = len(coords)
        # The final object extent is hair_length * obj.scale
        settings.hair_length = 100  # This must not be 0
        settings.use_emit_random = False
        settings.render_type = "OBJECT"
        settings.instance_object = particle_obj
    return point_cloud_obj


def add_points_as_object_with_particle_system(
    points,
    reconstruction_collection,
    mesh_type="CUBE",
    point_extent=0.01,
    add_particle_color_emission=True,
    particle_overwrite_color=None,
    op=None,
):
    """Add a point cloud as particle system."""
    log_report("INFO", "Adding Points as Particle System: ...", op)
    stop_watch = StopWatch()

    # The particle systems in Blender do not work for large particle numbers
    # (see https://developer.blender.org/T81103). Thus, we represent large
    # point clouds with multiple smaller particle systems.
    max_number_particles = 10000

    particle_system_collection = add_collection(
        "Particle System", reconstruction_collection
    )

    point_cloud_obj_list = []
    for i in range(0, len(points), max_number_particles):

        particle_obj_name = f"Particle Shape {i}"
        particle_material_name = f"Point Cloud Material {i}"
        point_cloud_obj_name = f"Particle Point Cloud {i}"

        points_subset = points[i : i + max_number_particles]
        coords, colors = Point.split_points(
            points_subset, normalize_colors=True
        )

        particle_obj = _add_particle_obj(
            colors,
            particle_obj_name,
            particle_material_name,
            particle_overwrite_color,
            add_particle_color_emission,
            mesh_type,
            point_extent,
            particle_system_collection,
        )
        point_cloud_obj = _add_particle_system_obj(
            coords,
            particle_obj,
            point_cloud_obj_name,
            particle_system_collection,
        )
        point_cloud_obj_list.append(point_cloud_obj)

    bpy.context.view_layer.update()

    log_report("INFO", "Duration: " + str(stop_watch.get_elapsed_time()), op)
    log_report("INFO", "Adding Points as Particle System: Done", op)
    return point_cloud_obj_list


def add_points_as_mesh_vertices(points, reconstruction_collection, op=None):
    """Add a point cloud as mesh."""
    log_report("INFO", "Adding Points as Mesh: ...", op)
    stop_watch = StopWatch()
    point_cloud_obj_name = "Mesh Point Cloud"
    point_cloud_mesh = bpy.data.meshes.new(point_cloud_obj_name)
    point_cloud_mesh.update()
    point_cloud_mesh.validate()
    point_world_coordinates = [tuple(point.coord) for point in points]
    point_cloud_mesh.from_pydata(point_world_coordinates, [], [])
    point_cloud_obj = add_obj(
        point_cloud_mesh, point_cloud_obj_name, reconstruction_collection
    )

    log_report("INFO", "Duration: " + str(stop_watch.get_elapsed_time()), op)
    log_report("INFO", "Adding Points as Mesh: Done", op)
    return point_cloud_obj
