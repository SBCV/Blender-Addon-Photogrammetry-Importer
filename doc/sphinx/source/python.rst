***********************
Addon Usage with Python
***********************

There are two ways to access the functionality of the addon with Blender's Python console / text editor (after installation and activation of the addon):

* Import the addon as Python module
* Call the appropriate operator registered in bpy.ops.import_scene 

Option 1: Import the addon as Python module
===========================================

According to the `documentation <https://docs.blender.org/api/blender_python_api_current/info_overview.html#addons>`_: 

        `The only difference between addons and built-in Python modules is that addons must contain a bl_info variable`

Therefore, after installation and activation one can use Python's standard import syntax to import different classes and functions such as: ::

        from photogrammetry_importer.types.camera import Camera
        from photogrammetry_importer.file_handlers.colmap_file_handler import ColmapFileHandler
        from photogrammetry_importer.importers.point_utility import add_points_as_mesh_vertices

Example 1: Add points contained in a :code:`ply` file as a :code:`particle system`. ::

        import bpy
        from photogrammetry_importer.file_handlers.point_data_file_handler import PointDataFileHandler
        from photogrammetry_importer.blender_utility.object_utility import add_collection
        from photogrammetry_importer.importers.point_utility import add_points_as_mesh_vertices

        ifp = "path/to/Blender-Addon-Photogrammetry-Importer/examples/Example.ply"
        points = PointDataFileHandler.parse_point_data_file(ifp)
        reconstruction_collection = add_collection("Reconstruction Collection")
        add_points_as_mesh_vertices(
                points,
                reconstruction_collection=reconstruction_collection,
                add_mesh_to_point_geometry_nodes=True,
                point_radius=0.05,
                point_subdivisions=1,
                add_color_as_custom_property=True,
        )
        # Optionally, change the shading type to show the particle colors
        area = next(area for area in bpy.context.screen.areas if area.type == "VIEW_3D")
        space = next(space for space in area.spaces if space.type == "VIEW_3D")
        space.shading.type = "RENDERED"

Example 2: Use the intrinsic and extrinsic parameters of each reconstructed camera to render the corresponding point cloud via an :code:`off screen buffer` to disk. ::

        import os
        from photogrammetry_importer.file_handlers.colmap_file_handler import ColmapFileHandler
        from photogrammetry_importer.types.point import Point
        from photogrammetry_importer.blender_utility.object_utility import add_collection
        from photogrammetry_importer.importers.camera_utility import add_camera_object
        from photogrammetry_importer.opengl.utility import render_opengl_image
        from photogrammetry_importer.blender_utility.image_utility import save_image_to_disk

        # Make sure you've downloaded the corresponding images (i.e. the sceaux castle dataset)
        model_idp = "path/to/Blender-Addon-Photogrammetry-Importer/examples/colmap_example_model_bin"
        image_idp = "path/to/Blender-Addon-Photogrammetry-Importer/examples/images"
        odp = "path/to/output"

        # Parse the reconstruction
        cameras, points3D = ColmapFileHandler.parse_colmap_model_folder(model_idp, image_idp, image_fp_type="NAME")
        coords, colors = Point.split_points(points3D)

        # Render the point cloud for reach camera
        camera_collection = add_collection("Camera Collection")
        render_img_name = "render_result"
        for cam in cameras:
                cam_name = cam.get_file_name()
                print(f"Camera: {cam_name}")
                ofp = os.path.join(odp, cam_name)

                camera_object = add_camera_object(cam, cam_name, camera_collection)
                render_opengl_image(render_img_name, camera_object, coords, colors, point_size=10)
                save_image_to_disk(render_img_name, ofp, save_alpha=False)

Example 3: Use the animated camera to render the point cloud with :code:`Cycles`. ::

        import os
        import bpy
        from photogrammetry_importer.file_handlers.colmap_file_handler import ColmapFileHandler
        from photogrammetry_importer.blender_utility.object_utility import add_collection
        from photogrammetry_importer.importers.point_utility import add_points_as_object_with_particle_system
        from photogrammetry_importer.importers.camera_animation_utility import add_camera_animation
        from photogrammetry_importer.importers.camera_utility import adjust_render_settings_if_possible

        # Make sure you've downloaded the corresponding images (i.e. the sceaux castle dataset)
        model_idp = "path/to/Blender-Addon-Photogrammetry-Importer/examples/colmap_example_model_bin"
        image_idp = "path/to/Blender-Addon-Photogrammetry-Importer/examples/images"
        odp = "path/to/output"

        # Parse the reconstruction
        cameras, points3D = ColmapFileHandler.parse_colmap_model_folder(model_idp, image_idp, image_fp_type="NAME")

        # Add the reconstruction results
        reconstruction_collection = add_collection("Reconstruction Collection")
        add_points_as_object_with_particle_system(points3D, reconstruction_collection, point_extent=0.02)
        animated_camera_object = add_camera_animation(cameras, reconstruction_collection)

        # Adjust the render settings and render animation with Cycles
        adjust_render_settings_if_possible(cameras)
        bpy.context.scene.render.engine = "CYCLES"
        bpy.context.scene.cycles.device = "GPU"
        bpy.context.scene.render.filepath = os.path.join(odp, "")
        bpy.context.scene.camera = animated_camera_object
        bpy.ops.render.render(animation=True)



Option 2: Call the appropriate operator registered in bpy.ops.import_scene
==========================================================================

In Blender open the :code:`Python Console` and use :code:`Tabulator` to list the available operators with corresponding parameters, i.e. ::

        >>> bpy.ops.import_scene.<TABULATOR>
        >>> bpy.ops.import_scene.
                                colmap_model(
                                fbx(
                                gltf(
                                meshroom_sfm_json(
                                mve_folder(
                                obj(
                                open3d_log_json(
                                openmvg_json(
                                opensfm_json(
                                point_data(
                                visualsfm_nvm(
                                x3d(

Or use :code:`Tabulator` with a specific function, e.g. :code:`point_data()`, to show the corresponding parameters. ::

        >>> bpy.ops.import_scene.point_data(<TABULATOR>
        >>> bpy.ops.import_scene.point_data(
        point_data()
        bpy.ops.import_scene.point_data(
                import_points=True,
                point_cloud_display_sparsity=1,
                draw_points_with_gpu=True,
                add_points_to_point_cloud_handle=True,
                add_points_as_particle_system=False,
                mesh_type='CUBE',
                point_extent=0.01,
                add_particle_color_emission=True,
                set_particle_color_flag=False,
                particle_overwrite_color=(0, 1, 0),
                add_points_as_mesh_oject=False,
                adjust_clipping_distance=False,
                filepath="",
                directory="",
                filter_glob="*.ply;*.pcd;*.las;*.laz;*.asc;*.pts;*.csv")


Python Scripting with Blender
=============================

`VS Code <https://code.visualstudio.com>`_ with this `extension <https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development>`_ has many advantages over Blender's built-in text editor. `Here <https://www.youtube.com/watch?v=q06-hER7Y1Q>`_ is an introduction / tutorial video.

Note: When using `VS Code` to start Blender with a specific addon for the first time, it is sometimes necessary to run the command twice (i.e. within VS Code run `ctrl+shift+p / Blender: Start / path_to_Blender_executable`, then close Blender, then run `ctrl+shift+p / Blender: Start / path_to_Blender_executable` again).


