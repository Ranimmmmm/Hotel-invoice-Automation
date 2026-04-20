#!/usr/bin/env python3
"""
Build script to create a standalone Windows executable.
Run: python build_exe.py
"""
import PyInstaller.__main__
import os
import sys

# PyInstaller configuration
app_name = "hotel_invoice_tool"
main_script = "main.py"

# Build the executable
PyInstaller.__main__.run([
    main_script,
    '--name=%s' % app_name,
    '--onefile',  # Create a single executable file
    '--console',  # Show console window (needed for CLI output)
    '--icon=NONE',  # No icon (you can add an .ico file if you have one)
    '--add-data=config.py;.',  # Include config.py in the bundle
    '--hidden-import=pandas',  # Explicitly include pandas
    '--hidden-import=openpyxl',  # Explicitly include openpyxl
    '--hidden-import=lxml',  # Explicitly include lxml
    '--hidden-import=lxml.etree',  # Explicitly include lxml.etree
    '--hidden-import=lxml._elementpath',  # Explicitly include lxml._elementpath
    '--hidden-import=bs4',  # Explicitly include beautifulsoup4
    '--hidden-import=requests',  # Explicitly include requests
    '--hidden-import=urllib3',  # Explicitly include urllib3
    '--hidden-import=dotenv',  # Explicitly include python-dotenv
    '--hidden-import=win32api',  # Explicitly include pywin32 components
    '--hidden-import=win32con',
    '--hidden-import=win32gui',
    '--hidden-import=win32process',
    '--collect-all=pandas',  # Collect all pandas data files
    '--collect-all=openpyxl',  # Collect all openpyxl data files
    '--collect-submodules=urllib3',  # Collect all urllib3 submodules
    '--noconfirm',  # Overwrite output directory without asking
    '--clean',  # Clean cache and remove temp files before building
])

print(f"\n[SUCCESS] Executable created in: dist/{app_name}.exe")
print("[INFO] You can now distribute the executable from the 'dist' folder")

