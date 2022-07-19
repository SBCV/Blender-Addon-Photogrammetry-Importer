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
            shift_half_pixel_node.outputs["Value"], divide_node.inputs[0]
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
    """Add a point cloud as particle system.

    This method is deprecated. It is recommended to use
    :code:`add_points_as_mesh_vertices()` instead.
    """
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


def create_geometry_nodes_node_group():
    """Create a new node group for a geometry nodes modifier."""
    node_group = bpy.data.node_groups.new("GeometryNodes", "GeometryNodeTree")
    input_node = node_group.nodes.new("NodeGroupInput")
    input_node.outputs.new("NodeSocketGeometry", "Geometry")
    output_node = node_group.nodes.new("NodeGroupOutput")
    output_node.inputs.new("NodeSocketGeometry", "Geometry")
    node_group.links.new(
        input_node.outputs["Geometry"], output_node.inputs["Geometry"]
    )
    return node_group


def add_points_as_mesh_vertices(
    points,
    reconstruction_collection,
    add_mesh_to_point_geometry_nodes=True,
    point_radius=0.05,
    point_subdivisions=1,
    add_color_as_custom_property=True,
    op=None,
):
    """Add a point cloud as mesh."""
    log_report("INFO", "Adding Points as Mesh: ...", op)
    stop_watch = StopWatch()
    point_cloud_obj_name = "Mesh Point Cloud"
    point_cloud_mesh = bpy.data.meshes.new(point_cloud_obj_name)
    point_cloud_mesh.update()
    point_cloud_mesh.validate()
    coords, colors = Point.split_points(points, normalize_colors=False)
    point_cloud_mesh.from_pydata(coords, [], [])
    point_cloud_obj = add_obj(
        point_cloud_mesh, point_cloud_obj_name, reconstruction_collection
    )
    if add_mesh_to_point_geometry_nodes:
        # Add a point_color attribute to each vertex
        point_cloud_mesh.attributes.new(
            name="point_color", type="FLOAT_COLOR", domain="POINT"
        )
        _add_colors_to_vertices(point_cloud_mesh, colors, "point_color")

        geometry_nodes = point_cloud_obj.modifiers.new(
            "GeometryNodes", "NODES"
        )

        # https://blender.stackexchange.com/questions/249763/python-geometry-node-trees
        if not geometry_nodes.node_group:
            geometry_nodes.node_group = create_geometry_nodes_node_group()

        # The group_input and the group_output nodes are created by default
        group_input = geometry_nodes.node_group.nodes["Group Input"]
        group_output = geometry_nodes.node_group.nodes["Group Output"]

        # Add modifier inputs that are editable from the GUI, the order these are added is important
        geometry_nodes.node_group.inputs.new(
            "NodeSocketMaterial", "Point Color"
        )  # Input_2
        geometry_nodes.node_group.inputs.new(
            "NodeSocketFloat", "Point Radius"
        )  # Input_3
        geometry_nodes.node_group.inputs.new(
            "NodeSocketIntUnsigned", "Point Subdivisions"
        )  # Input_4
        geometry_nodes["Input_2"] = _get_color_from_attribute("point_color")
        geometry_nodes["Input_3"] = point_radius
        geometry_nodes["Input_4"] = point_subdivisions

        # Note: To determine the name required for new(...), create the
        # corresponding node with the gui and print the value of "bl_rna".
        # Or enable python tooltips under preferences > interface and hover
        # over a node in the add node dropdown
        mesh_to_points = geometry_nodes.node_group.nodes.new(
            "GeometryNodeMeshToPoints"
        )
        instance_on_points = geometry_nodes.node_group.nodes.new(
            "GeometryNodeInstanceOnPoints"
        )
        realize_instances = geometry_nodes.node_group.nodes.new(
            "GeometryNodeRealizeInstances"
        )
        sphere_marker = geometry_nodes.node_group.nodes.new(
            "GeometryNodeMeshIcoSphere"
        )
        set_material = geometry_nodes.node_group.nodes.new(
            "GeometryNodeSetMaterial"
        )

        geometry_nodes.node_group.links.new(
            group_input.outputs["Geometry"], mesh_to_points.inputs["Mesh"]
        )
        geometry_nodes.node_group.links.new(
            mesh_to_points.outputs["Points"],
            instance_on_points.inputs["Points"],
        )
        geometry_nodes.node_group.links.new(
            instance_on_points.outputs["Instances"],
            realize_instances.inputs["Geometry"],
        )
        geometry_nodes.node_group.links.new(
            realize_instances.outputs["Geometry"],
            group_output.inputs["Geometry"],
        )

        geometry_nodes.node_group.links.new(
            group_input.outputs["Point Radius"], sphere_marker.inputs["Radius"]
        )
        geometry_nodes.node_group.links.new(
            group_input.outputs["Point Subdivisions"],
            sphere_marker.inputs["Subdivisions"],
        )
        geometry_nodes.node_group.links.new(
            sphere_marker.outputs["Mesh"], set_material.inputs["Geometry"]
        )
        geometry_nodes.node_group.links.new(
            group_input.outputs["Point Color"], set_material.inputs["Material"]
        )
        geometry_nodes.node_group.links.new(
            set_material.outputs["Geometry"],
            instance_on_points.inputs["Instance"],
        )

    if add_color_as_custom_property:
        point_cloud_obj["colors"] = colors

    log_report("INFO", "Duration: " + str(stop_watch.get_elapsed_time()), op)
    log_report("INFO", "Adding Points as Mesh: Done", op)
    return point_cloud_obj


def _add_colors_to_vertices(mesh, colors, attribute_name):
    """Add a color attribute to each vertex of mesh."""
    if len(mesh.vertices) != len(colors):
        raise ValueError(
            f"Got {len(mesh.vertices)} vertices and {len(colors)} color values."
        )

    color_array = np.array(colors)
    color_array[:, :3] /= 255.0
    mesh.attributes[attribute_name].data.foreach_set(
        "color", color_array.reshape(-1)
    )


def _get_color_from_attribute(attribute_name):
    """Create a material that obtains its color from the specified attribute."""
    material = bpy.data.materials.new("color")
    material.use_nodes = True
    color_node = material.node_tree.nodes.new("ShaderNodeAttribute")
    color_node.attribute_name = attribute_name
    material.node_tree.links.new(
        color_node.outputs["Color"],
        material.node_tree.nodes["Principled BSDF"].inputs["Base Color"],
    )
    return material
