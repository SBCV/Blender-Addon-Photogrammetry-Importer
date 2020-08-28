import bpy
import numpy as np
from mathutils import Vector

from photogrammetry_importer.types.point import Point
from photogrammetry_importer.utility.blender_utility import add_obj
from photogrammetry_importer.utility.stop_watch import StopWatch
from photogrammetry_importer.utility.blender_logging_utility import log_report


def copy_values_to_image(value_tripplets, image_name):
    image = bpy.data.images[image_name]
    # working on a copy of the pixels results in a MASSIVE performance speed
    local_pixels = list(image.pixels[:])
    for value_index, tripplet in enumerate(value_tripplets):
        column_offset = value_index * 4     # (R,G,B,A)
        # Order is R,G,B, opacity
        local_pixels[column_offset] = tripplet[0]
        local_pixels[column_offset + 1] = tripplet[1]
        local_pixels[column_offset + 2] = tripplet[2]
        # opacity (0 = transparent, 1 = opaque)
        #local_pixels[column_offset + 3] = 1.0    # already set by default   
    image.pixels = local_pixels[:]


def compute_particle_coord_texture(coords, name='ParticleCoord'):

    image = bpy.data.images.new(
        name=name, 
        alpha=False,
        # is_data=True,
        float_buffer=True,
        width=len(coords), 
        height=1)

    copy_values_to_image(colors, image.name)
    image = bpy.data.images[image.name]
    # https://docs.blender.org/api/current/bpy.types.Image.html#bpy.types.Image.pack
    image.pack()
    return image

def compute_particle_color_texture(colors, name='ParticleColor'):
    # To view the texture we set the height of the texture to vis_image_height 
    image = bpy.data.images.new(
        name=name, 
        width=len(colors), 
        height=1)

    copy_values_to_image(colors, image.name)
    image = bpy.data.images[image.name]
    # https://docs.blender.org/api/current/bpy.types.Image.html#bpy.types.Image.pack
    image.pack()
    return image

def create_particle_color_nodes(node_tree, points, set_particle_color_flag, particle_overwrite_color=None):

    if set_particle_color_flag:
        assert particle_overwrite_color is not None
        if 'RGB' in node_tree.nodes:
            particle_color_node = node_tree.nodes['RGB']
        else:
            particle_color_node = node_tree.nodes.new("ShaderNodeRGB")  

        rgba_vec = Vector(particle_overwrite_color).to_4d() # creates a copy
        particle_color_node.outputs['Color'].default_value = rgba_vec

    else:
        if 'Image Texture' in node_tree.nodes:
            particle_color_node = node_tree.nodes['Image Texture']
        else:
            particle_color_node = node_tree.nodes.new("ShaderNodeTexImage")

        coords, colors = Point.split_points(points)
        particle_color_node.image = compute_particle_color_texture(colors)

        particle_info_node = node_tree.nodes.new('ShaderNodeParticleInfo')
        divide_node = node_tree.nodes.new('ShaderNodeMath')
        divide_node.operation = 'DIVIDE'
        node_tree.links.new(
            particle_info_node.outputs['Index'], 
            divide_node.inputs[0])
        divide_node.inputs[1].default_value = len(points)
        shader_node_combine = node_tree.nodes.new('ShaderNodeCombineXYZ')
        node_tree.links.new(
            divide_node.outputs['Value'], 
            shader_node_combine.inputs['X'])
        node_tree.links.new(
            shader_node_combine.outputs['Vector'], 
            particle_color_node.inputs['Vector'])

    return particle_color_node

def add_points_as_mesh( op, 
                        points, 
                        reconstruction_collection):
    log_report('INFO', 'Adding Points as Mesh: ...', op)
    stop_watch = StopWatch()
    point_cloud_obj_name = "Mesh Point Cloud"
    point_cloud_mesh = bpy.data.meshes.new(point_cloud_obj_name)
    point_cloud_mesh.update()
    point_cloud_mesh.validate()
    point_world_coordinates = [tuple(point.coord) for point in points]
    point_cloud_mesh.from_pydata(point_world_coordinates, [], [])
    point_cloud_obj = add_obj(point_cloud_mesh, point_cloud_obj_name, reconstruction_collection)

    log_report('INFO', 'Duration: ' + str(stop_watch.get_elapsed_time()), op)
    log_report('INFO', 'Adding Points as Mesh: Done', op)
    return point_cloud_obj.name

