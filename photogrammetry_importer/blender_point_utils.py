import bpy

from photogrammetry_importer.blender_utils import add_obj
from photogrammetry_importer.stop_watch import StopWatch

def add_points_as_mesh(op, points, add_points_as_particle_system, mesh_type, point_extent, add_particle_color_emission, reconstruction_collection):
    op.report({'INFO'}, 'Adding Points: ...')
    stop_watch = StopWatch()
    particle_obj_name = "Particle Shape" 
    point_cloud_obj_name = "Point Cloud"
    point_cloud_mesh = bpy.data.meshes.new(point_cloud_obj_name)
    point_cloud_mesh.update()
    point_cloud_mesh.validate()

    point_world_coordinates = [tuple(point.coord) for point in points]

    point_cloud_mesh.from_pydata(point_world_coordinates, [], [])
    point_cloud_obj = add_obj(point_cloud_mesh, point_cloud_obj_name, reconstruction_collection)

    if add_points_as_particle_system:
        op.report({'INFO'}, 'Representing Points in the Point Cloud with Meshes: True')
        op.report({'INFO'}, 'Mesh Type: ' + str(mesh_type))

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
        
        if 'Image Texture' in node_tree.nodes:
            image_texture_node = node_tree.nodes['Image Texture']
        else:
            image_texture_node = node_tree.nodes.new("ShaderNodeTexImage")

        # Add links for base color and emission to improve color visibility
        node_tree.links.new(
            image_texture_node.outputs['Color'], 
            principled_bsdf_node.inputs['Base Color'])
        if add_particle_color_emission:
            node_tree.links.new(
                image_texture_node.outputs['Color'], 
                principled_bsdf_node.inputs['Emission'])
        
        vis_image_height = 1
        
        # To view the texture we set the height of the texture to vis_image_height 
        image = bpy.data.images.new(
            'ParticleColor', 
            len(point_world_coordinates), 
            vis_image_height)
        
        # working on a copy of the pixels results in a MASSIVE performance speed
        local_pixels = list(image.pixels[:])
        
        num_points = len(points)
        
        for j in range(vis_image_height):
            for point_index, point in enumerate(points):
                column_offset = point_index * 4     # (R,G,B,A)
                row_offset = j * 4 * num_points
                color = point.color 
                # Order is R,G,B, opacity
                local_pixels[row_offset + column_offset] = color[0] / 255.0
                local_pixels[row_offset + column_offset + 1] = color[1] / 255.0
                local_pixels[row_offset + column_offset + 2] = color[2] / 255.0
                # opacity (0 = transparent, 1 = opaque)
                #local_pixels[row_offset + column_offset + 3] = 1.0    # already set by default   
            
        image.pixels = local_pixels[:] 
        
        image_texture_node.image = image
        particle_info_node = node_tree.nodes.new('ShaderNodeParticleInfo')
        divide_node = node_tree.nodes.new('ShaderNodeMath')
        divide_node.operation = 'DIVIDE'
        node_tree.links.new(
            particle_info_node.outputs['Index'], 
            divide_node.inputs[0])
        divide_node.inputs[1].default_value = num_points
        shader_node_combine = node_tree.nodes.new('ShaderNodeCombineXYZ')
        node_tree.links.new(
            divide_node.outputs['Value'], 
            shader_node_combine.inputs['X'])
        node_tree.links.new(
            shader_node_combine.outputs['Vector'], 
            image_texture_node.inputs['Vector'])
        
        if len(point_cloud_obj.particle_systems) == 0:
            point_cloud_obj.modifiers.new("particle sys", type='PARTICLE_SYSTEM')
            particle_sys = point_cloud_obj.particle_systems[0]
            settings = particle_sys.settings
            settings.type = 'HAIR'
            settings.use_advanced_hair = True
            settings.emit_from = 'VERT'
            settings.count = len(point_world_coordinates)
            # The final object extent is hair_length * obj.scale 
            settings.hair_length = 100           # This must not be 0
            settings.use_emit_random = False
            settings.render_type = 'OBJECT'
            settings.instance_object = particle_obj
            
        bpy.context.view_layer.update()
    else:
        op.report({'INFO'}, 'Representing Points in the Point Cloud with Meshes: False')
    op.report({'INFO'}, 'Duration: ' + str(stop_watch.get_elapsed_time()))
    op.report({'INFO'}, 'Adding Points: Done')
    return point_cloud_obj.name
