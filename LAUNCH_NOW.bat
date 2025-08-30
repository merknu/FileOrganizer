@echo off
REM FileOrganizer - Immediate Launch with Fixes

title FileOrganizer - Quick Launch
color 0A

echo.
echo ===========================================
echo    FileOrganizer - Quick Launch
echo ===========================================
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [WARNING] Using system Python
)

echo [LAUNCH] Starting FileOrganizer with hotfixes...

REM Try the hotfix version first
python hotfix_main.py
if %errorlevel% equ 0 (
    echo [SUCCESS] FileOrganizer launched successfully!
    goto :end
)

echo [FALLBACK] Trying photo transfer tool...
python photo_transfer.py
if %errorlevel% equ 0 (
    echo [SUCCESS] Photo transfer tool launched!
    goto :end
)

echo [FALLBACK] Trying portable mode...
python portable.py
if %errorlevel% equ 0 (
    echo [SUCCESS] Portable mode launched!
    goto :end
)

echo.
echo [HELP] All launch attempts failed. Here's what you can try:
echo.
echo 1. Free up disk space (you were low earlier)
echo 2. Run: python -m pip install --upgrade PyQt5
echo 3. Try: python run.py --check-deps
echo 4. Manual launch: python main.py
echo.

:end
echo.
echo Press any key to exit...
pause >nul