# Blender-Addon-Photogrammetry-Importer
This repository contains a Blender addon to import and export Structure-from-Motion (SfM) reconstruction results.

This addon supports currently the following data formats: 
- [x] PLY ([http://paulbourke.net/dataformats/ply/](http://paulbourke.net/dataformats/ply/))
- [x] NVM ([http://ccwu.me/vsfm/](http://ccwu.me/vsfm/))
- [x] Colmap Model Folders ([https://github.com/colmap/colmap](https://github.com/colmap/colmap))
- [x] OpenMVG JSON files ([https://github.com/openMVG/openMVG](https://github.com/openMVG/openMVG))
- [ ] Meshroom Graphs ([https://alicevision.github.io/](https://alicevision.github.io/))

Thus, it is possible to import reconstruction results of the following libraries:
- [x] VisualSFM's ([http://ccwu.me/vsfm/](http://ccwu.me/vsfm/))
	* using NVM
- [x] Colmap ([https://github.com/colmap/colmap](https://github.com/colmap/colmap)) 
	* using Colmap model folders (binary and txt format), NVM, PLY 
- [x] OpenMVG ([https://github.com/openMVG/openMVG](https://github.com/openMVG/openMVG))
	* using OpenMVG JSON files, NVM, PLY
- [ ] Meshroom ([https://alicevision.github.io/](https://alicevision.github.io/))

Tested for Blender 2.80. If you want to run the addon in Blender 2.79 use the [2.79 branch](https://github.com/SBCV/Blender-Import-NVM-Addon/tree/blender279).

## Getting Started
- [Installation Instructions](doc/markdown/installation.md)
- [Usage (Import/Export)](doc/markdown/usage.md)
- [Adjust Results (Scale cameras and points)](doc/markdown/adjustment.md)

## Example
This repository contains an example NVM file. The imported result looks as follows.
![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/images/import_result.jpg)
The input images of the NVM file are located here: [https://github.com/openMVG/ImageDataset_SceauxCastle](https://github.com/openMVG/ImageDataset_SceauxCastle).

There is an import option that interpolates the reconstructed camera poses to compute a camera animation.
![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/images/camera_animation.gif)



