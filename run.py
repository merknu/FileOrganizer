#!/usr/bin/env python3
"""
FileOrganizer Smart Launcher
============================

Intelligent launcher that automatically handles dependencies and runs FileOrganizer.
This script makes it incredibly easy to run FileOrganizer without manual setup.

Usage:
    python run.py                    # Launch main GUI
    python run.py --transfer        # Launch photo transfer tool
    python run.py --check-deps     # Check dependencies only
    python run.py --install-deps   # Install missing dependencies
    python run.py --portable       # Run in portable mode
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path
import argparse
import json

# Color codes for cross-platform terminal output
class Colors:
    if os.name == 'nt':  # Windows
        GREEN = YELLOW = RED = BLUE = BOLD = END = ''
    else:  # Unix/Linux/macOS
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        BLUE = '\033[94m'
        BOLD = '\033[1m'
        END = '\033[0m'

def print_colored(text, color=Colors.GREEN):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.END}")

def print_status(message, status="info"):
    """Print status message with appropriate color"""
    colors = {
        "success": Colors.GREEN,
        "warning": Colors.YELLOW,
        "error": Colors.RED,
        "info": Colors.BLUE
    }
    color = colors.get(status, Colors.BLUE)
    print_colored(f"[FileOrganizer] {message}", color)

def check_dependency(module_name, package_name=None, min_version=None):
    """Check if a dependency is available and optionally check version"""
    if package_name is None:
        package_name = module_name
    
    try:
        module = importlib.import_module(module_name)
        
        if min_version and hasattr(module, '__version__'):
            installed_version = module.__version__
            # Simple version comparison (works for most cases)
            if installed_version < min_version:
                return False, f"Version {installed_version} < {min_version}"
        
        return True, "OK"
    except ImportError:
        return False, "Not installed"

def get_required_dependencies():
    """Get list of required dependencies with their import names"""
    return [
        # (import_name, pip_package_name, min_version, required)
        ("PyQt5", "PyQt5", "5.15.0", True),
        ("watchdog", "watchdog", "2.1.0", True),
        ("PIL", "Pillow", "10.0.0", True),
        ("mutagen", "mutagen", "1.46.0", True),
        ("pypdf", "pypdf", "3.17.0", True),
        ("docx", "python-docx", "0.8.11", True),
        ("moviepy.editor", "moviepy", "1.0.3", True),
        ("magic", "python-magic", "0.4.27", False),  # Optional on Windows
        ("pyopencl", "pyopencl", None, False),  # Optional GPU acceleration
        ("numpy", "numpy", None, False),  # Optional GPU acceleration
    ]

def check_all_dependencies():
    """Check all dependencies and return status"""
    print_status("Checking dependencies...")
    
    missing_required = []
    missing_optional = []
    
    for import_name, package_name, min_version, required in get_required_dependencies():
        available, status = check_dependency(import_name, package_name, min_version)
        
        if available:
            print_colored(f"  ✅ {package_name}: {status}", Colors.GREEN)
        else:
            print_colored(f"  ❌ {package_name}: {status}", Colors.RED)
            if required:
                missing_required.append(package_name)
            else:
                missing_optional.append(package_name)
    
    return missing_required, missing_optional

def install_dependencies(packages, optional=False):
    """Install missing dependencies"""
    if not packages:
        return True
    
    dep_type = "optional" if optional else "required"
    print_status(f"Installing {dep_type} dependencies...")
    
    for package in packages:
        try:
            print_colored(f"  Installing {package}...", Colors.YELLOW)
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                          check=True, capture_output=True, text=True)
            print_colored(f"  ✅ {package} installed", Colors.GREEN)
        except subprocess.CalledProcessError as e:
            if optional:
                print_colored(f"  ⚠️  {package} failed to install (optional)", Colors.YELLOW)
            else:
                print_colored(f"  ❌ {package} failed to install: {e}", Colors.RED)
                return False
    
    return True

def create_minimal_config():
    """Create minimal config if it doesn't exist"""
    config_path = Path("config/config.json")
    
    if not config_path.exists():
        print_status("Creating default configuration...")
        
        config_path.parent.mkdir(exist_ok=True)
        
        minimal_config = {
            "file_categories": {
                "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
                "Audio": [".mp3", ".wav", ".flac", ".m4a"],
                "Documents": [".pdf", ".doc", ".docx", ".txt"],
                "Video": [".mp4", ".avi", ".mov", ".mkv"]
            },
            "default_duplicate_action": "k",
            "enable_gpu": True
        }
        
        with open(config_path, 'w') as f:
            json.dump(minimal_config, f, indent=2)
        
        print_status("Default configuration created", "success")

