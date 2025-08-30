#!/usr/bin/env python3
"""
FileOrganizer Portable Launcher
===============================

Runs FileOrganizer without requiring system installation or admin rights.
Perfect for USB drives, shared computers, or when you can't install packages.

Features:
- No system-wide installation needed
- Downloads dependencies to local folder
- Self-contained environment
- Runs from any location
- Automatic fallback to basic functionality

Usage:
    python portable.py                    # Run main application
    python portable.py --transfer        # Run photo transfer
    python portable.py --setup          # Setup portable environment
"""

import os
import sys
import subprocess
import shutil
import tempfile
import zipfile
import urllib.request
from pathlib import Path
import json
import argparse

# Ensure we can import basic modules
try:
    import tkinter as tk
    from tkinter import messagebox, filedialog, ttk
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

class PortableLauncher:
    def __init__(self):
        self.app_dir = Path(__file__).parent
        self.portable_dir = self.app_dir / "portable_env"
        self.packages_dir = self.portable_dir / "packages"
        self.config_dir = self.app_dir / "config"
        
        # Minimal dependencies that we absolutely need
        self.core_packages = [
            "Pillow",
            "watchdog",
            "mutagen"
        ]
        
        # Optional packages that enhance functionality
        self.optional_packages = [
            "PyQt5",
            "pypdf",
            "python-docx",
            "moviepy"
        ]
    
    def setup_portable_env(self):
        """Set up portable environment"""
        print("🏗️  Setting up portable environment...")
        
        # Create directories
        self.portable_dir.mkdir(exist_ok=True)
        self.packages_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
        # Add packages directory to Python path
        sys.path.insert(0, str(self.packages_dir))
        
        # Create basic config if needed
        self.create_basic_config()
        
        # Try to install portable packages
        self.install_portable_packages()
    
    def create_basic_config(self):
        """Create minimal configuration"""
        config_file = self.config_dir / "config.json"
        
        if not config_file.exists():
            basic_config = {
                "file_categories": {
                    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
                    "Audio": [".mp3", ".wav", ".flac", ".m4a"],
                    "Documents": [".pdf", ".doc", ".docx", ".txt"],
                    "Video": [".mp4", ".avi", ".mov", ".mkv"]
                },
                "default_duplicate_action": "k",
                "portable_mode": True,
                "enable_gpu": False,
                "basic_mode": True
            }
            
            with open(config_file, 'w') as f:
                json.dump(basic_config, f, indent=2)
            
            print("✅ Basic configuration created")
    
    def install_portable_packages(self):
        """Try to install packages to local directory"""
        print("📦 Installing portable packages...")
        
        # Try pip install to local directory
        for package in self.core_packages:
            try:
                print(f"  Installing {package}...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install", 
                    "--target", str(self.packages_dir),
                    "--no-deps", package
                ], check=True, capture_output=True)
                print(f"  ✅ {package} installed")
            except subprocess.CalledProcessError:
                print(f"  ⚠️  {package} failed to install")
        
        print("✅ Portable package installation completed")
    
    def check_dependencies(self):
        """Check what dependencies are available"""
        available = {}
        
        # Add portable packages to path
        if self.packages_dir.exists():
            sys.path.insert(0, str(self.packages_dir))
        
        # Check each package
        for package_name in self.core_packages + self.optional_packages:
            try:
                # Map package names to import names
                import_name = {
                    "Pillow": "PIL",
                    "python-docx": "docx",
                    "python-magic": "magic",
                    "moviepy": "moviepy.editor"
                }.get(package_name, package_name.lower())
                
                __import__(import_name)
                available[package_name] = True
            except ImportError:
                available[package_name] = False
        
        return available
    
    def run_basic_gui(self):
        """Run basic GUI using tkinter if available"""
        if not HAS_TKINTER:
            print("❌ No GUI available. Install PyQt5 or tkinter.")
            return False
        
        class BasicFileOrganizer:
            def __init__(self):
                self.root = tk.Tk()
                self.root.title("FileOrganizer - Portable Mode")
                self.root.geometry("600x400")
                
                self.setup_ui()
                
            def setup_ui(self):
                # Main frame
                main_frame = ttk.Frame(self.root, padding="10")
                main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                
                # Title
                title_label = ttk.Label(main_frame, text="FileOrganizer - Portable Mode", 
                                       font=("Arial", 16, "bold"))
                title_label.grid(row=0, column=0, columnspan=2, pady=10)
                
                # Source folder
                ttk.Label(main_frame, text="Source Folder:").grid(row=1, column=0, sticky=tk.W)
                self.source_var = tk.StringVar()
                ttk.Entry(main_frame, textvariable=self.source_var, width=50).grid(row=1, column=1, padx=5)
                ttk.Button(main_frame, text="Browse", command=self.browse_source).grid(row=1, column=2)
                
                # Actions
                ttk.Button(main_frame, text="Preview Organization", 
                          command=self.preview_organization).grid(row=2, column=0, pady=10)
                ttk.Button(main_frame, text="Organize Files", 
                          command=self.organize_files).grid(row=2, column=1, pady=10)
                
                # Status
                self.status_var = tk.StringVar(value="Ready")
                ttk.Label(main_frame, textvariable=self.status_var).grid(row=3, column=0, columnspan=3, pady=10)
                
                # Log area
                self.log_text = tk.Text(main_frame, height=15, width=70)
                self.log_text.grid(row=4, column=0, columnspan=3, pady=10)
                
                scrollbar = ttk.Scrollbar(main_frame, command=self.log_text.yview)
                scrollbar.grid(row=4, column=3, sticky='nsew')
                self.log_text.config(yscrollcommand=scrollbar.set)
                
            def browse_source(self):
                folder = filedialog.askdirectory()
                if folder:
                    self.source_var.set(folder)
                    self.log(f"Selected folder: {folder}")
                    
            def log(self, message):
                self.log_text.insert(tk.END, f"{message}\n")
                self.log_text.see(tk.END)
                self.root.update()
                
            def preview_organization(self):
                source = self.source_var.get()
                if not source:
                    messagebox.showerror("Error", "Please select a source folder")
                    return
                
                self.status_var.set("Previewing...")
                self.log("Starting preview...")
                
                try:
                    # Basic file organization preview
                    from file_handler.file_utils import organize_files
                    from config.config_handler import ConfigHandler
                    
                    config = ConfigHandler(str(launcher.config_dir / "config.json")).config
                    summary = organize_files(source, config, preview_mode=True)
                    
                    self.log(f"Preview completed: {summary}")
                    self.status_var.set("Preview completed")
                    
                except Exception as e:
                    self.log(f"Preview failed: {e}")
                    self.status_var.set("Preview failed")
                    
            def organize_files(self):
                source = self.source_var.get()
                if not source:
                    messagebox.showerror("Error", "Please select a source folder")
                    return
                
                if not messagebox.askyesno("Confirm", "This will move files. Continue?"):
                    return
                
                self.status_var.set("Organizing...")
                self.log("Starting file organization...")
                
                try:
                    # Basic file organization
                    from file_handler.file_utils import organize_files
                    from config.config_handler import ConfigHandler
                    
                    config = ConfigHandler(str(launcher.config_dir / "config.json")).config
                    summary = organize_files(source, config, preview_mode=False)
                    
                    self.log(f"Organization completed: {summary}")
                    self.status_var.set("Organization completed")
                    
                except Exception as e:
                    self.log(f"Organization failed: {e}")
                    self.status_var.set("Organization failed")
                    
            def run(self):
                self.root.mainloop()
        
        app = BasicFileOrganizer()
        app.run()
        return True
    
    def run_command_line(self):
        """Run basic command line interface"""
        print("\n🗂️  FileOrganizer - Portable Command Line Mode")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Organize folder")
            print("2. Preview organization")
            print("3. Transfer photos")
            print("4. Exit")
            
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                folder = input("Enter folder path to organize: ").strip()
                if folder and Path(folder).exists():
                    try:
                        from file_handler.file_utils import organize_files
                        from config.config_handler import ConfigHandler
                        
                        config = ConfigHandler(str(self.config_dir / "config.json")).config
                        summary = organize_files(folder, config, preview_mode=False)
                        print(f"✅ Organization completed: {summary}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                else:
                    print("❌ Invalid folder path")
                    
            elif choice == "2":
                folder = input("Enter folder path to preview: ").strip()
                if folder and Path(folder).exists():
                    try:
                        from file_handler.file_utils import organize_files
                        from config.config_handler import ConfigHandler
                        
                        config = ConfigHandler(str(self.config_dir / "config.json")).config
                        summary = organize_files(folder, config, preview_mode=True)
                        print(f"📋 Preview: {summary}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                else:
                    print("❌ Invalid folder path")
                    
            elif choice == "3":
                try:
                    print("📸 Launching photo transfer tool...")
                    exec(open("photo_transfer.py").read())
                except Exception as e:
                    print(f"❌ Photo transfer failed: {e}")
                    
            elif choice == "4":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
    
    def launch(self, transfer_mode=False):
        """Launch the application"""
        print("🚀 FileOrganizer - Portable Mode")
        
        # Setup environment
        self.setup_portable_env()
        
        # Check dependencies
        deps = self.check_dependencies()
        print(f"📊 Available: {sum(deps.values())}/{len(deps)} packages")
        
        if transfer_mode:
            try:
                print("📸 Launching photo transfer tool...")
                exec(open("photo_transfer.py").read())
            except Exception as e:
                print(f"❌ Photo transfer failed: {e}")
                return False
        else:
            # Try GUI first, fallback to command line
            try:
                if deps.get("PyQt5", False):
                    print("🖥️  Launching PyQt5 GUI...")
                    exec(open("main.py").read())
                elif HAS_TKINTER:
                    print("🖥️  Launching basic GUI...")
                    return self.run_basic_gui()
                else:
                    print("💻 Launching command line interface...")
                    return self.run_command_line()
            except Exception as e:
                print(f"❌ GUI launch failed: {e}")
                print("💻 Falling back to command line...")
                return self.run_command_line()
        
        return True

def main():
    parser = argparse.ArgumentParser(description="FileOrganizer Portable Launcher")
    parser.add_argument("--transfer", action="store_true", help="Launch photo transfer tool")
    parser.add_argument("--setup", action="store_true", help="Setup portable environment only")
    
    args = parser.parse_args()
    
    launcher = PortableLauncher()
    
    if args.setup:
        launcher.setup_portable_env()
        print("✅ Portable environment setup completed")
        return 0
    
    success = launcher.launch(transfer_mode=args.transfer)
    return 0 if success else 1

if __name__ == "__main__":
    launcher = PortableLauncher()  # Make launcher available globally
    sys.exit(main())