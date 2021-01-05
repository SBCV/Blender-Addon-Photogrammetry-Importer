:: Go to the directory where the script is located
cd /D "%~dp0"
:: Use the HEAD of the current branch to create an archive of the subfolder photogrammetry_importer
git archive --format=zip -o photogrammetry_importer.zip HEAD photogrammetry_importer