from photogrammetry_importer.file_handlers.image_file_handler import (
    ImageFileHandler,
)
from photogrammetry_importer.utility.blender_logging_utility import log_report


def set_image_size_for_cameras(cameras, default_width, default_height, op):
    """ Set image sizes for cameras and return a boolean. """

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
