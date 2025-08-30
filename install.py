#!/usr/bin/env python3
"""
FileOrganizer Easy Installer
============================

One-click installer for FileOrganizer that handles all dependencies
and setup automatically across Windows, Linux, and macOS.

Usage:
    python install.py

This will:
1. Check Python version compatibility
2. Install all required dependencies
3. Set up the application
4. Create desktop shortcuts (optional)
5. Run initial setup wizard
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
import json
import webbrowser

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(text, color=Colors.GREEN):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.END}")

def print_header():
    """Print installation header"""
    print_colored("\n" + "="*60, Colors.BLUE)
    print_colored("🗂️  FileOrganizer Easy Installer", Colors.BOLD)
    print_colored("Automated setup for all platforms", Colors.BLUE)
    print_colored("="*60 + "\n", Colors.BLUE)

def check_python_version():
    """Check if Python version is compatible"""
    print_colored("🐍 Checking Python version...", Colors.BLUE)
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_colored("❌ Python 3.8+ required. Current version: {}.{}.{}".format(
            version.major, version.minor, version.micro), Colors.RED)
        print_colored("Please upgrade Python and try again.", Colors.RED)
        return False
    
    print_colored(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible!", Colors.GREEN)
    return True

def check_pip():
    """Check if pip is available"""
    print_colored("📦 Checking pip...", Colors.BLUE)
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        print_colored("✅ pip is available", Colors.GREEN)
        return True
    except subprocess.CalledProcessError:
        print_colored("❌ pip not found", Colors.RED)
        return False

def install_dependencies():
    """Install required dependencies"""
    print_colored("📋 Installing dependencies...", Colors.BLUE)
    
    # Core requirements
    requirements = [
        "PyQt5>=5.15.0",
        "watchdog>=2.1.0",
        "Pillow>=10.0.0",
        "mutagen>=1.46.0",
        "python-magic>=0.4.27",
        "pypdf>=3.17.0",
        "python-docx>=0.8.11",
        "moviepy>=1.0.3"
    ]
    
    # GPU requirements (optional)
    gpu_requirements = [
        "pyopencl",
        "numpy"
    ]
    
    try:
        # Install core requirements
        print_colored("Installing core dependencies...", Colors.YELLOW)
        for req in requirements:
            print(f"  Installing {req}...")
            subprocess.run([sys.executable, "-m", "pip", "install", req], 
                          check=True, capture_output=True)
        
        print_colored("✅ Core dependencies installed", Colors.GREEN)
        
        # Try to install GPU dependencies
        try_gpu = input("\n🚀 Install GPU acceleration? (recommended for large files) [Y/n]: ").strip().lower()
        if try_gpu in ('', 'y', 'yes'):
            try:
                print_colored("Installing GPU dependencies...", Colors.YELLOW)
                for req in gpu_requirements:
                    print(f"  Installing {req}...")
                    subprocess.run([sys.executable, "-m", "pip", "install", req], 
                                  check=True, capture_output=True)
                print_colored("✅ GPU acceleration enabled", Colors.GREEN)
            except subprocess.CalledProcessError as e:
                print_colored("⚠️  GPU dependencies failed to install. GPU acceleration disabled.", Colors.YELLOW)
                print_colored("This is normal if you don't have OpenCL drivers.", Colors.YELLOW)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ Failed to install dependencies: {e}", Colors.RED)
        return False

def create_config():
    """Create default configuration if it doesn't exist"""
    print_colored("⚙️  Setting up configuration...", Colors.BLUE)
    
    config_path = Path("config/config.json")
    if not config_path.exists():
        default_config = {
            "file_categories": {
                "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
                "Audio": [".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac"],
                "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"],
                "Video": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"],
                "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"]
            },
            "subfolders": {
                ".pdf": "PDFs",
                ".doc": "Word_Documents",
                ".docx": "Word_Documents",
                ".txt": "Text_Files"
            },
            "default_duplicate_action": "k",
            "enable_gpu": True,
            "max_workers": 4
        }
        
        config_path.parent.mkdir(exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        
        print_colored("✅ Configuration created", Colors.GREEN)
    else:
        print_colored("✅ Configuration already exists", Colors.GREEN)

def create_launcher():
    """Create platform-specific launcher"""
    print_colored("🚀 Creating launcher...", Colors.BLUE)
    
    system = platform.system()
    app_path = Path.cwd()
    
    if system == "Windows":
        # Create Windows batch launcher
        launcher_content = f'''@echo off
cd /d "{app_path}"
python main.py %*
pause
'''
        launcher_path = app_path / "FileOrganizer.bat"
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
        print_colored("✅ Windows launcher created: FileOrganizer.bat", Colors.GREEN)
        
    else:  # Linux/macOS
        # Create shell script launcher
        launcher_content = f'''#!/bin/bash
cd "{app_path}"
python3 main.py "$@"
'''
        launcher_path = app_path / "fileorganizer.sh"
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
        
        # Make executable
        os.chmod(launcher_path, 0o755)
        print_colored("✅ Shell launcher created: fileorganizer.sh", Colors.GREEN)

def create_desktop_shortcut():
    """Create desktop shortcut (optional)"""
    create_shortcut = input("\n🖥️  Create desktop shortcut? [Y/n]: ").strip().lower()
    if create_shortcut not in ('', 'y', 'yes'):
        return
    
    system = platform.system()
    app_path = Path.cwd()
    
    try:
        if system == "Windows":
            # Windows desktop shortcut
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "FileOrganizer.lnk"
            
            # Create using PowerShell
            ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{app_path / 'FileOrganizer.bat'}"
$Shortcut.WorkingDirectory = "{app_path}"
$Shortcut.Description = "FileOrganizer - Smart File Organization Tool"
$Shortcut.Save()
'''
            subprocess.run(["powershell", "-Command", ps_script], check=True, capture_output=True)
            print_colored("✅ Desktop shortcut created", Colors.GREEN)
            
        elif system == "Linux":
            # Linux .desktop file
            desktop = Path.home() / "Desktop"
            desktop.mkdir(exist_ok=True)
            
            desktop_entry = f'''[Desktop Entry]
Version=1.0
Name=FileOrganizer
Comment=Smart File Organization Tool
Exec={app_path / "fileorganizer.sh"}
Icon={app_path / "icon.png"}
Terminal=false
Type=Application
Categories=Utility;FileManager;
StartupWMClass=FileOrganizer
'''
            
            shortcut_path = desktop / "FileOrganizer.desktop"
            with open(shortcut_path, 'w') as f:
                f.write(desktop_entry)
            
            # Make executable
            os.chmod(shortcut_path, 0o755)
            print_colored("✅ Desktop shortcut created", Colors.GREEN)
            
    except Exception as e:
        print_colored(f"⚠️  Could not create desktop shortcut: {e}", Colors.YELLOW)

def run_first_time_setup():
    """Run first-time setup wizard"""
    print_colored("\n🎯 First-Time Setup", Colors.BLUE)
    print_colored("-" * 20, Colors.BLUE)
    
    print("\nFileOrganizer is now installed! Here's how to use it:\n")
    
    print_colored("📂 Basic Usage:", Colors.BOLD)
    print("  • Run the GUI: python main.py")
    print("  • Photo Transfer: python photo_transfer.py")
    print("  • Or use the launcher you just created")
    
    print_colored("\n⚙️  Configuration:", Colors.BOLD)
    print("  • Edit config/config.json to customize file categories")
    print("  • GPU acceleration is enabled by default (if available)")
    
    print_colored("\n🚀 Quick Start:", Colors.BOLD)
    print("  1. Launch the application")
    print("  2. Select a folder to organize")
    print("  3. Preview changes first (recommended)")
    print("  4. Apply organization rules")
    
    # Test run option
    test_run = input("\n🧪 Test run FileOrganizer now? [Y/n]: ").strip().lower()
    if test_run in ('', 'y', 'yes'):
        try:
            subprocess.Popen([sys.executable, "main.py"])
            print_colored("✅ FileOrganizer launched!", Colors.GREEN)
        except Exception as e:
            print_colored(f"❌ Could not launch: {e}", Colors.RED)
            print_colored("Try running manually: python main.py", Colors.YELLOW)

def main():
    """Main installation process"""
    print_header()
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    if not check_pip():
        print_colored("Please install pip and try again.", Colors.RED)
        return False
    
    # Install dependencies
    if not install_dependencies():
        print_colored("Installation failed. Please check the errors above.", Colors.RED)
        return False
    
    # Setup application
    create_config()
    create_launcher()
    create_desktop_shortcut()
    
    # Final setup
    print_colored("\n🎉 Installation Complete!", Colors.GREEN)
    print_colored("=" * 40, Colors.GREEN)
    
    run_first_time_setup()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print_colored("\n\n❌ Installation cancelled by user", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n❌ Unexpected error: {e}", Colors.RED)
        sys.exit(1)