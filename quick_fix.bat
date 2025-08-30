@echo off
REM Quick fix for FileOrganizer after installation issues

title FileOrganizer - Quick Fix
color 0B

echo.
echo ===========================================
echo    FileOrganizer - Quick Fix & Launch
echo ===========================================
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo [FIX] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] No virtual environment found, using system Python
)

REM Test if core dependencies work
echo [TEST] Testing core functionality...
python -c "import PyQt5; print('PyQt5: OK')" 2>nul || echo "[WARNING] PyQt5 may have issues"
python -c "import PIL; print('Pillow: OK')" 2>nul || echo "[WARNING] Pillow may have issues"
python -c "import watchdog; print('Watchdog: OK')" 2>nul || echo "[WARNING] Watchdog may have issues"
python -c "import mutagen; print('Mutagen: OK')" 2>nul || echo "[WARNING] Mutagen may have issues"

echo.
echo [INFO] Core dependencies tested. Some warnings are normal.
echo [INFO] MoviePy (video support) may not work due to disk space, but that's optional.
echo.

REM Create basic config if missing
if not exist "config\config.json" (
    echo [FIX] Creating minimal configuration...
    if not exist "config" mkdir config
    
    (
    echo {
    echo     "file_categories": {
    echo         "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
    echo         "Audio": [".mp3", ".wav", ".flac", ".m4a"],
    echo         "Documents": [".pdf", ".doc", ".docx", ".txt"],
    echo         "Video": [".mp4", ".avi", ".mov", ".mkv"]
    echo     },
    echo     "default_duplicate_action": "k",
    echo     "enable_gpu": false,
    echo     "basic_mode": true
    echo }
    ) > config\config.json
    
    echo [OK] Configuration created
)

REM Try to launch FileOrganizer
echo.
echo [LAUNCH] Starting FileOrganizer...
echo.

python main.py
if %errorlevel% neq 0 (
    echo.
    echo [ALTERNATIVE] Main GUI failed, trying photo transfer tool...
    python photo_transfer.py
    
    if %errorlevel% neq 0 (
        echo.
        echo [TROUBLESHOOTING]
        echo =================
        echo The installation had some issues due to disk space.
        echo.
        echo SOLUTIONS:
        echo 1. Free up some disk space (at least 500MB)
        echo 2. Try: python -m pip install --upgrade moviepy imageio
        echo 3. For now, video file support may be limited
        echo 4. Core file organization should still work
        echo.
        echo QUICK TEST:
        python -c "print('Python is working'); import sys; print('Python version:', sys.version)"
        echo.
    )
)

echo.
echo Press any key to exit...
pause >nul