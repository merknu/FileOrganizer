@echo off
title Media Transfer Hub - FileOrganizer
color 0A

:MENU
cls
echo ============================================
echo         MEDIA TRANSFER HUB
echo     Advanced File Transfer with Transcoding
echo ============================================
echo.
echo Select a transfer tool to launch:
echo.
echo   [1] Photo Transfer Tool
echo       - Advanced photo selection by date
echo       - Metadata preservation
echo       - Duplicate detection
echo.
echo   [2] Audio Transfer Tool
echo       - Audio transcoding (MP3, AAC, FLAC, etc.)
echo       - Metadata-based filtering
echo       - Audio normalization
echo       - Batch processing
echo.
echo   [3] Video Transfer Tool  
echo       - Video transcoding with ffmpeg
echo       - Resolution scaling
echo       - Format conversion
echo       - Hardware acceleration
echo.
echo   [4] Launch Main FileOrganizer
echo.
echo   [0] Exit
echo.
echo ============================================

set /p choice="Enter your choice (0-4): "

if "%choice%"=="1" goto PHOTO
if "%choice%"=="2" goto AUDIO
if "%choice%"=="3" goto VIDEO
if "%choice%"=="4" goto MAIN
if "%choice%"=="0" goto EXIT

echo Invalid choice. Please try again.
pause
goto MENU

:PHOTO
echo.
echo Launching Photo Transfer Tool...
python photo_transfer.py
if errorlevel 1 (
    echo Error launching Photo Transfer Tool
    pause
)
goto MENU

:AUDIO
echo.
echo Launching Audio Transfer Tool...
python audio_transfer.py
if errorlevel 1 (
    echo Error launching Audio Transfer Tool
    pause
)
goto MENU

:VIDEO
echo.
echo Launching Video Transfer Tool...
python video_transfer.py
if errorlevel 1 (
    echo Error launching Video Transfer Tool
    pause
)
goto MENU

:MAIN
echo.
echo Launching Main FileOrganizer...
python main.py
if errorlevel 1 (
    echo Error launching FileOrganizer
    pause
)
goto MENU

:EXIT
echo.
echo Thank you for using Media Transfer Hub!
timeout /t 2 >nul
exit