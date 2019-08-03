## Installation
Clone the addon for Blender 2.80:
```
git clone https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer.git
```
or for Blender 2.79:
```
git clone -b blender279 https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer.git
```
Compress the folder "photogrammetry_importer" in "Blender-Addon-Photogrammetry-Importer" to a zip archive. 
The final structure must look as follows:
- photogrammetry_importer.zip /  
	- photogrammetry_importer/
		- ext  
		- file_handler  
		- blender_utils.py
		- ...  


## Dependencies (optional)
This addon uses Pillow (https://python-pillow.org/) to read the image sizes from disc. 

If you haven't installed pip for blender already, download https://bootstrap.pypa.io/get-pip.py and copy the file to 
```
<Blender_Root>/<Version>/python/bin
```

For Linux run:
```
<Blender_Root>/<Version>/python/bin/python3.7m get-pip.py
<Blender_Root>/<Version>/python/bin/pip install pillow
```
For Windows run:
```
<Blender_Root>/<Version>/python/bin/python.exe get-pip.py
<Blender_Root>/<Version>/python/Scripts/pip.exe install pillow
```

IMPORTANT: Use the full path to the python and the pip executable. Otherwise the system python installation or the system pip executable may be used.

