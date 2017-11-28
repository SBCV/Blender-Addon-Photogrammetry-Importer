# Blender-Import-NVM-Addon
Addon to import VisualSFM's NVM files into Blender 2.78.

Installation
============
Clone the addon:
```
git clone https://github.com/SBCV/Blender-Import-NVM-Addon.git
```
Compress the folder "nvm_import" in "Blender-Import-NVM-Addon" to a zip archive. 
The final structure looks as follows:
	nvm_import.zip/
		nvm_import/
			nvm_file_handler.py
			__init__.py 
			import_nvm_op.py
			...


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

Usage
=====
In Blender use (as usual) File/Import/VSFM NVM Import (.nvm) to import the NVM file. The corresponding image files must be located in the same folder as the NVM file. 
