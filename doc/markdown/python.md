## Addon Usage Within Python

There are two ways to access the functionality of the addon with Blender's Python console / text editor (after installation and activation of the addon):
* Import the addon as Python module
* Call the appropriate operator registered in bpy.ops.import_scene 

### Option 1: Import the addon as Python module

According to the [documentation](https://docs.blender.org/api/blender_python_api_current/info_overview.html#addons): 
> The only difference between addons and built-in Python modules is that addons must contain a bl_info variable

Therefore, after installation and activation one can import different classes etc. using Pythons standard import syntax.
For example:
```
from photogrammetry_importer.camera import Camera
from photogrammetry_importer.file_handler.colmap_file_handler import ColmapFileHandler
```

### Option 2: Call the appropriate operator registered in bpy.ops.import_scene

In Blender open the `Python Console` and use `Tabulator` to list the available operators with corresponding parameters, i.e.
```
>>> bpy.ops.import_scene.<TABULATOR>
>>> bpy.ops.import_scene.
                        colmap_model(
                        fbx(
                        gltf(
                        meshroom_sfm_json(
                        nvm(
                        obj(
                        open3d_log_json(
                        openmvg_json(
                        ply(
                        x3d(
```
Or use `Tabulator` with a specific function, e.g. `ply()`, to show the corresponding parameters.

```
>>> bpy.ops.import_scene.ply(<TABULATOR>
>>> bpy.ops.import_scene.ply(
ply()
bpy.ops.import_scene.ply(import_points=True, draw_points_with_gpu=False, add_points_as_particle_system=True, mesh_type='CUBE', point_extent=0.01, add_particle_color_emission=True, set_particle_color_flag=False, particle_overwrite_color=(0, 1, 0), path_to_transformations="", filepath="", directory="", filter_glob="*.ply")
Import a PLY file as point cloud
```

