# Blender-Addon-Photogrammetry-Importer
This repository contains a Blender addon to import reconstruction results of several libraries.

Supported libraries (data formats):

- [x] [Colmap](https://github.com/colmap/colmap) (Model folders (BIN and TXT), dense workspaces, NVM, PLY)  
- [x] [Meshroom](https://alicevision.github.io/) (MG, JSON, SfM, PLY)
- [x] [MVE](https://github.com/simonfuhrmann/mve) (Workspaces) <sup>1</sup>
- [x] [Open3D](http://www.open3d.org/) (JSON, LOG, PLY) <sup>1</sup>
- [x] [OpenSfM](https://github.com/mapillary/OpenSfM) (JSON)
- [x] [OpenMVG](https://github.com/openMVG/openMVG) (JSON, NVM, PLY) <sup>2</sup>
- [x] [Regard3D](https://www.regard3d.org/) (OpenMVG JSON)
- [x] [VisualSFM](http://ccwu.me/vsfm/) (NVM) <sup>1</sup>

In addition, the addon supports some common point cloud data formats:

- [x] [Polygon files](http://paulbourke.net/dataformats/ply/) (PLY) <sup>3</sup>
- [x] [Point Cloud Library files](https://github.com/PointCloudLibrary/pcl) (PCD) <sup>3</sup>
- [x] [LASer files](https://www.asprs.org/divisions-committees/lidar-division/laser-las-file-format-exchange-activities) (LAS) <sup>3,4</sup>
- [x] [LASzip files](https://laszip.org/) (LAZ) <sup>3,4,5</sup>
- [x] [Simple ASCII point files](https://www.cloudcompare.org/doc/wiki/index.php?title=FILE_I/O) (ASC, PTS, CSV) <sup>3</sup>

<sup>1</sup> Requires [Pillow](https://pypi.org/project/Pillow/) to read image sizes from disk.
<sup>2</sup> Requires Pillow for point color computation.\
<sup>3</sup> Requires [Pyntcloud](https://pypi.org/project/pyntcloud/) for parsing.
<sup>4</sup> Requires [Pylas](https://pypi.org/project/pylas/) for parsing.
<sup>5</sup> Requires [Lazrs](https://pypi.org/project/lazrs/) for parsing.

Compatible with Blender 2.80 onwards. There is an older version of the addon available for Blender 2.79 that allows to import NVM files - see the [2.79 branch](https://github.com/SBCV/Blender-Import-NVM-Addon/tree/blender279).

## Getting Started
- [Documentation](https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest) 
- [Tutorial Video](https://www.youtube.com/watch?v=BwwaT2scoP0) 
- [Installation Instructions](https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest/installation.html)
- [Troubleshooting](https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest/troubleshooting.html)
- [Customize Import/Export Options](https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest/customize.html)
- [Examples](https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest/examples.html)
- [Import Data](https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest/import.html)
- [Export Data](https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest/export.html)
- [Adjust Results (Scale Cameras and Points)](https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest/adjustment.html)
- [Ensure Camera and Point Alignment](https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest/alignment.html)
- [Point Cloud Visualization and Rendering](https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest/point_cloud.html)
- [Addon Usage with Python](https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest/python.html)
- [Contribution](https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest/contribution.html)
- [Recent features / Changelog](https://blender-addon-photogrammetry-importer.readthedocs.io/en/latest/changelog.html)

## Example
This repository contains an example NVM file. The imported result looks as follows.
![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/import_result.jpg)
The input images of the NVM file are located here: [https://github.com/openMVG/ImageDataset_SceauxCastle](https://github.com/openMVG/ImageDataset_SceauxCastle).

There is an import option that interpolates the reconstructed camera poses to compute a camera animation.
![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/camera_animation.gif)

You can also overlay the (sparse) point cloud with the corresponding mesh - see [Import Data](doc/markdown/import.md). 
![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/point_cloud_mesh_overlay.jpg)

In addition, the addon allows to visualize depth maps (reconstructed with Colmap or MVE) as point clouds.
<p float="left" align="middle">
  <img src="https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/depth_map_3d_view.jpg" width="400" />
  <img src="https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/depth_map_from_camera.jpg" width="400" /> 
</p>


The addon offers an option to draw big point clouds with OpenGL to reduce computational requirements. The addon provides a panel to export these OpenGL point clouds renderings - see [Point Cloud Visualization and Rendering](doc/markdown/point_cloud.md). 
![alt text](https://github.com/SBCV/Blender-Import-NVM-Addon/blob/master/doc/images/import_result_opengl.jpg)
