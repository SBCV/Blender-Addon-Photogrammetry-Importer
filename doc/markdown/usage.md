## Usage

**Errors, help and logging information during import / export is shown in the "Info" area. Check this output, if nothing is imported. Probably the default width and height values are not set (see below).**

### Import

#### General

**For correct camera visualization the size of the images is required. If the size information is not present in the reconstruction result (e.g. NVM file) use the import dialog to adjust the "image path" to automatically read the image size or set the default "width" and "height" values. Pillow is required to read the image size from disc.** By default the addon searches for the images in the in the folder where the reconstruction file is located. 

There is an option to represent each vertex position with an object using a particle system. This allows you to render the point cloud. A single texture is used to store the color of all particles. **The color of the points / textures of the images are visible, if 'Cycles Render' is selected and the 3D view is set to "Material".**

One can add the image plane for each camera defined in the reconstruction file. **This addon uses the node system of Cycles to visualize the image planes. Thus, the addon switches automatically to Cycles, if image planes are added.** 

Blender supports only global render settings (which define the ratio of all cameras). If the reconstruction file contains cameras with different aspect ratios, it is not possible to visualize the camera cones correctly. 

#### NVM
In Blender use File/Import/VSFM NVM Import (.nvm) to import the NVM file. 

The addon automatically looks for the fixed calibration line in the NVM file (i.e. "NVM_V3 FixedK fx cx fy cy r"  (first line)).
Without the fixed calibration line the addon assumes that the principal point is at the image center. 


### Export
In Blender use File/Export/VSFM NVM Export (.nvm) to export the NVM file. 
Select all cameras and objects you want to export. For each selected mesh the vertices are stored as points in the NVM file.