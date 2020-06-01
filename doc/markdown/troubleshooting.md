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

#### Linux
Under Linux delete:\
`~/.config/blender/<Version>/scripts/addons/photogrammetry_importer`\
In the case of Blender 2.82:\
`~/.config/blender/2.82/scripts/addons/photogrammetry_importer`

### Blender Crashes while Importing Reconstructions

This is probably not an issue of the addon or Blender, but caused by outdated graphic drivers. 
If the problem persists (after restarting Blender / the operating system), one can find more information in the [Blender manual](https://docs.blender.org/manual/en/dev/troubleshooting/gpu/index.html).
As workaround one may import the point cloud as Blender object or as a particle system (additional import options) instead of drawing the point cloud with OpenGL (default import option).
