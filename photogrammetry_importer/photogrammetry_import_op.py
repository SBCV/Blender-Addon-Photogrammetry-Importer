import os
import numpy as np
import bpy

from photogrammetry_importer.point import Point
from photogrammetry_importer.blender_utils import principal_points_initialized
from photogrammetry_importer.blender_utils import set_principal_point_for_cameras
from photogrammetry_importer.blender_utils import adjust_render_settings_if_possible
from photogrammetry_importer.blender_utils import add_cameras
from photogrammetry_importer.blender_utils import add_camera_animation
from photogrammetry_importer.blender_utils import add_points_as_mesh
from photogrammetry_importer.file_handler.nvm_file_handler import NVMFileHandler
from photogrammetry_importer.file_handler.ply_file_handler import PLYFileHandler

# Notes:
#   http://sinestesia.co/blog/tutorials/using-blenders-filebrowser-with-python/
#       Nice blender tutorial
#   https://blog.michelanders.nl/2014/07/inheritance-and-mixin-classes-vs_13.html
#       - The class that is actually used as operator must inherit from bpy.types.Operator and ImportHelper
#       - Properties defined in the parent class, which inherits from bpy.types.Operator and ImportHelper
#         are not considered  
# https://blender.stackexchange.com/questions/717/is-it-possible-to-print-to-the-report-window-in-the-info-view
#   The color depends on the type enum: INFO gets green, WARNING light red, and ERROR dark red

from bpy.props import (CollectionProperty,
                       StringProperty,
                       BoolProperty,
                       EnumProperty,
                       FloatProperty,
                       IntProperty,
                       )

from bpy_extras.io_utils import (ImportHelper,
                                 ExportHelper,
                                 axis_conversion)


class CameraImportProperties():
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
        success = True
        return cameras, success

    def import_photogrammetry_cameras(self, cameras):
        if self.import_cameras or self.add_camera_motion_as_animation:
            cameras, success = self.enhance_camera_with_images(cameras)
            if success:
                # principal point information may be provided in the NVM file
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
                        path_to_images=self.path_to_images, 
                        add_image_planes=self.add_image_planes, 
                        camera_scale=self.camera_extent)
                if self.add_camera_motion_as_animation:
                    add_camera_animation(
                        self,
                        cameras,
                        self.number_interpolation_frames
                        )
            else:
                return {'FINISHED'}


class PointImportProperties():

    import_points: BoolProperty(
        name="Import Points",
        description = "Import Points", 
        default=True)
    add_points_as_particle_system: BoolProperty(
        name="Add Points as Particle System",
        description="Use a particle system to represent vertex positions with objects",
        default=True)
    mesh_items = [
        ("CUBE", "Cube", "", 1),
        ("SPHERE", "Sphere", "", 2),
        ("PLANE", "Plane", "", 3)
        ]
    mesh_type: EnumProperty(
        name="Mesh Type",
        description = "Select the vertex representation mesh type.", 
        items=mesh_items)
    point_extent: FloatProperty(
        name="Initial Point Extent (in Blender Units)", 
        description = "Initial Point Extent for meshes at vertex positions",
        default=0.01)
        
    def import_photogrammetry_points(self, points):
        if self.import_points:
            add_points_as_mesh(
                self, 
                points, 
                self.add_points_as_particle_system, 
                self.mesh_type, 
                self.point_extent)


class ImportNVM(CameraImportProperties, PointImportProperties, bpy.types.Operator, ImportHelper):
    
    """Load a NVM file"""
    bl_idname = "import_scene.nvm"
    bl_label = "Import NVM"
    bl_options = {'UNDO'}

    files: CollectionProperty(
        name="File Path",
        description="File path used for importing the NVM file",
        type=bpy.types.OperatorFileListElement)

    directory: StringProperty()

    filter_glob: StringProperty(default="*.nvm", options={'HIDDEN'})

    def enhance_camera_with_images(self, cameras):
        cameras, success = NVMFileHandler.parse_camera_image_files(
        cameras, self.path_to_images, self.default_width, self.default_height, self)
        return cameras, success

    def execute(self, context):
        paths = [os.path.join(self.directory, name.name)
                 for name in self.files]
        if not paths:
            paths.append(self.filepath)
            
        self.report({'INFO'}, 'paths: ' + str(paths))

        for path in paths:
            
            # by default search for the images in the nvm directory
            if self.path_to_images == '':
                self.path_to_images = os.path.dirname(path)
            
            cameras, points = NVMFileHandler.parse_nvm_file(path, self)
            
            self.report({'INFO'}, 'Number cameras: ' + str(len(cameras)))
            self.report({'INFO'}, 'Number points: ' + str(len(points)))
            
            self.import_photogrammetry_cameras(cameras)
            self.import_photogrammetry_points(points)

        return {'FINISHED'}

class ImportPLY(PointImportProperties, bpy.types.Operator, ImportHelper):

    """Load a PLY file"""
    bl_idname = "import_scene.ply"
    bl_label = "Import PLY"
    bl_options = {'UNDO'}

    files: CollectionProperty(
        name="File Path",
        description="File path used for importing the PLY file",
        type=bpy.types.OperatorFileListElement)

    directory: StringProperty()

    filter_glob: StringProperty(default="*.ply", options={'HIDDEN'})

    def execute(self, context):
        paths = [os.path.join(self.directory, name.name)
                 for name in self.files]
        if not paths:
            paths.append(self.filepath)
            
        self.report({'INFO'}, 'paths: ' + str(paths))

        for path in paths:
            points = PLYFileHandler.parse_ply_file(path)
            self.report({'INFO'}, 'Number points: ' + str(len(points)))
            self.import_photogrammetry_points(points)

        return {'FINISHED'}

