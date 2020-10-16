.. Blender-Addon-Photgrammetry-Importer documentation master file, created by
   sphinx-quickstart on Sat Jun 20 18:28:02 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

####################################
Blender-Addon-Photgrammetry-Importer 
####################################

..  https://documentation-style-guide-sphinx.readthedocs.io/en/latest/style-guide.html
		Heading Levels (recommended order)
			# with overline
			* with overline
			=
			-
			^
			"
	There should be only one H1 in a document.

This documentation describes an `addon for Blender <https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer>`_ that allows to import different reconstruction results of several :code:`Structure from Motion` and :code:`Multi-View Stereo` libraries.

Supported libraries (data formats):

.. hlist::
   :columns: 1

   - `Colmap <https://github.com/colmap/colmap>`_ (Model folders (BIN and TXT), workspaces, NVM, PLY) 
   - `Meshroom <https://alicevision.github.io/>`_ (MG, JSON, SfM, PLY)
   - `MVE <https://github.com/simonfuhrmann/mve>`_ (MVE workspaces) :sup:`1`
   - `Open3D <http://www.open3d.org/>`_ (JSON, LOG, PLY) :sup:`1`
   - `OpenSfM <https://github.com/mapillary/OpenSfM>`_ (JSON)
   - `OpenMVG <https://github.com/openMVG/openMVG>`_ (JSON, NVM, PLY) :sup:`2`
   - `Regard3D <https://www.regard3d.org/>`_ (OpenMVG JSON)
   - `VisualSFM <http://ccwu.me/vsfm/>`_ (NVM) :sup:`1`

In addition, the addon supports some common point cloud data formats:

.. hlist::
   :columns: 1

   - `Polygon files <http://paulbourke.net/dataformats/ply/>`_ (PLY) :sup:`3`
   - `Point Cloud Library files <https://github.com/PointCloudLibrary/pcl>`_ (PCD) :sup:`3`
   - `LASer files <https://www.asprs.org/divisions-committees/lidar-division/laser-las-file-format-exchange-activities>`_ (LAS) :sup:`3, 4`
   - `LASzip files <https://laszip.org/>`_ (LAZ) :sup:`3, 4, 5`
   - `Simple ASCII point files <https://www.cloudcompare.org/doc/wiki/index.php?title=FILE_I/O>`_ (ASC, PTS, CSV) :sup:`3`

| :sup:`1` Requires :code:`pillow` to read image sizes from disk. :sup:`2` Requires :code:`pillow` for point color computation.
| :sup:`3` Requires :code:`pyntcloud` for parsing. :sup:`4` Requires :code:`pylas` for parsing. :sup:`5` Requires :code:`lazrs` for parsing.

Compatible with Blender 2.8.0 onwards. There is an older version of the addon available for Blender 2.79 that allows to import NVM files - see the `2.79 branch <https://github.com/SBCV/Blender-Import-NVM-Addon/tree/blender279>`_.

Getting Started
===============

.. https://www.sphinx-doc.org/en/1.5/markup/toctree.html
.. toctree::
   :maxdepth: 1

   self
   installation
   troubleshooting
   customize
   examples
   import
   export
   adjustment
   alignment
   point_cloud
   python
   contribution
   changelog

There is a short `tutorial video <https://www.youtube.com/watch?v=BwwaT2scoP0>`_ that shows how to

- install the addon
- compute a reconstruction with Meshroom
- import the results into Blender


Example Results (Shipped with Addon)
====================================
This repository contains an example NVM file. The imported result looks as follows.

.. image:: ../../images/import_result.jpg
   :scale: 32 %
   :align: center

The input images of the NVM file are located here: https://github.com/openMVG/ImageDataset_SceauxCastle.

There is an import option that interpolates the reconstructed camera poses to compute a camera animation.

.. image:: ../../images/camera_animation.gif
   :scale: 22 %
   :align: center

You can also overlay the (sparse) point cloud with the corresponding mesh - see :doc:`Import Data <./import>`. 

.. image:: ../../images/point_cloud_mesh_overlay.jpg
   :scale: 32 %
   :align: center

The addon offers an option to draw big point clouds with OpenGL to reduce computational requirements. The addon provides a panel to export these OpenGL point clouds renderings - see :doc:`Point Cloud Visualization and Rendering <./point_cloud>`. 

.. image:: ../../images/import_result_opengl.jpg
   :scale: 40 %
   :align: center


..
	Indices and tables
	==================

	* :ref:`genindex`
	* :ref:`search`
