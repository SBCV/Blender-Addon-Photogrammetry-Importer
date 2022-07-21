***************************
Recent Features / Changelog
***************************

Changelog with most relevant features. Recently added features are listed at the top of this page.

2022
====
* Fix geometry node creation for Blender 3.2.1
* Add support for installation and removal of individual dependencies
* Fix the point exporter for OpenGL point clouds
* Remove the particle system based point cloud representation method (because of the new point clound representation option based on geometry nodes)
* Add particle colors to geometry nodes (Thanks to @Linusnie)
* Add a new point cloud representation method based on geometry nodes. Allows to render the point coud with Eevee and Cycles
* Replace pylas with laspy (>= 2.0)
* Add an option to center points around the origin (useful for laz/las files)
* Remove the point color computation for OpenMVG json files, due to a bug in pillow caused by the blender python environment
* Adjust the screenshot rendering functionality according to api changes of Blender 3.0
* Replacing the bgl module with the gpu module to fix the offscreen rendering of point clouds under windows
* Fix the dependency installation for Blender 2.8 - 2.91 of the newly introduced dependency manager

2021
====
* Improve management of dependency installation and corresponding GUI options
* Made point sizes of point clouds and depth maps (drawn with OpenGL) persistent
* Changed the usage of draw handlers to avoid potential crashes when deleting the point cloud anchor objects
* Made depth maps persistent (i.e. the corresponding information is stored in the blend file)
* Added features to export images of the imported reconstructions including cameras, background images, image planes, point clouds and meshes

2020
====

* Reorganized (persistent) addon preferences
* Added an option to use the undistorted images contained in the workspaces of the Colmap, Meshroom and MVE  
* Added several python examples that demonstrate the API usage
* Added vertex colors to the mesh shader nodes to improve the visibility of the corresponding mesh
* Added background images for the animated camera
* Added code to automatically generate the API Documentation with autoapi
* Fixed an incorrect offset in the texture coordinate computation of the particle system
* Added a workaround to circumvent a bug in Blender, which appears only for large particle systems (T81103)
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

