import bpy

from bpy.props import (StringProperty,
                       BoolProperty,
                       FloatProperty,
                       IntProperty)

from photogrammetry_importer.blender_utils import principal_points_initialized
from photogrammetry_importer.blender_utils import set_principal_point_for_cameras
from photogrammetry_importer.blender_utils import adjust_render_settings_if_possible

from photogrammetry_importer.blender_utils import add_cameras
from photogrammetry_importer.blender_utils import add_camera_animation

class CameraImportProperties():
    """ This class encapsulates Blender UI properties that are required to visualize the reconstructed cameras correctly. """
    import_cameras: BoolProperty(
        name="Import Cameras",
        description = "Import Cameras", 
        default=True)
    default_width: IntProperty(
        name="Default Width",
        description = "Width, which will be used used if corresponding image is not found.", 
        default=-1)
    default_height: IntProperty(
        name="Default Height", 
        description = "Height, which will be used used if corresponding image is not found.",
        default=-1)
    default_pp_x: FloatProperty(
        name="Principal Point X Component",
        description = "Principal Point X Component, which will be used if not contained in the NVM file. " + \
                      "If no value is provided, the principal point is set to the image center.", 
        default=float('nan'))
    default_pp_y: FloatProperty(
        name="Principal Point Y Component", 
        description = "Principal Point Y Component, which will be used if not contained in the NVM file. " + \
                      "If no value is provided, the principal point is set to the image center.", 
        default=float('nan'))
    add_image_planes: BoolProperty(
        name="Add an Image Plane for each Camera",
        description = "Add an Image Plane for each Camera", 
        default=True)
    path_to_images: StringProperty(
        name="Image Directory",
        description = "Path to the directory of images. If no path is provided, the paths in the nvm file are used.", 
        default="",
        # Can not use subtype='DIR_PATH' while importing another file (i.e. .nvm)
        )
    add_image_plane_emission: BoolProperty(
        name="Add image plane color emission",
        description = "Add image plane color emission to increase the visibility of the image planes.", 
        default=True)
    image_plane_transparency: FloatProperty(
        name="Image plane transparency value", 
        description = "Transparency value of the image planes: 0 = invisible, 1 = opaque.",
        default=0.5,
        min=0,
        max=1)
    add_camera_motion_as_animation: BoolProperty(
        name="Add Camera Motion as Animation",
        description = "Add an animation reflecting the camera motion. The order of the cameras is determined by the corresponding file name.", 
        default=True)
    number_interpolation_frames: IntProperty(
        name="Number of frames between two reconstructed cameras.",
        description = "The poses of the animated camera are interpolated.", 
        default=0,
        min=0)
    adjust_render_settings: BoolProperty(
        name="Adjust Render Settings",
        description = "Adjust the render settings according to the corresponding images. "  +
                      "All images have to be captured with the same device). " +
                      "If disabled the visualization of the camera cone in 3D view might be incorrect.", 
        default=True)
    camera_extent: FloatProperty(
        name="Initial Camera Extent (in Blender Units)", 
        description = "Initial Camera Extent (Visualization)",
        default=1)

    def enhance_camera_with_images(self, cameras):
        # This function should be overwritten, 
        # if image size is not part of the reconstruction data
        # (e.g. nvm file)
        success = True
        return cameras, success

    def import_photogrammetry_cameras(self, cameras, parent_collection):
        if self.import_cameras or self.add_camera_motion_as_animation:
            cameras, success = self.enhance_camera_with_images(cameras)
            if success:
                # The principal point information may be provided in the reconstruction data
                if not principal_points_initialized(cameras):
                    set_principal_point_for_cameras(
                        cameras, 
                        self.default_pp_x,
                        self.default_pp_y,
                        self)
                
                if self.adjust_render_settings:
                    adjust_render_settings_if_possible(
                        self, 
                        cameras)

                if self.import_cameras:
                    add_cameras(
                        self, 
                        cameras, 
                        parent_collection,
                        path_to_images=self.path_to_images, 
                        add_image_planes=self.add_image_planes, 
                        camera_scale=self.camera_extent,
                        image_plane_transparency=self.image_plane_transparency,
                        add_image_plane_emission=self.add_image_plane_emission)

                if self.add_camera_motion_as_animation:
                    add_camera_animation(
                        self,
                        cameras,
                        parent_collection,
                        self.number_interpolation_frames)
            else:
                return {'FINISHED'}