# Blender-Import-NVM-Addon
Blender addon to import and export VisualSFM's NVM files.
Tested for Blender 2.78 and 2.79 as well as Ubuntu 14.04 and Windows 10.

Import
=====
In Blender use File/Import/VSFM NVM Import (.nvm) to import the NVM file. 
There are several import options. You can add the image plane for each camera defined in the NVM file. The corresponding image files must be located in the same folder as the NVM file. 
There is an option to represent each vertex position with an object using a particle system. This allows you to render the point cloud. A single texture is used to store the color of all particles. The color of the points are shown, if the 3D view is set to "Material".

Export
=====
In Blender use File/Export/VSFM NVM Export (.nvm) to export the NVM file. 
Select all cameras and objects you want to export. For each selected mesh the vertices are stored as points in the NVM file.

Example
=====
This repository contains an example NVM file. The imported result looks as follows.
![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/import_result.jpg)

Installation
============
Clone the addon:
```
git clone https://github.com/SBCV/Blender-Import-NVM-Addon.git
```
Compress the folder "nvm_import" in "Blender-Import-NVM-Addon" to a zip archive. 
The final structure must look as follows:
- nvm_import_export.zip/  
	- nvm_import_export/  
		- nvm_file_handler.py  
		- __init__.py  
		- import_nvm_op.py  
		- ...  


Dependencies
============
This addon uses Pillow (https://python-pillow.org/) to import the SfM input images. 

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

License
=====
Blender NVM Import Export Addon
Copyright (C) 2018  Sebastian Bullinger

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
