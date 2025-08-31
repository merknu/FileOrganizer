@echo off
title Video Transfer Tool - FileOrganizer
echo ========================================
echo    Video Transfer Tool with Transcoding
echo ========================================
echo.
echo Starting Video Transfer Tool...
echo.
echo Features:
echo - Smart video file detection
echo - Video transcoding with ffmpeg
echo - Resolution and quality filtering
echo - Format conversion (MP4, AVI, MKV, WebM, etc.)
echo - Hardware acceleration support
echo - Batch processing with queue management
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ from python.org
    pause
    exit /b 1
)

:: Check if required packages are installed
echo Checking dependencies...
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo Installing PyQt5...
    pip install PyQt5
)

:: Check if ffmpeg is available
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: ffmpeg is REQUIRED for Video Transfer Tool
    echo Please install ffmpeg:
    echo 1. Download from: https://ffmpeg.org/download.html
    echo 2. Extract to a folder (e.g., C:\ffmpeg)
    echo 3. Add the bin folder to your PATH
    echo.
    pause
    exit /b 1
)

:: Check if ffprobe is available
where ffprobe >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: ffprobe not found (usually comes with ffmpeg)
    echo Video metadata features may be limited
    echo.
)

:: Launch the video transfer tool
python video_transfer.py

if errorlevel 1 (
    echo.
    echo Error: Failed to launch Video Transfer Tool
    pause
)