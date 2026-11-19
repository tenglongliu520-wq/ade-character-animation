@echo off
cd /d "%~dp0"
if exist "D:\AI\Ade-3D-Blender-20261119\.venv\Scripts\python.exe" (
  "D:\AI\Ade-3D-Blender-20261119\.venv\Scripts\python.exe" preview.py --port 4193
) else (
  py -3 preview.py --port 4193
)
pause