def add_points_as_particle_system(op, 
                                  points, 
                                  mesh_type, 
                                  point_extent, 
                                  add_particle_color_emission, 
                                  reconstruction_collection,
                                  set_particle_color_flag,
                                  particle_overwrite_color=None):
    log_report('INFO', 'Adding Points as Particle System: ...', op)
    stop_watch = StopWatch()
    particle_obj_name = "Particle Shape" 
    point_cloud_obj_name = "Particle Point Cloud"
    point_cloud_mesh = bpy.data.meshes.new(point_cloud_obj_name)
    point_cloud_mesh.update()
    point_cloud_mesh.validate()

    point_world_coordinates = [tuple(point.coord) for point in points]

    point_cloud_mesh.from_pydata(point_world_coordinates, [], [])
    point_cloud_obj = add_obj(point_cloud_mesh, point_cloud_obj_name, reconstruction_collection)

    log_report('INFO', 'Mesh Type: ' + str(mesh_type), op)

    # The default size of elements added with 
    #   primitive_cube_add, primitive_uv_sphere_add, etc. is (2,2,2)
    point_scale = point_extent * 0.5 

    bpy.ops.object.select_all(action='DESELECT')
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
        
    material_name = "PointCloudMaterial"
    material = bpy.data.materials.new(name=material_name)
    particle_obj.data.materials.append(material)
    
    # enable cycles, otherwise the material has no nodes
    bpy.context.scene.render.engine = 'CYCLES'
    material.use_nodes = True
    node_tree = material.node_tree

    # Print all available nodes with:
    # bpy.data.materials['material_name'].node_tree.nodes.keys()

    if 'Material Output' in node_tree.nodes:    # is created by default
        material_output_node = node_tree.nodes['Material Output']
    else:
        material_output_node = node_tree.nodes.new('ShaderNodeOutputMaterial')

    if 'Principled BSDF' in node_tree.nodes:       # is created by default
        principled_bsdf_node = node_tree.nodes['Principled BSDF']
    else:
        principled_bsdf_node = node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    node_tree.links.new(
        principled_bsdf_node.outputs['BSDF'], 
        material_output_node.inputs['Surface'])
    
    assert len(point_world_coordinates) == len(points)
    particle_color_node = create_particle_color_nodes(
        node_tree, points, set_particle_color_flag, particle_overwrite_color)

        # Add links for base color and emission to improve color visibility
    node_tree.links.new(
        particle_color_node.outputs['Color'], 
        principled_bsdf_node.inputs['Base Color'])
    if add_particle_color_emission:
        node_tree.links.new(
            particle_color_node.outputs['Color'], 
            principled_bsdf_node.inputs['Emission'])
    
    if len(point_cloud_obj.particle_systems) == 0:
        point_cloud_obj.modifiers.new("particle sys", type='PARTICLE_SYSTEM')
        particle_sys = point_cloud_obj.particle_systems[0]
        settings = particle_sys.settings
        settings.type = 'HAIR'
        settings.use_advanced_hair = True
        settings.emit_from = 'VERT'
        settings.count = len(points)
        # The final object extent is hair_length * obj.scale 
        settings.hair_length = 100           # This must not be 0
        settings.use_emit_random = False
        settings.render_type = 'OBJECT'
        settings.instance_object = particle_obj
        
    bpy.context.view_layer.update()

    log_report('INFO', 'Duration: ' + str(stop_watch.get_elapsed_time()), op)
    log_report('INFO', 'Adding Points as Particle System: Done', op)
    return point_cloud_obj.name
