'''
Copyright (C) 2017 YOUR NAME
YOUR@MAIL.com

Created by Sebastian Bullinger

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    "name": "VSFM NVM Import Addon",
    "description": "Allows to import VisualSFM's .nvm file format (cameras and points) into Blender.",
    "author": "Sebastian Bullinger",
    "version": (1, 0, 0),
    "blender": (2, 79, 0),
    "location": "View3D",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export" }


import bpy


# load and reload submodules
##################################

import importlib
from . import developer_utils
importlib.reload(developer_utils)
modules = developer_utils.setup_addon_modules(__path__, __name__, "bpy" in locals())

# The root dir is blenders addon folder, 
# therefore we need the "nvm_import" specifier for this addon  
from nvm_import.import_nvm_op import ImportNVM


# register
##################################

import traceback

def menu_func_import(self, context):
    self.layout.operator(ImportNVM.bl_idname, text="VSFM NVM Import (.nvm)")

def register():
    try: bpy.utils.register_module(__name__)
    except: traceback.print_exc()

    bpy.types.INFO_MT_file_import.append(menu_func_import)

    print("Registered {} with {} modules".format(bl_info["name"], len(modules)))
    

def unregister():
    try: bpy.utils.unregister_module(__name__)
    except: traceback.print_exc()

    bpy.types.INFO_MT_file_import.remove(menu_func_import)

    print("Unregistered {}".format(bl_info["name"]))

if __name__ == '__main__':
    print('main called')
    
