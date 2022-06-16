@echo off

:: #################################################################
:: Run this bat file (without parameters) to create a Blender add-on 
:: (photogrammetry_importer.zip), which can be installed in Blender.
:: #################################################################

:: Go to the directory where the script is located
:: cd /D "%~dp0"

where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo Found NO git executable, use tar to create photogrammetry_importer.zip.
  tar -caf photogrammetry_importer.zip photogrammetry_importer
  exit 0
) else (
  echo Found git executable.
)

git rev-parse --git-dir >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo Found NO valid git repository, use tar to create photogrammetry_importer.zip.
  tar -caf photogrammetry_importer.zip photogrammetry_importer
) else (
    echo Found valid git repository, use git-archive to create zip file.
    git archive --format=zip -o photogrammetry_importer.zip HEAD photogrammetry_importer
)
