@echo off
title Audio Transfer Tool - FileOrganizer
echo ========================================
echo    Audio Transfer Tool with Transcoding
echo ========================================
echo.
echo Starting Audio Transfer Tool...
echo.
echo Features:
echo - Smart audio file detection
echo - Audio format transcoding (MP3, AAC, FLAC, OGG, etc.)
echo - Metadata-based filtering
echo - Audio normalization and effects
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

python -c "import mutagen" >nul 2>&1
if errorlevel 1 (
    echo Installing mutagen for audio metadata...
    pip install mutagen
)

:: Check if ffmpeg is available
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: ffmpeg not found in PATH
    echo Transcoding features will not be available
    echo Download ffmpeg from: https://ffmpeg.org/download.html
    echo.
    pause
)

:: Launch the audio transfer tool
python audio_transfer.py

if errorlevel 1 (
    echo.
    echo Error: Failed to launch Audio Transfer Tool
    pause
)