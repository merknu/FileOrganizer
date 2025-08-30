@echo off
REM FileOrganizer Easy Setup and Launcher for Windows
REM Double-click this file to install and run FileOrganizer!

title FileOrganizer - Easy Setup
color 0A

echo.
echo ===========================================
echo    FileOrganizer - Easy Setup ^& Launch
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
    pause
    exit /b 1
)

echo [OK] Python is installed
python --version

REM Check if we're in a virtual environment, if not, create one
if not exist "venv" (
    echo.
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

echo [OK] Virtual environment activated

REM Install/upgrade pip
echo [SETUP] Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo [SETUP] Installing dependencies...
echo This may take a few minutes...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install some dependencies
    echo Trying alternative installation...
    
    REM Try installing core dependencies one by one
    python -m pip install PyQt5^>=5.15.0
    python -m pip install watchdog^>=2.1.0
    python -m pip install Pillow^>=10.0.0
    python -m pip install mutagen^>=1.46.0
    python -m pip install pypdf^>=3.17.0
    python -m pip install python-docx^>=0.8.11
    python -m pip install moviepy^>=1.0.3
    
    echo [WARNING] Some optional dependencies may have failed to install
    echo The application should still work with core functionality
)

echo.
echo [SUCCESS] Setup completed!
echo.

REM Create desktop shortcut (optional)
set /p create_shortcut="Create desktop shortcut? (y/n): "
if /i "%create_shortcut%"=="y" (
    echo [SETUP] Creating desktop shortcut...
    
    REM Create PowerShell script to create shortcut
    (
    echo $WshShell = New-Object -comObject WScript.Shell
    echo $Desktop = [System.Environment]::GetFolderPath('Desktop'^)
    echo $Shortcut = $WshShell.CreateShortcut("$Desktop\FileOrganizer.lnk"^)
    echo $Shortcut.TargetPath = "%cd%\START_HERE.bat"
    echo $Shortcut.WorkingDirectory = "%cd%"
    echo $Shortcut.Description = "FileOrganizer - Smart File Organization Tool"
    echo $Shortcut.Save(^)
    ) > create_shortcut.ps1
    
    powershell -ExecutionPolicy Bypass -File create_shortcut.ps1 >nul 2>&1
    del create_shortcut.ps1 >nul 2>&1
    
    if exist "%USERPROFILE%\Desktop\FileOrganizer.lnk" (
        echo [OK] Desktop shortcut created
    ) else (
        echo [WARNING] Could not create desktop shortcut
    )
)

REM Check if this is first run
if not exist "config\config.json" (
    echo.
    echo [FIRST RUN] Setting up configuration...
    if not exist "config" mkdir config
    
    REM Create basic config
    (
    echo {
    echo     "file_categories": {
    echo         "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
    echo         "Audio": [".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac"],
    echo         "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf"],
    echo         "Video": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"],
    echo         "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"]
    echo     },
    echo     "subfolders": {
    echo         ".pdf": "PDFs",
    echo         ".doc": "Word_Documents",
    echo         ".docx": "Word_Documents",
    echo         ".txt": "Text_Files"
    echo     },
    echo     "default_duplicate_action": "k",
    echo     "enable_gpu": true
    echo }
    ) > config\config.json
    
    echo [OK] Default configuration created
)

REM Launch the application
echo.
echo ===========================================
echo    Launching FileOrganizer...
echo ===========================================
echo.

REM Try to launch with GUI
python main.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to launch GUI. Trying basic mode...
    python -c "print('Testing basic Python functionality...')"
    
    REM Show troubleshooting info
    echo.
    echo TROUBLESHOOTING:
    echo ================
    echo 1. Make sure you have Python 3.8+ installed
    echo 2. Try running: python -m pip install --upgrade PyQt5
    echo 3. On Windows, you may need: python -m pip install PyQt5-tools
    echo 4. For GUI issues, try: python photo_transfer.py
    echo.
)

echo.
echo Press any key to exit...
pause >nul