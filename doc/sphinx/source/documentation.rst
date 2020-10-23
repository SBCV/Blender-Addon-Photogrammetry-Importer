*************
Documentation
*************

The addon uses `Sphinx <https://www.sphinx-doc.org>`_, `sphinx_rtd_theme <https://github.com/readthedocs/sphinx_rtd_theme>`_, `sphinx-autoapi <https://github.com/readthedocs/sphinx-autoapi>`_ to generate the documentation.

These tools can be installed with

.. hlist::
   :columns: 1

   - :code:`pip install -U sphinx`
   - :code:`pip install sphinx-rtd-theme`
   - :code:`pip install sphinx-autoapi`

In order to build the documentation locally

.. hlist::
   :columns: 1
   
   - download the `project <https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer>`_
   - navigate to the :code:`sphinx` folder (i.e. :code:`cd Blender-Addon-Photogrammetry-Importer/doc/sphinx`)
   - run :code:`make html` / :code:`make latex` (using Linux) or :code:`make.bat html` / :code:`make.bat latex` (using Windows)
