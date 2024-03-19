#!/bin/bash
# Go to the directory where the script is located
cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd
REQUIRED_VERSION="24.3.0"
black --required-version ${REQUIRED_VERSION} --line-length 79 --exclude photogrammetry_importer/ext photogrammetry_importer
black --required-version ${REQUIRED_VERSION} --line-length 79 example_view_synthesis_scripts
black --required-version ${REQUIRED_VERSION} --line-length 79 doc/sphinx/source/conf.py
