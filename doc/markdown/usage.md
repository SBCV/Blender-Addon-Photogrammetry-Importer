## Usage

**Errors, help and logging information during import / export is shown in the "Info" area. Check this output, if nothing is imported. Probably the default width and height values are not set (see below).**

### Import

#### General
In Blender use File/Import/\<Import Function\> to import the corresponding file. 

For each camera one can add the corresponding image plane. Pillow is required to read the images from disc. Use the import dialog to adjust the "image path". By default the addon searches for the images in the in the folder where the reconstruction file is located. **This addon uses the node system of Cycles to visualize the image planes. Thus, the addon switches automatically to Cycles, if image planes are added.** 

There is an option to represent the point cloud with a particle system. This allows you to render the point cloud. A single texture is used to store the color of all particles. **The color of the points / textures of the images are visible, if "Cycles Render" is selected and the 3D view is set to "Material".** Eevee does not (yet) support "particle info" nodes. (See [here](https://docs.blender.org/manual/es/dev/render/eevee/materials/nodes_support.html) for more information.) Thus, it is currently **not possible** to render point clouds with individual particle colors **in Eevee**. 

#### NVM
The addon automatically looks for the fixed calibration line in the NVM file (i.e. "NVM_V3 FixedK fx cx fy cy r"  (first line)).
Without the fixed calibration line the addon assumes that the principal point is at the image center. NVM files contain no information about the size of the images. Use the import dialog to adjust the "image path" to automatically read the image size from disc or set the default "width" and "height" values.

#### OpenMVG JSON
The OpenMVG JSON files contain no color information. The addon uses the input images (if provided) to compute the color of the triangulated 3D points - this computation requires the optional Pillow dependency.

#### Meshroom
The native file format Alembic (*.abc) of Meshroom is currently not supported, since parsing *.abc files requires building additional dependencies, e.g. ![this](https://github.com/alembic/alembic) library. In order to write the reconstruction result to *.SfM / *.json files, one can can add a ConvertSfMFormat node in Meshroom (see image below). 
![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/meshroom_export_json.jpg)


### Limitations
Blender supports only global render settings (which define the ratio of all cameras). If the reconstruction file contains cameras with different aspect ratios, it is not possible to visualize the camera cones correctly. Furthermore, radial distortions of the camera model used to compute the reconstruction will result in small misalignment of the cameras and the particle system in Blender.

### Visualization
Sometimes Blender draws boundaries around the particles of the point cloud. In oder to improve the visualization of the point cloud one can disable "Extras" under "Overlays" in the "3D view". The following image shows the corresponding options. 
![Disable Object Overlays](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/disable_object_extras_overlay_annotation.jpg)

### Export
In Blender use File/Export/VSFM NVM Export (.nvm) to export the NVM file. 
Select all cameras and objects you want to export. For each selected mesh the vertices are stored as points in the NVM file.
