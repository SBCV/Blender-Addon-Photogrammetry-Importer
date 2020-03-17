import os
try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None

class ImageFileHandler(object):

    @staticmethod
    def parse_camera_image_files(cameras, default_width, default_height, op):
        op.report({'INFO'}, 'parse_camera_image_files: ')
        success = True 
        for camera in cameras:
            image_path = camera.get_absolute_fp()
            if PILImage is not None and os.path.isfile(image_path):
                # this does NOT load the data into memory -> should be fast!
                image = PILImage.open(image_path)
                camera.width, camera.height = image.size
            elif default_width > 0 and default_height > 0:
                camera.width = default_width
                camera.height = default_height
                op.report({'WARNING'}, 'Set width and height to provided default values! (' + str(default_width) + ', ' + str(default_height) + ')')
            else:
                if PILImage is None:
                    op.report({'ERROR'}, 'PIL/PILLOW is not installed. Can not read image from disc to get image size.')
                else:
                    op.report({'ERROR'}, 'Corresponding image not found at: ' + image_path)
                op.report({'ERROR'}, 'Invalid default values provided for width (' + str(default_width) + ') and height (' + str(default_height) + ')')
                if PILImage is None:
                    op.report({'ERROR'}, 'Adjust the default width/height values to import the NVM / LOG file.')
                else:
                    op.report({'ERROR'}, 'Adjust the image path or the default width/height values to import the NVM / LOG file.')
                success = False
                break

        op.report({'INFO'}, 'parse_camera_image_files: Done')
        return cameras, success