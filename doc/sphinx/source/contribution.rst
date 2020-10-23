************
Contribution
************

I am always happy to get advices as well as feature and pull requests. 
If you want to create a pull request, I recommend to use `VS Code <https://code.visualstudio.com>`_ with this `extension <https://marketplace.visualstudio.com/items?itemName=JacquesLucke.blender-development>`_. 
This allows to perform fast development and validation cycles with Blender scripts and addons. `Here <https://www.youtube.com/watch?v=q06-hER7Y1Q>`_ is an introduction / tutorial video.

This addon relies on `Black <https://github.com/psf/black>`_ for formatting. To ensure that your :code:`Pull Request` is correctly formatted perform the following steps:

.. hlist::
   :columns: 1

   - Install Black - checkout the `installation instructions <https://github.com/psf/black#installation-and-usage>`_
   - :code:`cd path/to/Blender-Addon-Photogrammetry-Importer`
   - :code:`black --line-length 79 --exclude photogrammetry_importer/ext photogrammetry_importer`
   - :code:`black --line-length 79 doc/sphinx/source/conf.py`

The addon uses Docstrings for documentation - see `PEP 257 <https://www.python.org/dev/peps/pep-0257/>`_ and `PEP 287 <https://www.python.org/dev/peps/pep-0287/>`_ .
