#!/bin/bash
# Go to the directory where the script is located
cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd
black --line-length 79 --exclude photogrammetry_importer/ext photogrammetry_importer
black --line-length 79 doc/sphinx/source/conf.py