import os
try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None

class ImageFileHandler(object):

    @staticmethod
    def parse_camera_image_file(image_path, default_width, default_height, op):
        if PILImage is not None and os.path.isfile(image_path):
            # this does NOT load the data into memory -> should be fast!
            image = PILImage.open(image_path)
            width, height = image.size
            success = True
        elif default_width > 0 and default_height > 0:
            width = default_width
            height = default_height
            op.report({'WARNING'}, 'Set width and height to provided default values! (' + str(default_width) + ', ' + str(default_height) + ')')
            success = True
        else:
            if PILImage is None:
                op.report({'ERROR'}, 'PIL/PILLOW is not installed. Can not read image from disc to get image size.')
            else:
                op.report({'ERROR'}, 'Corresponding image not found at: ' + image_path)
            op.report({'ERROR'}, 'Invalid default values provided for width (' + str(default_width) + ') and height (' + str(default_height) + ')')
            if PILImage is None:
                op.report({'ERROR'}, 'Adjust the default width/height values to import the NVM / LOG / MVE file.')
            else:
                op.report({'ERROR'}, 'Adjust the image path or the default width/height values to import the NVM / LOG file.')
            width = None
            height = None
            success = False
        return success, width, height

    @staticmethod
    def parse_camera_image_files(cameras, default_width, default_height, op):
        op.report({'INFO'}, 'parse_camera_image_files: ')
        success = True 
        for camera in cameras:
            image_path = camera.get_absolute_fp()
            success, width, height = ImageFileHandler.parse_camera_image_file(
                image_path, default_width, default_height, op)
            camera.width = width
            camera.height = height
            if not success:
                break
        op.report({'INFO'}, 'parse_camera_image_files: Done')
        return cameras, success