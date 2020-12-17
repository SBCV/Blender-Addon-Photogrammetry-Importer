import os
import bpy


def save_image_to_disk(image_name, file_path, save_alpha=True):
    """Save a Blender image to disk."""

    file_ext = os.path.splitext(file_path)[1]
    # https://docs.blender.org/api/current/bpy.types.Image.html#bpy.types.Image.file_format
    file_format = file_ext[1:].upper()
    if file_format == "JPG":
        file_format = "JPEG"
    assert file_format in ["BPM", "PNG", "JPEG", "OPEN_EXR", "HDR", "TIFF"]

    scene = bpy.context.scene
    settings = scene.render.image_settings

    # Backup previous settings
    previous_file_format = settings.file_format
    if previous_file_format == "FFMPEG":
        output_settings = scene.render.ffmpeg
    else:
        output_settings = scene.render.image_settings
    previous_settings_dict = {}
    for prop in output_settings.bl_rna.properties:
        if not prop.is_readonly:
            key = prop.identifier
            previous_settings_dict[key] = getattr(output_settings, key)

    # Apply the new settings. This modifies the "output_settings" variable.
    settings.file_format = file_format
    if save_alpha and file_format in ["PNG", "OPEN_EXR", "TIFF"]:
        settings.color_mode = "RGBA"
    else:
        settings.color_mode = "RGB"

    # Perform the rendering
    bpy.data.images[image_name].save_render(file_path)

    # Restore previous settings
    settings.file_format = previous_file_format
    for key in previous_settings_dict:
        setattr(output_settings, key, previous_settings_dict[key])
