#!/bin/bash
# Go to the directory where the script is located
cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd

if command -v git >/dev/null 2>&1; then
	echo "Found git executable."
else
	echo "Found NO git executable, use zip to create photogrammetry_importer.zip."
  	zip -r photogrammetry_importer.zip photogrammetry_importer
  	exit 0
fi

if git rev-parse --git-dir > /dev/null 2>&1; then
	echo "Found valid git repository, use git-archive to create zip file."
	# Use the HEAD of the current branch to create an archive of the subfolder photogrammetry_importer 
	git archive --format=zip -o photogrammetry_importer.zip HEAD photogrammetry_importer
else
  echo "Found NO valid git repository, use zip to create photogrammetry_importer.zip."
  zip -r photogrammetry_importer.zip photogrammetry_importer
fi
