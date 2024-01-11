import bpy


def add_color_emission_to_material(mesh_obj):
    """Add color emmision for the given mesh to improve the visibility."""
    for material in mesh_obj.data.materials:
        node_tree = material.node_tree
        if "Principled BSDF" not in node_tree.nodes:  # is created by default
            break
        principled_bsdf_node = node_tree.nodes["Principled BSDF"]
        link = principled_bsdf_node.inputs["Base Color"].links[0]
        input_socket = link.from_socket

        node_tree.links.new(
            input_socket,
            principled_bsdf_node.inputs["Emission Color"],
        )


def add_mesh_vertex_color_material(
    mesh_obj,
    mesh_material_name,
    add_mesh_color_emission,
):
    """Add a material with vertex colors to the given mesh."""
    material = bpy.data.materials.new(name=mesh_material_name)
    mesh_obj.data.materials.append(material)

    # Enable cycles - otherwise the material has no nodes
    bpy.context.scene.render.engine = "CYCLES"
    material.use_nodes = True
    node_tree = material.node_tree

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

    attribute_node = node_tree.nodes.new("ShaderNodeAttribute")
    # Use the vertex colors (stored in "Col") as colors
    attribute_node.attribute_name = "Col"
    node_tree.links.new(
        attribute_node.outputs["Color"],
        principled_bsdf_node.inputs["Base Color"],
    )
    if add_mesh_color_emission:
        node_tree.links.new(
            attribute_node.outputs["Color"],
            principled_bsdf_node.inputs["Emission Color"],
        )
