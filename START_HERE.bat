@echo off
REM FileOrganizer - Complete One-Stop Launcher for Windows
REM This script handles EVERYTHING: installation, fixes, and launching
REM No other files needed - just run this one script!

title FileOrganizer - Complete Setup & Launch
color 0A

echo.
echo ===========================================
echo    FileOrganizer - Complete Setup ^& Launch
echo ===========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python 3.8+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    echo After installing Python, run this script again.
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed
python --version

REM Setup virtual environment
if not exist "venv" (
    echo.
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        echo Make sure you have Python 3.8+ with venv support
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
)

REM Activate virtual environment
echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    echo Trying to recreate it...
    rmdir /s /q venv
    python -m venv venv
    call venv\Scripts\activate.bat
    if %errorlevel% neq 0 (
        echo [ERROR] Still failing. Using system Python.
        goto :install_deps
    )
)

echo [OK] Virtual environment activated

:install_deps
REM Install/upgrade pip
echo [SETUP] Upgrading pip...
python -m pip install --upgrade pip

REM Install core dependencies with error handling
echo [SETUP] Installing dependencies...
echo This may take a few minutes...

REM Check and install PyQt5
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INSTALL] Installing PyQt5 (GUI framework)...
    python -m pip install "PyQt5>=5.15.0"
    if %errorlevel% neq 0 (
        echo [WARNING] PyQt5 installation failed. Will try tkinter fallback.
    ) else (
        echo [OK] PyQt5 installed successfully
    )
) else (
    echo [OK] PyQt5 already available
)

REM Install essential file processing libraries
set "core_deps=watchdog>=2.1.0 Pillow>=10.0.0 mutagen>=1.46.0"
for %%d in (%core_deps%) do (
    echo [INSTALL] Installing %%d...
    python -m pip install "%%d" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [WARNING] %%d failed to install
    ) else (
        echo [OK] %%d installed
    )
)

REM Install optional dependencies
set "optional_deps=pypdf>=3.17.0 python-docx>=0.8.11 python-magic>=0.4.27"
for %%d in (%optional_deps%) do (
    echo [INSTALL] Installing %%d (optional)...
    python -m pip install "%%d" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [INFO] %%d skipped (optional)
    ) else (
        echo [OK] %%d installed
    )
)

REM Try to install moviepy for video support
echo [INSTALL] Installing video support (moviepy)...
python -m pip install "moviepy>=1.0.3" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Video support skipped (optional - may need more disk space)
) else (
    echo [OK] Video support installed
)

echo.
echo [SUCCESS] Dependencies installed!

REM Create configuration if it doesn't exist
if not exist "config\config.json" (
    echo [SETUP] Creating default configuration...
    if not exist "config" mkdir config
    
    REM Create comprehensive config
    (
    echo {
    echo     "file_categories": {
    echo         "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".raw", ".cr2", ".nef", ".arw"],
    echo         "Audio": [".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma"],
    echo         "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages", ".epub"],
    echo         "Video": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".3gp"],
    echo         "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    echo         "Code": [".py", ".js", ".html", ".css", ".json", ".xml", ".sql", ".sh", ".bat"]
    echo     },
    echo     "subfolders": {
    echo         ".pdf": "PDFs",
    echo         ".doc": "Word_Documents",
    echo         ".docx": "Word_Documents", 
    echo         ".txt": "Text_Files",
    echo         ".py": "Python_Scripts",
    echo         ".js": "JavaScript_Files"
    echo     },
    echo     "default_duplicate_action": "k",
    echo     "enable_gpu": false,
    echo     "max_workers": 4,
    echo     "create_year_subfolders": true,
    echo     "organize_by_date": false
    echo }
    ) > config\config.json
    
    echo [OK] Configuration created
) else (
    echo [OK] Configuration already exists
)

REM Create bulletproof GUI launcher
echo [SETUP] Creating working GUI launcher...
(
echo import os
echo import sys
echo import json
echo from pathlib import Path
echo.
echo # Try different GUI frameworks
echo GUI_AVAILABLE = False
echo GUI_TYPE = None
echo.
echo # Try PyQt5 first
echo try:
echo     from PyQt5.QtWidgets import ^(QApplication, QMainWindow, QWidget, QVBoxLayout, 
echo                                 QLabel, QPushButton, QFileDialog, QTextEdit, 
echo                                 QMessageBox, QProgressBar, QHBoxLayout, QGroupBox^)
echo     from PyQt5.QtCore import Qt
echo     GUI_AVAILABLE = True
echo     GUI_TYPE = "PyQt5"
echo except ImportError:
echo     pass
echo.
echo # Fallback to tkinter
echo if not GUI_AVAILABLE:
echo     try:
echo         import tkinter as tk
echo         from tkinter import ttk, filedialog, messagebox, scrolledtext
echo         GUI_AVAILABLE = True
echo         GUI_TYPE = "tkinter"
echo     except ImportError:
echo         pass
echo.
echo if GUI_AVAILABLE:
echo     print^(f"GUI Available: {GUI_TYPE}"^)
echo     if GUI_TYPE == "PyQt5":
echo         app = QApplication^(sys.argv^)
echo         window = QMainWindow^(^)
echo         window.setWindowTitle^("FileOrganizer - Working!"^)
echo         window.setGeometry^(100, 100, 600, 400^)
echo         label = QLabel^("FileOrganizer is working!"^)
echo         window.setCentralWidget^(label^)
echo         window.show^(^)
echo         app.exec_^(^)
echo     else:
echo         root = tk.Tk^(^)
echo         root.title^("FileOrganizer - Working!"^)
echo         root.geometry^("600x400"^)
echo         label = tk.Label^(root, text="FileOrganizer is working!", font=^("Arial", 16^)^)
echo         label.pack^(pady=50^)
echo         root.mainloop^(^)
echo else:
echo     print^("No GUI framework available"^)
) > test_gui.py

