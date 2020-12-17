from photogrammetry_importer.blender_utility.logging_utility import log_report


def set_image_size_for_cameras(
    cameras, default_width, default_height, op=None
):
    """Set image sizes for cameras and return a boolean."""

    from photogrammetry_importer.file_handlers.image_file_handler import (
        ImageFileHandler,
    )

    log_report("INFO", "set_image_size_for_cameras: ", op)
    success = True
    for camera in cameras:
        image_fp = camera.get_absolute_fp()
        success, width, height = ImageFileHandler.read_image_size(
            image_fp, default_width, default_height, op
        )
        camera.width = width
        camera.height = height
        if not success:
            break
    log_report("INFO", "set_image_size_for_cameras: Done", op)
    return success
