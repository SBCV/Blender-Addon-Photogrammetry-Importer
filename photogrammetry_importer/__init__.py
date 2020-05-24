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
    "name": "Photogrammetry Import Export Addon",
    "description": "Allows to import and export photogrammetry results (cameras and points).",
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
from .utils import developer_utils
importlib.reload(developer_utils)
modules = developer_utils.setup_addon_modules(__path__, __name__, "bpy" in locals())

# The root dir is blenders addon folder, 
# therefore we need the "photogrammetry_importer" specifier for this addon
from photogrammetry_importer.photogrammetry_import_op import ImportMeshroom
from photogrammetry_importer.photogrammetry_import_op import ImportOpenMVG
from photogrammetry_importer.photogrammetry_import_op import ImportColmap
from photogrammetry_importer.photogrammetry_import_op import ImportNVM
from photogrammetry_importer.photogrammetry_import_op import ImportOpen3D
from photogrammetry_importer.photogrammetry_import_op import ImportPLY

from photogrammetry_importer.photogrammetry_export_op import ExportNVM
from photogrammetry_importer.photogrammetry_export_op import ExportColmap

from photogrammetry_importer.panel.opengl_panel import OpenGLPanel
from photogrammetry_importer.opengl.visualization_utils import redraw_points
bpy.app.handlers.load_post.append(redraw_points)

# register
##################################

def menu_func_import(self, context):
    self.layout.operator(ImportMeshroom.bl_idname, text="Meshroom Import (.sfm/.json/.mg)")
    self.layout.operator(ImportOpenMVG.bl_idname, text="OpenMVG / Regard3D Import (.json)")
    self.layout.operator(ImportColmap.bl_idname, text="Colmap Import (model/workspace)")
    self.layout.operator(ImportNVM.bl_idname, text="VSFM NVM Import (.nvm)")
    self.layout.operator(ImportOpen3D.bl_idname, text="Open3D Import (.log/.json)")
    self.layout.operator(ImportPLY.bl_idname, text="Point Cloud PLY Import (.ply)")
    
def menu_func_export(self, context):
    self.layout.operator(ExportNVM.bl_idname, text="VSFM NVM Export (.nvm)")
    self.layout.operator(ExportColmap.bl_idname, text="Colmap Export (folder)")

# =========================================================================
# === Uncomment for fast debugging ===
# from bpy.app.handlers import persistent
# @persistent
# def load_handler(dummy):
#     from photogrammetry_importer.file_handler.ply_file_handler import PLYFileHandler
#     from photogrammetry_importer.utils.visualization_utils import draw_points
#     points = PLYFileHandler.parse_ply_file('path/to/file.ply')

#     class LogOp():
#         def report(sef, arg1, arg2):
#             print(arg1, arg2)

#     log_op = LogOp()
#     draw_points(log_op, points)
# =========================================================================

def register():
    bpy.utils.register_class(ImportMeshroom)
    bpy.utils.register_class(ImportOpenMVG)
    bpy.utils.register_class(ImportColmap)
    bpy.utils.register_class(ImportNVM)
    bpy.utils.register_class(ImportOpen3D)
    bpy.utils.register_class(ImportPLY)

    bpy.utils.register_class(ExportNVM)
    bpy.utils.register_class(ExportColmap)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    bpy.utils.register_class(OpenGLPanel)

    # === Uncomment for fast debugging ===
    # bpy.app.handlers.load_post.append(load_handler)

    print("Registered {} with {} modules".format(bl_info["name"], len(modules)))
    

def unregister():
    bpy.utils.unregister_class(ImportMeshroom)
    bpy.utils.unregister_class(ImportOpenMVG)
    bpy.utils.unregister_class(ImportColmap)
    bpy.utils.unregister_class(ImportNVM)
    bpy.utils.unregister_class(ImportOpen3D)
    bpy.utils.unregister_class(ImportPLY)

    bpy.utils.unregister_class(ExportNVM)
    bpy.utils.unregister_class(ExportColmap)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    bpy.utils.unregister_class(OpenGLPanel)

    print("Unregistered {}".format(bl_info["name"]))


if __name__ == '__main__':
    print('main called')
    