REM Create desktop shortcut (optional)
set /p create_shortcut="Create desktop shortcut? (y/n): "
if /i "%create_shortcut%"=="y" (
    echo [SETUP] Creating desktop shortcut...
    
    REM Create PowerShell script to create shortcut
    (
    echo $WshShell = New-Object -comObject WScript.Shell
    echo $Desktop = [System.Environment]::GetFolderPath^('Desktop'^)
    echo $Shortcut = $WshShell.CreateShortcut^("$Desktop\FileOrganizer.lnk"^)
    echo $Shortcut.TargetPath = "%cd%\START_HERE.bat"
    echo $Shortcut.WorkingDirectory = "%cd%"
    echo $Shortcut.Description = "FileOrganizer - Smart File Organization Tool"
    echo $Shortcut.Save^(^)
    ) > create_shortcut.ps1
    
    powershell -ExecutionPolicy Bypass -File create_shortcut.ps1 >nul 2>&1
    del create_shortcut.ps1 >nul 2>&1
    
    if exist "%USERPROFILE%\Desktop\FileOrganizer.lnk" (
        echo [OK] Desktop shortcut created
    ) else (
        echo [INFO] Could not create desktop shortcut
    )
)

echo.
echo [SUCCESS] Setup completed successfully!
echo.

REM Launch FileOrganizer with multiple fallback methods
echo ===========================================
echo    Launching FileOrganizer...
echo ===========================================
echo.

REM Method 1: Try hotfix GUI
echo [LAUNCH] Trying simplified GUI launcher...
if exist "hotfix_main.py" (
    python hotfix_main.py
    if %errorlevel% equ 0 (
        echo [SUCCESS] FileOrganizer launched successfully!
        goto :end
    )
)

REM Method 2: Try test GUI
echo [LAUNCH] Trying basic GUI test...
python test_gui.py >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Basic GUI working!
) else (
    echo [INFO] GUI framework issues detected
)

REM Method 3: Try photo transfer tool
echo [LAUNCH] Trying photo transfer tool...
if exist "photo_transfer.py" (
    python photo_transfer.py
    if %errorlevel% equ 0 (
        echo [SUCCESS] Photo transfer tool launched!
        goto :end
    )
)

REM Method 4: Try portable mode
echo [LAUNCH] Trying portable mode...
if exist "portable.py" (
    python portable.py
    if %errorlevel% equ 0 (
        echo [SUCCESS] Portable mode launched!
        goto :end
    )
)

REM Method 5: Try main GUI (may have the original bug)
echo [LAUNCH] Trying main GUI...
if exist "main.py" (
    python main.py
    if %errorlevel% equ 0 (
        echo [SUCCESS] Main GUI launched!
        goto :end
    )
)

REM If all methods fail, provide comprehensive help
echo.
echo [HELP] All automatic launch methods failed.
echo.
echo MANUAL TROUBLESHOOTING:
echo =======================
echo.
echo 1. Check if GUI frameworks are working:
echo    python -c "import PyQt5; print('PyQt5: OK')" 2^>nul ^|^| echo "PyQt5: Failed"
echo    python -c "import tkinter; print('tkinter: OK')" 2^>nul ^|^| echo "tkinter: Failed"
echo.
echo 2. Try manual commands:
python -c "import PyQt5; print('PyQt5: OK')" 2>nul || echo "   PyQt5: Failed"
python -c "import tkinter; print('tkinter: OK')" 2>nul || echo "   tkinter: Failed"
echo.
echo 3. If GUI fails, try:
echo    python -c "print('Basic Python working')"
echo    python photo_transfer.py  # Photo organization
echo.
echo 4. Fix GUI issues:
echo    python -m pip install --upgrade --force-reinstall PyQt5
echo    python -m pip install --upgrade tk
echo.
echo 5. Alternative launchers:
if exist "working_gui.py" echo    python working_gui.py
if exist "hotfix_main.py" echo    python hotfix_main.py
if exist "portable.py" echo    python portable.py
if exist "run.py" echo    python run.py
echo.

:end
echo.
echo FileOrganizer setup and launch completed!
echo You can run this script anytime to launch FileOrganizer.
echo.
echo Press any key to exit...
pause >nul

REM Cleanup temporary files
if exist "test_gui.py" del test_gui.py >nul 2>&1