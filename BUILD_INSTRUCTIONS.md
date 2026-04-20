# Building a Standalone Executable

This guide explains how to create a standalone `.exe` file that can run on any Windows computer without requiring Python installation.

## Quick Start

### Option 1: Using the Batch File (Easiest)
1. Double-click `build_exe.bat`
2. Wait for the build to complete
3. Find your executable in the `dist` folder

### Option 2: Manual Build
1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Choose your build script:
   - **With console window** (recommended for debugging):
     ```bash
     python build_console.py
     ```
   - **Without console window** (cleaner interface):
     ```bash
     python build_exe.py
     ```

3. The executable will be in the `dist` folder

## What Gets Created

- `dist/hotel_invoice_tool.exe` - The standalone executable (can be run on any Windows PC)
- `build/` - Temporary build files (can be deleted)
- `hotel_invoice_tool.spec` - PyInstaller spec file (can be used for custom builds)

## Distributing the Executable

1. Copy `dist/hotel_invoice_tool.exe` to any Windows computer
2. The executable is completely standalone - no Python or dependencies needed!
3. Users can run it directly by double-clicking or from command line:
   ```bash
   hotel_invoice_tool.exe --file "path\to\bookings.xlsx" --sender-name "Your Name" --client-name "Client Name" --mailer web --outlook-host live
   ```

## Important Notes

- **Environment Variables**: Users will need to create a `.env` file in the same directory as the executable, or pass credentials via command line:
  ```bash
  hotel_invoice_tool.exe --google-api-key "YOUR_KEY" --google-cx "YOUR_CX" ...
  ```

- **File Paths**: Users need to provide full paths to their Excel files:
  ```bash
  hotel_invoice_tool.exe --file "C:\Users\Username\Downloads\bookings.xlsx" ...
  ```

- **Console vs Windowed**:
  - `build_console.py` - Shows console output (good for debugging)
  - `build_exe.py` - No console window (cleaner, but harder to debug)

## Troubleshooting

### If the executable is too large:
The executable includes all Python dependencies. This is normal and expected (usually 50-100MB).

### If you get "ModuleNotFoundError":
Add the missing module to the `--hidden-import` list in the build script.

### If Excel files don't work:
Make sure `openpyxl` and `pandas` are properly included (already in the build script).

## Advanced: Customizing the Build

Edit the build script to:
- Add an icon: `--icon=path/to/icon.ico`
- Change the name: Modify `app_name` variable
- Include additional files: `--add-data="file.txt;."`

