*************************
Installation Instructions
*************************

Delete any Previous Version of the Addon
========================================

- Remove any previous version of the addon from Blender.
    * Inside Blender go to :code:`Edit/Preferences/Add-ons`, search for :code:`Import-Export: Photogrammetry Import Export Addon` and click on :code:`Remove`
    * See the :doc:`troubleshooting page <./troubleshooting>` for more information.
- **THEN, CLOSE BLENDER**
- Reopen Blender and follow the installation instructions below

Without removal of previos versions errors may appear during activation or Blender may not reflect the latest changes of the addon. 


Download the Addon for Blender 2.80 (or newer)
==============================================

Option 1: Download a Release Version of the Addon
-------------------------------------------------
Download the corresponding :code:`photogrammetry_importer.zip` from the `release page <https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer/releases>`_.

Option 2: Download the Latest Version of the Addon
--------------------------------------------------

For example, clone the addon with ::

	git clone https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer.git

(Alternatively, go to :code:`https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer`, click on :code:`clone or download`, and download the archive by clicking on :code:`Download Zip`. Extract the :code:`Blender-Addon-Photogrammetry-Importer-master.zip` file, which creates a folder :code:`Blender-Addon-Photogrammetry-Importer`.) 

Finally, compress the folder :code:`photogrammetry_importer` in :code:`Blender-Addon-Photogrammetry-Importer` to a zip archive :code:`photogrammetry_importer.zip`. 
The final structure must look as follows:

::

	photogrammetry_importer.zip /
	    photogrammetry_importer /
	        ext
	        file_handler
	        blender_utils.py
	        ...

Install the Addon
=================

Install the addon by 
	- Opening the preferences of Blender (:code:`Edit / Preferences ...`)  
	- Select :code:`Add-ons` in the left toolbar
	- Click on :code:`Install...` in the top toolbar
	- Navigate to the :code:`photogrammetry_importer.zip` file, select it and click on :code:`Install Add-on` 
	- Scroll down to **ACTIVATE the addon**, i.e. check the bounding box left of :code:`Import-Export: Photogrammetry Import Export Addon` (see image below)

.. image:: ../../images/activated.jpg
   :scale: 75 %
   :align: center

Follow the instructions on the :doc:`customize <./customize>` page, to adjust the default options of the addon. 

Optional Dependency for VisualSfM, Multi-View Environment and OpenMVG/Regard3D
==============================================================================
This addon uses `Pillow <https://pypi.org/project/Pillow/>`_ to compute missing information for VisualSFM NVM files, Multi-View Environment folders and OpenMVG JSON files.

- For VisualSFM (NVM files) and Multi-View Environment the addon uses pillow to read the (missing) image sizes from disc.
- For OpenMVG/Regard3D (JSON files) the addon uses pillow to compute the (missing) colors for the 3D points in the point cloud.

Using Pillow instead of Blender's image API significantly improves processing time. 

If you haven't installed `pip <https://pypi.org/project/pip/>`_ for Blender already, download https://bootstrap.pypa.io/get-pip.py and copy the file to ::

<Blender_Root>/<Version>/python/bin

For Linux run: ::

<Blender_Root>/<Version>/python/bin/python3.7m <Blender_Root>/<Version>/python/bin/get-pip.py
<Blender_Root>/<Version>/python/bin/pip install pillow

For Windows run: ::

<Blender_Root>/<Version>/python/bin/python.exe <Blender_Root>/<Version>/python/bin/get-pip.py
<Blender_Root>/<Version>/python/Scripts/pip.exe install pillow

IMPORTANT: Use the full path to the python and the pip executable. Otherwise the system python installation or the system pip executable may be used.
