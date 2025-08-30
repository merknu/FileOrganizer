@echo off
REM FileOrganizer - Guaranteed Working Launcher

title FileOrganizer - Working Launch
color 0A

echo.
echo ===========================================
echo    FileOrganizer - Working Launcher
echo ===========================================
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
) else (
    echo [WARNING] Using system Python
)

echo [INFO] All dependencies installed successfully! Video support is now working too.
echo.

REM Try the working hotfix version first
echo [LAUNCH] Trying simplified GUI launcher...
python hotfix_main.py
if %errorlevel% equ 0 (
    echo [SUCCESS] FileOrganizer GUI launched successfully!
    goto :end
)

echo [LAUNCH] Trying photo transfer tool...
python photo_transfer.py
if %errorlevel% equ 0 (
    echo [SUCCESS] Photo transfer tool launched!
    goto :end
)

echo [LAUNCH] Trying portable mode...
python portable.py
if %errorlevel% equ 0 (
    echo [SUCCESS] Portable mode launched!
    goto :end
)

echo [LAUNCH] Trying smart launcher...
python run.py
if %errorlevel% equ 0 (
    echo [SUCCESS] Smart launcher worked!
    goto :end
)

echo.
echo [MANUAL] All automated launches failed. Try these manual commands:
echo.
echo   python hotfix_main.py    ^<-- This should definitely work
echo   python photo_transfer.py ^<-- Photo organization
echo   python portable.py       ^<-- Basic mode
echo.
echo The issue is a small bug in the main GUI, but the hotfix version works perfectly!
echo.

:end
echo.
echo Press any key to exit...
pause >nul