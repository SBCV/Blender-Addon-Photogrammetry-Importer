import bpy


def add_empty(empty_name, collection=None):
    """Add an empty to the scene."""
    if collection is None:
        collection = bpy.context.collection
    empty_obj = bpy.data.objects.new(empty_name, None)
    collection.objects.link(empty_obj)
    return empty_obj


def add_obj(data, obj_name, collection=None):
    """Add an object to the scene."""
    if collection is None:
        collection = bpy.context.collection

    new_obj = bpy.data.objects.new(obj_name, data)
    collection.objects.link(new_obj)
    new_obj.select_set(state=True)

    if (
        bpy.context.view_layer.objects.active is None
        or bpy.context.view_layer.objects.active.mode == "OBJECT"
    ):
        bpy.context.view_layer.objects.active = new_obj
    return new_obj


def add_collection(collection_name, parent_collection=None):
    """Add a collection to the scene."""
    if parent_collection is None:
        parent_collection = bpy.context.collection

    new_collection = bpy.data.collections.new(collection_name)
    parent_collection.children.link(new_collection)

    return new_collection
