@echo off
REM FileOrganizer Background Service Manager
REM Provides easy management of system tray and service modes

setlocal EnableDelayedExpansion

REM Set colors
set RED=[91m
set GREEN=[92m
set YELLOW=[93m
set BLUE=[94m
set PURPLE=[95m
set CYAN=[96m
set WHITE=[97m
set NC=[0m

echo %CYAN%=================================================%NC%
echo %CYAN%    FileOrganizer Background Service Manager     %NC%
echo %CYAN%=================================================%NC%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%Error: Python not found in PATH%NC%
    echo Please install Python and ensure it's added to PATH
    pause
    exit /b 1
)

REM Get current directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

if "%1"=="" goto MENU

REM Handle command line arguments
if /i "%1"=="tray" goto START_TRAY
if /i "%1"=="service-install" goto INSTALL_SERVICE
if /i "%1"=="service-start" goto START_SERVICE
if /i "%1"=="service-stop" goto STOP_SERVICE
if /i "%1"=="service-remove" goto REMOVE_SERVICE
if /i "%1"=="startup-enable" goto ENABLE_STARTUP
if /i "%1"=="startup-disable" goto DISABLE_STARTUP
if /i "%1"=="help" goto HELP

echo %RED%Unknown command: %1%NC%
goto HELP

:MENU
echo %WHITE%Select operation:%NC%
echo.
echo %GREEN%1.%NC% Start System Tray Mode
echo %GREEN%2.%NC% Configure Background Processing
echo %GREEN%3.%NC% Manage Windows Startup
echo %GREEN%4.%NC% Windows Service Management
echo %GREEN%5.%NC% View Status and Logs
echo %GREEN%6.%NC% Create Desktop Shortcut
echo %GREEN%7.%NC% Help and Information
echo %GREEN%8.%NC% Exit
echo.
set /p choice=%YELLOW%Enter choice (1-8): %NC%

if "%choice%"=="1" goto START_TRAY_MENU
if "%choice%"=="2" goto BACKGROUND_CONFIG
if "%choice%"=="3" goto STARTUP_MENU
if "%choice%"=="4" goto SERVICE_MENU
if "%choice%"=="5" goto STATUS_MENU
if "%choice%"=="6" goto CREATE_SHORTCUT
if "%choice%"=="7" goto HELP
if "%choice%"=="8" goto EXIT

echo %RED%Invalid choice. Please select 1-8.%NC%
pause
goto MENU

:START_TRAY_MENU
echo.
echo %BLUE%Starting FileOrganizer in System Tray Mode...%NC%
echo %YELLOW%This will run FileOrganizer in the background with system tray icon.%NC%
echo %YELLOW%Look for the FileOrganizer icon in your system tray.%NC%
echo.
python tray_launcher.py
goto MENU

:START_TRAY
echo %BLUE%Starting FileOrganizer System Tray...%NC%
python tray_launcher.py
exit /b 0

:BACKGROUND_CONFIG
echo.
echo %BLUE%Background Processing Configuration%NC%
echo %PURPLE%=================================%NC%
echo.
echo This will open the background processing dialog.
echo You can configure which folders to monitor and
echo set automatic file organization preferences.
echo.
pause
python tray_launcher.py --configure
goto MENU

:STARTUP_MENU
echo.
echo %BLUE%Windows Startup Management%NC%
echo %PURPLE%=========================%NC%
echo.

REM Check current startup status
python startup_manager.py status >nul 2>&1
if errorlevel 1 (
    set STARTUP_STATUS=%RED%Disabled%NC%
    set STARTUP_ACTION=enable
    set STARTUP_TEXT=Enable
) else (
    set STARTUP_STATUS=%GREEN%Enabled%NC%
    set STARTUP_ACTION=disable  
    set STARTUP_TEXT=Disable
)

echo Current Status: !STARTUP_STATUS!
echo.
echo %GREEN%1.%NC% !STARTUP_TEXT! Windows Startup
echo %GREEN%2.%NC% Create Startup Shortcut
echo %GREEN%3.%NC% Remove Startup Shortcut
echo %GREEN%4.%NC% Back to Main Menu
echo.
set /p startup_choice=%YELLOW%Enter choice (1-4): %NC%

if "%startup_choice%"=="1" (
    echo.
    echo %BLUE%Updating startup settings...%NC%
    python startup_manager.py !STARTUP_ACTION!
    pause
)
if "%startup_choice%"=="2" (
    echo.
    echo %BLUE%Creating startup shortcut...%NC%
    python startup_manager.py shortcut-add
    pause
)
if "%startup_choice%"=="3" (
    echo.
    echo %BLUE%Removing startup shortcut...%NC%
    python startup_manager.py shortcut-remove
    pause
)
if "%startup_choice%"=="4" goto MENU

goto STARTUP_MENU

:ENABLE_STARTUP
echo %BLUE%Enabling Windows startup...%NC%
python startup_manager.py enable
exit /b 0

:DISABLE_STARTUP
echo %BLUE%Disabling Windows startup...%NC%
python startup_manager.py disable
exit /b 0

:SERVICE_MENU
echo.
echo %BLUE%Windows Service Management%NC%
echo %PURPLE%=========================%NC%
echo.
echo %YELLOW%Note: Service management requires Administrator privileges%NC%
echo.

REM Check service status
python service_wrapper.py status 2>nul
set SERVICE_ERRORLEVEL=%errorlevel%

echo %GREEN%1.%NC% Install Service
echo %GREEN%2.%NC% Start Service
echo %GREEN%3.%NC% Stop Service
echo %GREEN%4.%NC% Remove Service
echo %GREEN%5.%NC% Check Service Status
echo %GREEN%6.%NC% Create Service Configuration
echo %GREEN%7.%NC% Back to Main Menu
echo.
set /p service_choice=%YELLOW%Enter choice (1-7): %NC%

if "%service_choice%"=="1" (
    echo.
    echo %BLUE%Installing Windows service...%NC%
    echo %YELLOW%Administrator privileges required.%NC%
    python service_wrapper.py install
    pause
)
if "%service_choice%"=="2" (
    echo.
    echo %BLUE%Starting service...%NC%
    python service_wrapper.py start
    pause
)
if "%service_choice%"=="3" (
    echo.
    echo %BLUE%Stopping service...%NC%
    python service_wrapper.py stop
    pause
)
if "%service_choice%"=="4" (
    echo.
    echo %BLUE%Removing service...%NC%
    echo %YELLOW%Administrator privileges required.%NC%
    python service_wrapper.py remove
    pause
)
if "%service_choice%"=="5" (
    echo.
    echo %BLUE%Checking service status...%NC%
    python service_wrapper.py status
    pause
)
if "%service_choice%"=="6" (
    echo.
    echo %BLUE%Creating service configuration...%NC%
    python service_wrapper.py config
    pause
)
if "%service_choice%"=="7" goto MENU

goto SERVICE_MENU

:INSTALL_SERVICE
echo %BLUE%Installing Windows service...%NC%
python service_wrapper.py install
exit /b 0

:START_SERVICE
echo %BLUE%Starting service...%NC%
python service_wrapper.py start
exit /b 0

:STOP_SERVICE
echo %BLUE%Stopping service...%NC%
python service_wrapper.py stop
exit /b 0

:REMOVE_SERVICE
echo %BLUE%Removing service...%NC%
python service_wrapper.py remove
exit /b 0

:STATUS_MENU
echo.
echo %BLUE%Status and Logs%NC%
echo %PURPLE%==============%NC%
echo.
echo %GREEN%1.%NC% Check System Tray Status
echo %GREEN%2.%NC% Check Service Status  
echo %GREEN%3.%NC% View Application Logs
echo %GREEN%4.%NC% View Service Logs
echo %GREEN%5.%NC% Test GPU Acceleration
echo %GREEN%6.%NC% Back to Main Menu
echo.
set /p status_choice=%YELLOW%Enter choice (1-6): %NC%

if "%status_choice%"=="1" (
    echo.
    echo %BLUE%Checking system tray processes...%NC%
    tasklist /FI "IMAGENAME eq python.exe" /FO TABLE | findstr tray_launcher
    if errorlevel 1 (
        echo %YELLOW%No system tray process found%NC%
    ) else (
        echo %GREEN%System tray process is running%NC%
    )
    pause
)
if "%status_choice%"=="2" (
    echo.
    echo %BLUE%Checking service status...%NC%
    python service_wrapper.py status
    pause
)
if "%status_choice%"=="3" (
    echo.
    echo %BLUE%Viewing application logs...%NC%
    if exist "logs\fileorganizer_tray.log" (
        type "logs\fileorganizer_tray.log" | more
    ) else (
        echo %YELLOW%No application log file found%NC%
    )
    pause
)
if "%status_choice%"=="4" (
    echo.
    echo %BLUE%Viewing service logs...%NC%
    if exist "logs\service.log" (
        type "logs\service.log" | more
    ) else (
        echo %YELLOW%No service log file found%NC%
    )
    pause
)
if "%status_choice%"=="5" (
    echo.
    echo %BLUE%Testing GPU acceleration...%NC%
    python test_enhanced_gui.py
    pause
)
if "%status_choice%"=="6" goto MENU

goto STATUS_MENU

:CREATE_SHORTCUT
echo.
echo %BLUE%Creating Desktop Shortcut%NC%
echo %PURPLE%========================%NC%
echo.
echo This will create a desktop shortcut to launch FileOrganizer
echo in system tray mode.
echo.
python tray_launcher.py --create-shortcut
echo.
pause
goto MENU

:HELP
echo.
echo %BLUE%FileOrganizer Background Service Help%NC%
echo %PURPLE%===================================%NC%
echo.
echo %YELLOW%System Tray Mode:%NC%
echo   - Runs FileOrganizer with a system tray icon
echo   - Right-click tray icon for quick access to features
echo   - Can be minimized and runs in background
echo   - Suitable for interactive desktop use
echo.
echo %YELLOW%Windows Service Mode:%NC%
echo   - Runs as a true Windows background service
echo   - No user interface, fully background operation
echo   - Starts automatically with Windows
echo   - Requires administrator privileges to install
echo.
echo %YELLOW%Command Line Usage:%NC%
echo   fileorganizer_manager.bat [command]
echo.
echo %YELLOW%Available Commands:%NC%
echo   tray              - Start system tray mode
echo   service-install   - Install Windows service
echo   service-start     - Start Windows service
echo   service-stop      - Stop Windows service
echo   service-remove    - Remove Windows service
echo   startup-enable    - Enable Windows startup
echo   startup-disable   - Disable Windows startup
echo   help              - Show this help
echo.
echo %YELLOW%Features:%NC%
echo   - GPU-accelerated file processing
echo   - Background folder monitoring
echo   - Automatic file organization
echo   - Dark/Light theme support
echo   - Real-time performance monitoring
echo   - System notifications
echo.
pause
if "%1"=="help" exit /b 0
goto MENU

:EXIT
echo.
echo %GREEN%Thank you for using FileOrganizer!%NC%
echo.
exit /b 0