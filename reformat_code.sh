#!/bin/bash
black --line-length 79 --exclude photogrammetry_importer/ext photogrammetry_importer
black --line-length 79 doc/sphinx/source/conf.py