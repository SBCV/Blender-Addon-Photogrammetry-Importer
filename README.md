# Blender-Import-NVM-Addon
Addon to import VisualSFM's NVM files into Blender 2.78.

Installation
============
In order to install the addon, download 
```
https://github.com/SBCV/Blender-Import-NVM-Addon/releases/download/v1.0/nvm_import.zip
```

This addon relies on Pillow (https://python-pillow.org/). 

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
