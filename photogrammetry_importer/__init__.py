'''
Copyright (C) 2018 Sebastian Bullinger


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
    "name": "VSFM NVM Import Export Addon",
    "description": "Allows to import and export VisualSFM's .nvm file format (cameras and points).",
    "author": "Sebastian Bullinger",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
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
# therefore we need the "photogrammetry_importer" specifier for this addon  
from photogrammetry_importer.photogrammetry_import_op import ImportNVM
from photogrammetry_importer.photogrammetry_import_op import ImportPLY
from photogrammetry_importer.photogrammetry_export_op import ExportNVM

# register
##################################

def menu_func_import(self, context):
    self.layout.operator(ImportNVM.bl_idname, text="VSFM NVM Import (.nvm)")
    self.layout.operator(ImportPLY.bl_idname, text="Point Cloud PLY Import (.ply)")
    
def menu_func_export(self, context):
    self.layout.operator(ExportNVM.bl_idname, text="VSFM NVM Export (.nvm)")

def register():
    bpy.utils.register_class(ImportNVM)
    bpy.utils.register_class(ImportPLY)
    bpy.utils.register_class(ExportNVM)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    print("Registered {} with {} modules".format(bl_info["name"], len(modules)))
    

def unregister():
    bpy.utils.unregister_class(ImportNVM)
    bpy.utils.unregister_class(ImportPLY)
    bpy.utils.unregister_class(ExportNVM)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    print("Unregistered {}".format(bl_info["name"]))

if __name__ == '__main__':
    print('main called')
    
