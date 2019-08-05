import os
from photogrammetry_importer.ext.read_model import read_model

class ColmapFileHandler(object):

    @staticmethod
    def parse_colmap_model_folder(model_ifp):

        ifp_s = os.listdir(model_ifp)

        if all(x in ['cameras.bin', 'images.bin', 'points3D.bin'] for x in ifp_s):
            ext = '.bin'
        elif all(x in ['cameras.txt', 'images.txt', 'points3D.txt'] for x in ifp_s):
            ext = '.txt'
        else:
            assert False

        cameras, images, points3D = read_model(model_ifp, ext=ext)