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
