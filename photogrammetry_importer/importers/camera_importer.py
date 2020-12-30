import math
import bpy
from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    FloatVectorProperty,
)

from photogrammetry_importer.importers.camera_utility import (
    add_cameras,
    adjust_render_settings_if_possible,
)
from photogrammetry_importer.importers.camera_animation_utility import (
    add_camera_animation,
)
from photogrammetry_importer.types.camera import Camera

from photogrammetry_importer.blender_utility.logging_utility import log_report


class CameraImporter:
    """Importer for cameras and corresponding image information."""

    use_workspace_images: BoolProperty(
        name="Use Workspace Images",
        description="If selected, use the (undistorted) images in the"
        " workspace (if available). Otherwise use the images in the default"
        " image path.",
        default=True,
    )

    image_fp_items = [
        (Camera.IMAGE_FP_TYPE_NAME, "File Name", "", 1),
        (Camera.IMAGE_FP_TYPE_RELATIVE, "Relative Path", "", 2),
        (Camera.IMAGE_FP_TYPE_ABSOLUTE, "Absolute Path", "", 3),
    ]
    image_fp_type: EnumProperty(
        name="Image File Path Type",
        description="Choose how image file paths are treated, "
        "i.e. absolute path, relative path or file name",
        items=image_fp_items,
    )
    image_dp: StringProperty(
        name="Image Directory",
        description="Assuming that the SfM reconstruction result is "
        "located in <some/path/rec.ext> or <some/path/rec_directory>. "
        "The addons uses either <some/path/images> (if available) "
        "or <some/path> as default image path. For MVS reconstruction "
        "results of Colmap, Meshroom or MVE the addon may or may not "
        "search for the images inside the corresponding workspace",
        # Can not use subtype='DIR_PATH' while importing another file
        # (i.e. nvm)
        default="",
    )
    import_cameras: BoolProperty(
        name="Import Cameras", description="Import Cameras", default=True
    )
    default_width: IntProperty(
        name="Default Width",
        description="Width, which will be used used if corresponding "
        "image is not found",
        default=-1,
    )
    default_height: IntProperty(
        name="Default Height",
        description="Height, which will be used used if corresponding "
        "image is not found",
        default=-1,
    )
    default_focal_length: FloatProperty(
        name="Focal length in pixel",
        description="Value for missing focal length in LOG (Open3D) file. ",
        default=float("nan"),
    )
    default_pp_x: FloatProperty(
        name="Principal Point X Component",
        description="Principal Point X Component, which will be used if "
        "not contained in the NVM (VisualSfM) / LOG (Open3D) file. If no "
        "value is provided, the principal point is set to the image "
        "center",
        default=float("nan"),
    )
    default_pp_y: FloatProperty(
        name="Principal Point Y Component",
        description="Principal Point Y Component, which will be used if "
        "not contained in the NVM (VisualSfM) / LOG (Open3D) file. If no "
        "value is provided, the principal point is set to the image "
        "center",
        default=float("nan"),
    )
    add_background_images: BoolProperty(
        name="Add a Background Image for each Camera",
        description="The background image is only visible by viewing the "
        "scene from a specific camera",
        default=True,
    )
    add_image_planes: BoolProperty(
        name="Add an Image Plane for each Camera",
        description="Add an Image Plane for each Camera - only for "
        "non-panoramic cameras",
        default=False,
    )
    add_image_plane_emission: BoolProperty(
        name="Add Image Plane Color Emission",
        description="Add image plane color emission to increase the "
        "visibility of the image planes",
        default=True,
    )
    image_plane_transparency: FloatProperty(
        name="Image Plane Transparency Value",
        description="Transparency value of the image planes: "
        "0 = invisible, 1 = opaque",
        default=0.5,
        min=0,
        max=1,
    )
    add_depth_maps_as_point_cloud: BoolProperty(
        name="Add Depth Maps (EXPERIMENTAL)",
        description="Add the depth map (if available) as point cloud "
        "for each Camera",
        default=False,
    )
    use_default_depth_map_color: BoolProperty(
        name="Use Default Depth Map Color",
        description="If not selected, each depth map is colorized with "
        "a different (random) color",
        default=False,
    )
    depth_map_default_color: FloatVectorProperty(
        name="Depth Map Color",
        description="Depth map color",
        subtype="COLOR",
        size=3,  # RGBA colors are not compatible with the GPU Module
        default=(0.0, 1.0, 0.0),
        min=0.0,
        max=1.0,
    )
    depth_map_display_sparsity: IntProperty(
        name="Depth Map Display Sparsity",
        description="Adjust the sparsity of the depth maps. A value of 10 "
        "means that every 10th depth map value is converted to a 3D point",
        default=10,
        min=1,
    )
    depth_map_id_or_name_str: StringProperty(
        name="Depth Map IDs or Names to Display",
        description="A list of camera indices or names (separated by "
        "whitespaces) used to select the depth maps, which will be "
        "displayed as point clouds. If no indices are provided, all "
        "depth maps are shown. The names must not contain whitespaces",
        default="",
    )
    add_camera_motion_as_animation: BoolProperty(
        name="Add Camera Motion as Animation",
        description="Add an animation reflecting the camera motion. The "
        "order of the cameras is determined by the corresponding file "
        "name",
        default=True,
    )
    animation_frame_source: EnumProperty(
        name="Use original frames",
        items=(
            ("ORIGINAL", "Original Frames", ""),
            ("ADJUSTED", "Adjusted Frames", ""),
        ),
    )
    add_animated_camera_background_images: BoolProperty(
        name="Add Background Images for the Animated Camera",
        description="The background images are only visible by viewing the "
        "scene from the animated camera at the corresponding time step",
        default=True,
    )
    reorganize_undistorted_images: BoolProperty(
        name="Reorganize Undistorted Workspace Images",
        description="Rename the undistorted images according to the original"
        " image names and write them to a single directory. Certain libraries"
        " such as Meshroom or MVE rename or move the undistorted images to"
        " different directories. Thus, the reversal is necessary to use the"
        " images as background sequence for the animated camera."
        " WARNING: This will write a copy of the corresponding images to the"
        " workspace directory",
        default=True,
    )
    number_interpolation_frames: IntProperty(
        name="Number of Frames Between two Reconstructed Cameras",
        description="The poses of the animated camera are interpolated",
        default=0,
        min=0,
    )

    interpolation_items = [
        ("LINEAR", "LINEAR", "", 1),
        ("BEZIER", "BEZIER", "", 2),
        ("SINE", "SINE", "", 3),
        ("QUAD", "QUAD", "", 4),
        ("CUBIC", "CUBIC", "", 5),
        ("QUART", "QUART", "", 6),
        ("QUINT", "QUINT", "", 7),
        ("EXPO", "EXPO", "", 8),
        ("CIRC", "CIRC", "", 9),
        ("BACK", "BACK", "", 10),
        ("BOUNCE", "BOUNCE", "", 11),
        ("ELASTIC", "ELASTIC", "", 12),
        ("CONSTANT", "CONSTANT", "", 13),
    ]
    interpolation_type: EnumProperty(
        name="Interpolation Type",
        description="Blender string that defines the type of the "
        "interpolation",
        items=interpolation_items,
    )

    consider_missing_cameras_during_animation: BoolProperty(
        name="Adjust Frame Numbers of Camera Animation",
        description="Assume there are three consecutive images A,B and "
        "C, but only A and C have been reconstructed. This option "
        "adjusts the frame number of C and the number of interpolation "
        "frames between camera A and C",
        default=True,
    )

    remove_rotation_discontinuities: BoolProperty(
        name="Remove Rotation Discontinuities",
        description="The addon uses quaternions q to represent the "
        "rotation. A quaternion q and its negative -q describe the same "
        "rotation. This option allows to remove different signs",
        default=True,
    )

    suppress_distortion_warnings: BoolProperty(
        name="Suppress Distortion Warnings",
        description="Radial distortion might lead to incorrect alignments "
        "of cameras and points. Enable this option to suppress "
        "corresponding warnings. If possible, consider to re-compute the "
        "reconstruction using a camera model without radial distortion",
        default=False,
    )

    adjust_render_settings: BoolProperty(
        name="Adjust Render Settings",
        description="Adjust the render settings according to the "
        "corresponding images - all images have to be captured with the "
        "same device. If disabled the visualization of the camera cone "
        "in 3D view might be incorrect",
        default=True,
    )

    camera_extent: FloatProperty(
        name="Initial Camera Extent (in Blender Units)",
        description="Initial Camera Extent (Visualization)",
        default=1,
    )

    def draw_camera_options(
        self,
        layout,
        draw_workspace_image_usage=False,
        reorganize_undistorted_images=False,
        draw_image_fp=True,
        draw_depth_map_import=False,
        draw_image_size=False,
        draw_principal_point=False,
        draw_focal_length=False,
        draw_everything=False,
    ):
        """Draw camera import options."""
        camera_box = layout.box()

        if draw_workspace_image_usage or draw_everything:
            camera_box.prop(self, "use_workspace_images")

        if draw_image_fp or draw_everything:
            camera_box.prop(self, "image_fp_type")
            if self.image_fp_type in ["NAME", "RELATIVE"] or draw_everything:
                camera_box.prop(self, "image_dp")

        if (
            draw_focal_length
            or draw_image_size
            or draw_principal_point
            or draw_everything
        ):
            image_box = camera_box.box()
            if draw_focal_length or draw_everything:
                image_box.prop(self, "default_focal_length")
            if draw_image_size or draw_everything:
                image_box.prop(self, "default_width")
                image_box.prop(self, "default_height")
            if draw_principal_point or draw_everything:
                image_box.prop(self, "default_pp_x")
                image_box.prop(self, "default_pp_y")

        import_camera_box = camera_box.box()
        import_camera_box.prop(self, "import_cameras")
        if self.import_cameras or draw_everything:
            import_camera_box.prop(self, "camera_extent")
            import_camera_box.prop(self, "add_background_images")

            image_plane_box = import_camera_box.box()
            image_plane_box.prop(self, "add_image_planes")
            if self.add_image_planes or draw_everything:
                image_plane_box.prop(self, "add_image_plane_emission")
                image_plane_box.prop(self, "image_plane_transparency")

            if draw_depth_map_import or draw_everything:
                depth_map_box = import_camera_box.box()
                depth_map_box.prop(self, "add_depth_maps_as_point_cloud")
                if self.add_depth_maps_as_point_cloud or draw_everything:
                    depth_map_box.prop(self, "use_default_depth_map_color")
                    if self.use_default_depth_map_color or draw_everything:
                        depth_map_box.prop(self, "depth_map_default_color")
                    depth_map_box.prop(self, "depth_map_display_sparsity")
                    depth_map_box.prop(self, "depth_map_id_or_name_str")

        anim_box = camera_box.box()
        anim_box.prop(self, "add_camera_motion_as_animation")

        if self.add_camera_motion_as_animation or draw_everything:
            anim_box.row().prop(self, "animation_frame_source", expand=True)
            if self.animation_frame_source == "ORIGINAL" or draw_everything:
                anim_box.prop(self, "add_animated_camera_background_images")
                if reorganize_undistorted_images or draw_everything:
                    anim_box.prop(self, "reorganize_undistorted_images")
            if self.animation_frame_source == "ADJUSTED" or draw_everything:
                anim_box.prop(self, "number_interpolation_frames")
            anim_box.prop(self, "consider_missing_cameras_during_animation")
            anim_box.prop(self, "interpolation_type")
            anim_box.prop(self, "remove_rotation_discontinuities")

        camera_box.prop(self, "suppress_distortion_warnings")
        camera_box.prop(self, "adjust_render_settings")

    def set_intrinsics_of_cameras(self, cameras):
        """Set intrinsic parameters of cameras.

        This function should be overwritten, if the intrinsic parameters are
        not part of the reconstruction data (e.g. log file).
        """
        success = True
        return cameras, success

    def set_image_size_of_cameras(self, cameras):
        """Set image size of cameras.

        This function should be overwritten, if the image size is not part of
        the reconstruction data (e.g. nvm file).
        """
        success = True
        return cameras, success

    @staticmethod
    def _principal_points_initialized(cameras):
        principal_points_initialized = True
        for camera in cameras:
            if not camera.has_principal_point():
                principal_points_initialized = False
                break
        return principal_points_initialized

    @staticmethod
    def _set_principal_point_for_cameras(
        cameras, default_pp_x, default_pp_y, op=None
    ):

        if not math.isnan(default_pp_x) and not math.isnan(default_pp_y):
            log_report(
                "WARNING", "Setting principal points to default values!", op
            )
        else:
            log_report(
                "WARNING", "Setting principal points to image centers!", op
            )
            assert (
                cameras[0].width is not None and cameras[0].height is not None
            )
            default_pp_x = cameras[0].width / 2.0
            default_pp_y = cameras[0].height / 2.0

        for camera in cameras:
            if not camera.has_principal_point():
                camera.set_principal_point([default_pp_x, default_pp_y])

    def import_photogrammetry_cameras(self, cameras, parent_collection):
        """Import the cameras using the properties of this class."""
        if not self.import_cameras and not self.add_camera_motion_as_animation:
            return {"FINISHED"}

        cameras, success = self.set_image_size_of_cameras(cameras)
        if not success:
            return {"FINISHED"}

        cameras, success = self.set_intrinsics_of_cameras(cameras)
        if not success:
            return {"FINISHED"}

        # The principal point may be part of the reconstruction data
        if not self.__class__._principal_points_initialized(cameras):
            self.__class__._set_principal_point_for_cameras(
                cameras, self.default_pp_x, self.default_pp_y, self
            )

        if self.adjust_render_settings:
            adjust_render_settings_if_possible(cameras, op=self)

        if self.import_cameras:
            add_cameras(
                cameras,
                parent_collection,
                add_background_images=self.add_background_images,
                add_image_planes=self.add_image_planes,
                add_depth_maps_as_point_cloud=self.add_depth_maps_as_point_cloud,
                camera_scale=self.camera_extent,
                image_plane_transparency=self.image_plane_transparency,
                add_image_plane_emission=self.add_image_plane_emission,
                use_default_depth_map_color=self.use_default_depth_map_color,
                depth_map_default_color=self.depth_map_default_color,
                depth_map_display_sparsity=self.depth_map_display_sparsity,
                depth_map_id_or_name_str=self.depth_map_id_or_name_str,
                op=self,
            )

        if self.add_camera_motion_as_animation:
            add_camera_animation(
                cameras=cameras,
                parent_collection=parent_collection,
                animation_frame_source=self.animation_frame_source,
                add_background_images=self.add_animated_camera_background_images,
                reorganize_undistorted_images=self.reorganize_undistorted_images,
                number_interpolation_frames=self.number_interpolation_frames,
                interpolation_type=self.interpolation_type,
                remove_rotation_discontinuities=self.remove_rotation_discontinuities,
                consider_missing_cameras_during_animation=self.consider_missing_cameras_during_animation,
                image_dp=self.image_dp,
                image_fp_type=self.image_fp_type,
                op=self,
            )
        return {"FINISHED"}
