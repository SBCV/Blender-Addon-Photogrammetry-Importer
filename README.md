# Blender-Addon-Photogrammetry-Importer
This repository contains a Blender addon to import and export Structure-from-Motion (SfM) reconstruction results.

This addon supports currently the following data formats: 
- [x] PLY ([http://paulbourke.net/dataformats/ply/](http://paulbourke.net/dataformats/ply/))
- [x] NVM ([http://ccwu.me/vsfm/](http://ccwu.me/vsfm/))
- [x] Colmap Model Folders ([https://github.com/colmap/colmap](https://github.com/colmap/colmap))
- [x] OpenMVG JSON files ([https://github.com/openMVG/openMVG](https://github.com/openMVG/openMVG))
- [x] Meshroom SfM/JSON files ([https://alicevision.github.io/](https://alicevision.github.io/))

Thus, it is possible to import reconstruction results of the following libraries:
- [x] VisualSFM's ([http://ccwu.me/vsfm/](http://ccwu.me/vsfm/))
	* using NVM
- [x] Colmap ([https://github.com/colmap/colmap](https://github.com/colmap/colmap)) 
	* using Colmap model folders (binary and txt format), NVM and PLY 
- [x] OpenMVG ([https://github.com/openMVG/openMVG](https://github.com/openMVG/openMVG))
	* using JSON (OpenMVG), NVM and PLY
- [x] Meshroom ([https://alicevision.github.io/](https://alicevision.github.io/))
	* using SfM, JSON (Meshroom) and PLY

Tested for Blender 2.81. There is an older version of the addon available for Blender 2.79 that allows to import NVM files - see the [2.79 branch](https://github.com/SBCV/Blender-Import-NVM-Addon/tree/blender279).

## Getting Started
- [Tutorial Video](https://www.youtube.com/watch?v=BwwaT2scoP0) 
- [Installation Instructions](doc/markdown/installation.md)
- [Examples](doc/markdown/example.md)
- [Usage (Import/Export)](doc/markdown/usage.md)
- [Adjust Results (Scale Cameras and Points)](doc/markdown/adjustment.md)
- [Reconstruction Representation with Blender Objects](doc/markdown/representation.md)
- [Contribution](doc/markdown/contribution.md)

## Example
This repository contains an example NVM file. The imported result looks as follows.
![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/import_result.jpg)
The input images of the NVM file are located here: [https://github.com/openMVG/ImageDataset_SceauxCastle](https://github.com/openMVG/ImageDataset_SceauxCastle).

There is an import option that interpolates the reconstructed camera poses to compute a camera animation.
![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/camera_animation.gif)

You can also overlay the (sparse) point cloud with the corresponding mesh - see [Usage (Import/Export)](doc/markdown/usage.md). 
![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/point_cloud_mesh_overlay.jpg)

