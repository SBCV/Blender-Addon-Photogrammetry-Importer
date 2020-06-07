## Import

**Errors, help and logging information during import / export is shown in the `Info` area. Check this output, if nothing is imported. Probably the default width and height values are not set (see below).**

### General
In Blender use File/Import/\<Import Function\> to import the corresponding file. 
<img src="https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/import_file_formats.jpg" width="400">

For each camera one can add the corresponding image plane. Pillow is required to read the images from disc. Use the import dialog to adjust the `image path`. By default the addon searches for the images in the in the folder where the reconstruction file is located. **This addon uses the node system of Cycles to visualize the image planes. Thus, the addon switches automatically to Cycles, if image planes are added.** 

There is an option to represent the point cloud with a particle system. This allows you to render the point cloud. A single texture is used to store the color of all particles. **The color of the points / textures of the images are visible, if "Cycles Render" is selected and the 3D view is set to "Material".** Eevee does not (yet) support `particle info` nodes. (See [here](https://docs.blender.org/manual/es/dev/render/eevee/materials/nodes_support.html) for more information.) Thus, it is currently **not possible** to render point clouds with individual particle colors **in Eevee**. 

### NVM
The addon automatically looks for the fixed calibration line in the NVM file (i.e. `NVM_V3 FixedK fx cx fy cy r`  (first line)).
Without the fixed calibration line the addon assumes that the principal point is at the image center. NVM files contain no information about the size of the images. Use the import dialog to adjust the `image path` to automatically read the image size from disc or set the default `width` and `height` values.

### OpenMVG JSON
The OpenMVG `JSON` files contain no color information. The addon uses the input images (if provided) to compute the color of the triangulated 3D points - this computation requires the optional Pillow dependency.

### Meshroom
By default Meshroom stores the Structure from Motion results (i.e. cameras and points) in Alembic (`*.abc`) files. Since parsing `*.abc` files requires building additional (heavy) dependencies, e.g. ![this](https://github.com/alembic/alembic) library, it is currently not supported by this addon.
However, one can add a ConvertSfMFormat node in Meshroom (see image below) to write the reconstruction result to `*.SfM` / `*.json` files. 
![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/meshroom_export_json.jpg)

In addition to `*.SfM` / `*.json` files the addon allows to import `*.mg` files, which allows to also import corresponding meshes. The addon prioritizes the output of recently added nodes (e.g. `ConvertSfMFormat3` has a higher priority than `ConvertSfMFormat`). For importing meshes the addon uses the following prioritization: first the output of `Texturing`, then the output of `Meshfiltering` and finally the output of `Meshing`. In order to import the original images corresponding to the `*.mg` file, one can set the import option `Image File Path Type` of the Blender-Addon to `Absolute Path`. To import the undistorted `*.exr` images set `Image File Path Type` to `File Name` and set `Image Directory` to the folder with the `*.exr` files.

### Regard3D
By default Regard3D stores the Structure from Motion results in `path/to/project/pictureset_0/matching_0/triangulation_0/sfm_data.bin`. Use [OpenMVG](https://github.com/openMVG/openMVG) to convert the `*.bin` to a `*.json` file with `openMVG_main_ConvertSfM_DataFormat -i "path/to/sfm_data.bin" -o "path/to/cameras.json"`. For Windows you can find the pre-built binaries [here](https://github.com/openMVG/openMVG/releases/).  

### Meshes
In order to view a reconstructed mesh with the corresponding sparse reconstruction (cameras and point cloud) import the files separately. When importing *.obj files make sure to adjust the corresponding import transform options. Set the `Forward` option to `Y Forward` and the `Up` option to `Z Up`.   

### Limitations
Blender supports only global render settings (which define the ratio of all cameras). If the reconstruction file contains cameras with different aspect ratios, it is not possible to visualize the camera cones correctly. Furthermore, radial distortions of the camera model used to compute the reconstruction will result in small misalignment of the cameras and the particle system in Blender.
