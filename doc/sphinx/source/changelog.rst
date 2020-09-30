***************************
Recent Features / Changelog
***************************

Changelog with most relevant features. Recently added features are listed at the top of this page.

2020
====

* Fixed a bug in the texture coordinate computation of the particle system
* Added a workaround to circumvent a bug in Blender, which appears only for large point clouds 
* Added GUI elements to install/uninstall the dependencies (Pillow, Pyntcloud)
* Addon uses now the Pyntcloud library to import PLY, PCD, LAS, ASC, PTS and CSV files
* Added an option to import depth maps of MVE workspaces
* Added an option to import depth maps of Colmap as point clouds
* Added support for MVE workspaces
* Added addon preferences to configure the import/export default settings
* Added addon preferences to enable/disable importers and exporters
* Added an OpenSfM importer
* OpenGL data is now persistent (stored in blend file) and is available after reopening
* Added a panel with options to export renderings of the point cloud using OpenGL
* Added support for Colmap dense workspaces
* Added support for Meshroom projects (.mg files)
* Fixed occlusion of point clouds drawn with OpenGL
* Added a Colmap exporter
* Added an Open3D importer
* Added an option to render point clouds with OpenGL
* Added support for absolute and relative paths in reconstruction results
* Added a preset possiblity for each importer to customize default import options

2019
====

* Added support to import undistorted images of Colmap/Meshroom
* Fixed a bug leading to incorrect principal points
* Added option to remove discontinuities in animations
* Added an option to show source images as Blender background images
* Added particle emission to improve visibility
* Added importers for Colmap, OpenMVG and Meshroom 
* Compatibility fix for Blender 2.8

2018
====

* Added an option to add camera animation
* Added an option to import images as image planes
* Added an exporter for cameras and mesh vertex positions as NVM
* Added an option to represent point clouds with particle systems 

2017
====

* Added a NVM importer
* Initial Commit 

