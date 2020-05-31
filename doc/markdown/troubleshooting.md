## Troubleshooting 

### Problems to Activate the Addon

If you experience problems while installing and activating a newer version of the addon 
(i.e. an older version of the addon was previously installed), delete Blender's user folder of the  addon.
[This page](https://docs.blender.org/manual/en/latest/advanced/blender_directory_layout.html) of the Blender manual
provides information about the location of the corresponding folder. Make sure that you close Blender before deleting the folder.

#### Windows
Under Windows delete the following folder:\
`%USERPROFILE%\AppData\Roaming\Blender Foundation\Blender\<Version>\scripts\addons\photogrammetry_importer`\
In the case of Blender 2.82:\
`%USERPROFILE%\AppData\Roaming\Blender Foundation\Blender\2.82\scripts\addons\photogrammetry_importer`
