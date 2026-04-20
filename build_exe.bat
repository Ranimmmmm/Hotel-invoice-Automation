@echo off
REM Build script to create a standalone Windows executable
REM Run this batch file to build the .exe

echo Installing PyInstaller if needed...
pip install pyinstaller

echo.
echo Building executable...
python build_exe.py

echo.
echo Build complete! Check the 'dist' folder for the executable.
pause

