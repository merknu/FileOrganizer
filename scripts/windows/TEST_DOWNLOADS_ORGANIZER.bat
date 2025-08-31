@echo off
title Downloads Organizer Test - FileOrganizer
echo ========================================
echo      Downloads Organizer Test
echo ========================================
echo.
echo This will test the downloads organizer functionality
echo that moves files from Downloads to appropriate system folders
echo.
echo File routing examples:
echo   PDF, DOC files    → Documents/
echo   JPG, PNG files    → Pictures/
echo   MP4, AVI files    → Videos/
echo   MP3, FLAC files   → Music/
echo   ZIP, RAR files    → Documents/Archives/
echo   PY, JS files      → Documents/Code/
echo   EPUB files        → Documents/eBooks/
echo   EXE files         → Downloads/Software/ (stays)
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ from python.org
    pause
    exit /b 1
)

echo Running categorization test...
echo.
python tests/test_downloads_organizer.py --categorization-only

echo.
echo ========================================
echo.
echo Would you like to run the full test?
echo This will create sample files and demonstrate organization.
echo.
set /p choice="Run full test? (y/N): "

if /i "%choice%"=="y" goto FULLTEST
if /i "%choice%"=="yes" goto FULLTEST
goto END

:FULLTEST
echo.
echo Running full downloads organizer test...
python tests/test_downloads_organizer.py

:END
echo.
echo Test completed!
echo.
echo To use in your FileOrganizer system tray:
echo 1. Right-click system tray icon
echo 2. Quick Scenarios → 📥 Downloads Organizer
echo 3. Files will be automatically moved to correct folders
echo.
pause