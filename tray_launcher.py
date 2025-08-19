#!/usr/bin/env python3
"""
FileOrganizer System Tray Launcher

Launches FileOrganizer in system tray mode for background operation.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """Setup logging for the application"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "fileorganizer_tray.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def load_config():
    """Load application configuration"""
    config = {
        'gpu_config': {
            'enable_gpu': True,
            'backend': 'auto',
            'memory_limit_mb': 2048,
            'batch_size': 10,
            'fallback_to_cpu': True
        },
        'processing': {
            'max_workers': 4,
            'chunk_size_mb': 32.0,
            'recursive': True,
            'handle_duplicates': True
        },
        'ui': {
            'theme': 'light',
            'show_notifications': True,
            'minimize_to_tray': True
        },
        'background': {
            'enable_monitoring': False,
            'check_interval_minutes': 5,
            'min_file_age_seconds': 30,
            'auto_process_new_files': True
        }
    }
    
    # Try to load from config file if exists
    config_file = project_root / "config.json"
    if config_file.exists():
        try:
            import json
            with open(config_file, 'r') as f:
                saved_config = json.load(f)
                # Merge saved config with defaults
                config.update(saved_config)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
    
    return config

def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []
    
    # Check PyQt5
    try:
        from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QIcon
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("Warning: System tray is not available on this system")
    except ImportError:
        missing_deps.append("PyQt5")
    
    # Check optional dependencies
    optional_deps = []
    
    try:
        import numpy
    except ImportError:
        optional_deps.append("numpy")
    
    try:
        import cupy
    except ImportError:
        optional_deps.append("cupy")
    
    if missing_deps:
        print(f"Error: Missing required dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install PyQt5")
        return False
    
    if optional_deps:
        print(f"Info: Optional dependencies not available: {', '.join(optional_deps)}")
        print("GPU acceleration may be limited")
    
    return True

def create_desktop_shortcut():
    """Create desktop shortcut for easy access"""
    try:
        if sys.platform == "win32":
            # Windows shortcut creation
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            path = os.path.join(desktop, "FileOrganizer.lnk")
            target = sys.executable
            wDir = str(project_root)
            arguments = str(project_root / "tray_launcher.py")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = target
            shortcut.Arguments = arguments
            shortcut.WorkingDirectory = wDir
            shortcut.Description = "FileOrganizer - Background File Organization"
            shortcut.save()
            
            print(f"Desktop shortcut created: {path}")
            
    except ImportError:
        print("Note: Could not create desktop shortcut (winshell not available)")
    except Exception as e:
        print(f"Warning: Could not create desktop shortcut: {e}")

def main():
    """Main entry point"""
    logger = setup_logging()
    logger.info("Starting FileOrganizer System Tray Application")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    logger.info(f"Loaded configuration: GPU={config['gpu_config']['enable_gpu']}")
    
    try:
        # Import and create system tray app
        from gui.system_tray import create_system_tray_app
        
        logger.info("Creating system tray application...")
        app = create_system_tray_app(config)
        
        # Setup and show tray icon
        if app.setup_tray_icon():
            app.show_tray_icon()
            
            logger.info("FileOrganizer is running in system tray")
            print("🚀 FileOrganizer is now running in the background!")
            print("📌 Look for the FileOrganizer icon in your system tray")
            print("🖱️  Right-click the tray icon to access features:")
            print("   • Show/Hide main window")
            print("   • Configure background file monitoring")
            print("   • Quick organize folders")
            print("   • GPU settings and themes")
            print("   • Exit application")
            print()
            print("💡 Double-click the tray icon to open the main window")
            
            # Create desktop shortcut if requested
            if "--create-shortcut" in sys.argv:
                create_desktop_shortcut()
            
            # Show initial notification
            app.show_notification(
                "FileOrganizer Started", 
                "Background file organization is now active. Right-click for options."
            )
            
            # Run the application
            exit_code = app.exec_()
            logger.info(f"Application exited with code: {exit_code}")
            sys.exit(exit_code)
            
        else:
            logger.error("Failed to create system tray icon")
            print("❌ Error: Could not create system tray icon")
            print("System tray may not be available on this system")
            sys.exit(1)
            
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print("❌ Error: Required GUI components not available")
        print("Make sure all dependencies are installed")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

def print_help():
    """Print help information"""
    print("FileOrganizer System Tray Launcher")
    print("=" * 40)
    print()
    print("Usage:")
    print("  python tray_launcher.py [options]")
    print()
    print("Options:")
    print("  --create-shortcut    Create desktop shortcut")
    print("  --help              Show this help message")
    print()
    print("Features:")
    print("  • Background file monitoring and organization")
    print("  • GPU-accelerated processing")
    print("  • System tray integration with notifications")
    print("  • Dark/Light theme support")
    print("  • Real-time performance monitoring")
    print("  • Advanced file filtering")
    print("  • Drag-and-drop interface")
    print()
    print("The application will run in the background and can be accessed")
    print("through the system tray icon.")

if __name__ == "__main__":
    if "--help" in sys.argv:
        print_help()
        sys.exit(0)
    
    main()