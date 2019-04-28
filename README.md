# Blender-Import-NVM-Addon
Blender addon to import and export Structure-from-Motion (SfM) results using VisualSFM's ([http://ccwu.me/vsfm/](http://ccwu.me/vsfm/)) NVM file format. Also other SfM software tools like Colmap ([https://github.com/colmap/colmap](https://github.com/colmap/colmap)) or OpenMVG ([https://github.com/openMVG/openMVG](https://github.com/openMVG/openMVG)) support this data format.

Tested for Blender 2.80 beta. If you want to run the addon in Blender 2.79 use the [2.79 branch](https://github.com/SBCV/Blender-Import-NVM-Addon/tree/blender279).

## Example
This repository contains an example NVM file. The imported result looks as follows.
![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/import_result.jpg)
The input images of the NVM file are located here: [https://github.com/openMVG/ImageDataset_SceauxCastle](https://github.com/openMVG/ImageDataset_SceauxCastle).

## Usage

**Errors, help and logging information during import / export is shown in the "Info" area. Check this output, if nothing is imported. Probably the default width and height values are not set (see below).**

### Import
In Blender use File/Import/VSFM NVM Import (.nvm) to import the NVM file. 

**For correct camera visualization the size of the images is required. Use the import dialog to adjust the "image path" to automatically read the image size or set the default "width" and "height" values. Pillow is required to read the image size from disc.** By default the addon searches for the images in the in the folder where the NVM file is located. 

The addon automatically looks for the fixed calibration line in the NVM file (i.e. "NVM_V3 FixedK fx cx fy cy r"  (first line)).
Without the fixed calibration line the addon assumes that the principal point is at the image center. 

One can add the image plane for each camera defined in the NVM file. **This addon uses the node system of Cycles to visualize the image planes. Thus, the addon switches automatically to Cycles, if image planes are added.** 

There is an option to represent each vertex position with an object using a particle system. This allows you to render the point cloud. A single texture is used to store the color of all particles. **The color of the points / textures of the images are visible, if 'Cycles Render' is selected and the 3D view is set to "Material".**

Note: Blender supports only global render settings (which define the ratio of all cameras). If the nvm file contains cameras with different aspect ratios, it is not possible to visualize the camera cones correctly. 

### Export
In Blender use File/Export/VSFM NVM Export (.nvm) to export the NVM file. 
Select all cameras and objects you want to export. For each selected mesh the vertices are stored as points in the NVM file.

### Adjust Scale of Points (after importing)
For each imported point cloud two objects are created. The first object represents the structure of the point cloud and the second object defines the shape of the points in the point cloud. Rescaling of the second object will also update the size of the points in the point cloud.

### Adjust Scale of Cameras (after importing) 
Select the cameras, click in the *3D View* on *Pivot Point* and then on *Individual Origins*. Subsequent scaling operations with *Individual Origins* will only change the camera appearances but not the positions.
![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/scale_cameras.jpg)

## Installation
Clone the addon for Blender 2.80 beta:
```
git clone https://github.com/SBCV/Blender-Import-NVM-Addon.git
```
or for Blender 2.79
```
git clone -b blender279 https://github.com/SBCV/Blender-Import-NVM-Addon.git
```
Compress the folder "nvm_import" in "Blender-Import-NVM-Addon" to a zip archive. 
The final structure must look as follows:
- nvm_import_export.zip/  
	- nvm_import_export/  
		- nvm_file_handler.py  
		- __init__.py  
		- import_nvm_op.py  
		- ...  


## Dependencies (optional)
This addon uses Pillow (https://python-pillow.org/) to read the image sizes from disc. 

If you haven't installed pip for blender already, download https://bootstrap.pypa.io/get-pip.py and copy the file to 
```
<Blender_Root>/<Version>/python/bin
```

Run
```
<Blender_Root>/<Version>/python/bin/python get-pip.py 
```
or 
```
<Blender_Root>/<Version>/python/bin/python.exe get-pip.py 
```
depending on your operating system.

Finally, install Pillow with
```
<Blender_Root>/<Version>/python/scripts/pip install pillow
```
or 
```
<Blender_Root>/<Version>/python/scripts/pip.exe install pillow
```
respectively.

IMPORTANT: The full path to the pip executable must be provided (./pip install pillow will not work).


