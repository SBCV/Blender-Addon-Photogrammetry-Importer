#!/bin/bash
# Go to the directory where the script is located
cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd
# Use the HEAD of the current branch to create an archive of the subfolder photogrammetry_importer 
git archive --format=zip -o photogrammetry_importer.zip HEAD photogrammetry_importer