def launch_application(transfer_mode=False):
    """Launch the main application"""
    try:
        if transfer_mode:
            print_status("Launching Photo Transfer Tool...")
            import photo_transfer
            return True
        else:
            print_status("Launching FileOrganizer GUI...")
            import main
            return True
            
    except ImportError as e:
        print_status(f"Failed to import application modules: {e}", "error")
        return False
    except Exception as e:
        print_status(f"Failed to launch application: {e}", "error")
        return False

def run_portable_mode():
    """Run in portable mode without installing system-wide dependencies"""
    print_status("Running in portable mode...")
    
    # Try to use local packages first
    local_packages = Path("portable_packages")
    if local_packages.exists():
        sys.path.insert(0, str(local_packages))
    
    # Create minimal environment
    create_minimal_config()
    
    # Try to run with available dependencies
    missing_required, missing_optional = check_all_dependencies()
    
    if missing_required:
        print_status("Missing required dependencies for portable mode:", "error")
        for dep in missing_required:
            print_colored(f"  - {dep}", Colors.RED)
        print_status("Try running: python run.py --install-deps", "warning")
        return False
    
    return launch_application()

def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(description="FileOrganizer Smart Launcher")
    parser.add_argument("--transfer", action="store_true", 
                       help="Launch photo transfer tool")
    parser.add_argument("--check-deps", action="store_true",
                       help="Check dependencies only")
    parser.add_argument("--install-deps", action="store_true",
                       help="Install missing dependencies")
    parser.add_argument("--portable", action="store_true",
                       help="Run in portable mode")
    parser.add_argument("--force-install", action="store_true",
                       help="Force reinstall all dependencies")
    
    args = parser.parse_args()
    
    # Print header
    print_colored("\n🗂️  FileOrganizer Smart Launcher", Colors.BOLD)
    print_colored("=" * 40, Colors.BLUE)
    
    # Handle specific modes
    if args.portable:
        success = run_portable_mode()
        return 0 if success else 1
    
    # Check dependencies
    missing_required, missing_optional = check_all_dependencies()
    
    if args.check_deps:
        if not missing_required:
            print_status("All required dependencies are available!", "success")
        return 0 if not missing_required else 1
    
    # Install dependencies if requested or needed
    if args.install_deps or args.force_install or missing_required:
        if args.force_install:
            all_deps = [pkg for _, pkg, _, _ in get_required_dependencies()]
            install_dependencies(all_deps)
        else:
            # Install required dependencies
            if missing_required and not install_dependencies(missing_required):
                print_status("Failed to install required dependencies", "error")
                return 1
            
            # Optionally install optional dependencies
            if missing_optional:
                install_opt = input(f"\nInstall optional dependencies for enhanced features? [y/N]: ").strip().lower()
                if install_opt in ('y', 'yes'):
                    install_dependencies(missing_optional, optional=True)
        
        print_status("Dependencies installed successfully!", "success")
        
        # Re-check after installation
        missing_required, missing_optional = check_all_dependencies()
    
    # Check if we can run
    if missing_required:
        print_status("Cannot run: missing required dependencies", "error")
        print_status("Run with --install-deps to install them", "warning")
        return 1
    
    # Create config if needed
    create_minimal_config()
    
    # Launch application
    success = launch_application(transfer_mode=args.transfer)
    
    if success:
        print_status("Application launched successfully!", "success")
        return 0
    else:
        print_status("Failed to launch application", "error")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_colored("\n\nOperation cancelled by user", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\nUnexpected error: {e}", Colors.RED)
        sys.exit(1)