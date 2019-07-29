## Installation
Clone the addon for Blender 2.80 Release Candidate 3:
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

Depending on your operating system, run
```
<Blender_Root>/<Version>/python/bin/python get-pip.py 
```
or 
```
<Blender_Root>/<Version>/python/bin/python.exe get-pip.py 
```


IMPORTANT: Use the full path to the python executable (otherwise the system python installation may be used).

Depending on your operating system, install Pillow with
```
<Blender_Root>/<Version>/python/bin/pip install pillow
```
or 
```
<Blender_Root>/<Version>/python/bin/pip.exe install pillow
```


IMPORTANT: Use the full path to the pip executable (./pip install pillow may not work).
