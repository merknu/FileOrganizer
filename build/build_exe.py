#!/usr/bin/env python3
"""
Build script for creating FileOrganizer executable
Automates the PyInstaller build process with optimization
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import argparse
import json
import platform

class ExeBuilder:
    """Handles the executable building process"""
    
    def __init__(self, debug=False, clean=True, compress=True):
        self.debug = debug
        self.clean = clean
        self.compress = compress
        self.project_root = Path(__file__).parent.parent  # Go up one level from build/
        self.src_dir = self.project_root / 'src'
        self.build_dir = self.project_root / 'build'
        self.dist_dir = self.project_root / 'dist'
        self.releases_dir = self.project_root / 'releases' / 'latest'
        self.platform = platform.system().lower()
        
    def check_requirements(self):
        """Check if required tools are installed"""
        print("Checking requirements...")
        
        # Check Python version
        if sys.version_info < (3, 7):
            print("ERROR: Python 3.7+ is required")
            return False
        print(f"OK: Python {sys.version}")
        
        # Check PyInstaller
        try:
            import PyInstaller
            print(f"OK: PyInstaller {PyInstaller.__version__}")
        except ImportError:
            print("ERROR: PyInstaller not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
            
        # Check for UPX (optional, for compression)
        if self.compress:
            upx_path = shutil.which("upx")
            if upx_path:
                print(f"OK: UPX found at {upx_path}")
            else:
                print("WARNING: UPX not found. Compression will be disabled.")
                print("   Download from: https://github.com/upx/upx/releases")
                self.compress = False
                
        return True
    
    def clean_build(self):
        """Clean previous build artifacts"""
        if self.clean:
            print("\nCleaning previous builds...")
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
                print(f"   Removed {self.build_dir}")
            if self.dist_dir.exists():
                shutil.rmtree(self.dist_dir)
                print(f"   Removed {self.dist_dir}")
    
    def prepare_resources(self):
        """Prepare resource files for bundling"""
        print("\nPreparing resources...")
        
        # Create resources directory if it doesn't exist
        resources_dir = self.project_root / 'resources'
        resources_dir.mkdir(exist_ok=True)
        
        # Create default icons if they don't exist
        icon_ico_path = resources_dir / 'icon.ico'
        icon_icns_path = resources_dir / 'icon.icns'
        
        if not icon_ico_path.exists():
            print("   WARNING: No icon.ico found. Using default.")
            
        if not icon_icns_path.exists():
            print("   WARNING: No icon.icns found. Creating placeholder.")
            # Create minimal icns file to prevent PyInstaller errors
            icon_icns_path.write_bytes(b'')
            
        # Create version info file
        self.create_version_info()
        
        return True
    
    def create_version_info(self):
        """Create version information file for Windows"""
        if self.platform != 'windows':
            return
            
        version_info = """
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(0, 2, 9, 0),
    prodvers=(0, 2, 9, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'FileOrganizer Team'),
        StringStruct(u'FileDescription', u'Advanced File Organization Tool - Alpha'),
        StringStruct(u'FileVersion', u'0.2.009.0'),
        StringStruct(u'InternalName', u'FileOrganizer'),
        StringStruct(u'LegalCopyright', u'Copyright 2024 FileOrganizer Team'),
        StringStruct(u'OriginalFilename', u'FileOrganizer.exe'),
        StringStruct(u'ProductName', u'FileOrganizer Alpha'),
        StringStruct(u'ProductVersion', u'0.2.009.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
        version_file = self.project_root / 'version_info.txt'
        version_file.write_text(version_info, encoding='utf-8')
        print(f"   Created {version_file}")
    
    def optimize_imports(self):
        """Create optimized imports file to reduce size"""
        print("\nOptimizing imports...")
        
        # Create a hook file for better import handling
        hooks_dir = self.project_root / 'hooks'
        hooks_dir.mkdir(exist_ok=True)
        
        hook_content = '''
"""Custom PyInstaller hooks for FileOrganizer"""

# Exclude test modules
excludedimports = ['pytest', 'unittest', 'test', 'tests']

# Include only necessary PyQt5 modules
hiddenimports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui', 
    'PyQt5.QtWidgets',
]
'''
        hook_file = hooks_dir / 'hook-fileorganizer.py'
        hook_file.write_text(hook_content)
        print(f"   Created {hook_file}")
    
    def build_executable(self):
        """Run PyInstaller to build the executable"""
        print("\nBuilding executable...")
        
        # Prepare PyInstaller arguments
        main_script = str(self.src_dir / 'core' / 'main.py')
        args = [
            main_script,
            '--name=FileOrganizer',
            '--clean',
            '--noconfirm',
            f'--distpath={self.dist_dir}',
            f'--workpath={self.build_dir / "temp"}',
        ]
        
        # Add platform-specific options
        if self.platform == 'windows':
            args.extend([
                '--windowed',  # No console window
                '--version-file=version_info.txt',
            ])
        elif self.platform == 'darwin':  # macOS
            args.extend([
                '--windowed',
                '--osx-bundle-identifier=com.fileorganizer.app',
            ])
        else:  # Linux
            args.extend([
                '--windowed',
            ])
        
        # Debug or release mode
        if self.debug:
            args.extend(['--debug=all', '--console'])
        else:
            args.append('--onefile')  # Single file in release mode
            
        # Compression
        if self.compress:
            args.append('--upx-dir=upx')  # Specify UPX directory if needed
        
        # Use spec file if it exists
        spec_file = self.build_dir / 'FileOrganizer.spec'
        if spec_file.exists():
            print(f"   Using spec file: {spec_file}")
            args = [str(spec_file)]
        
        # Run PyInstaller
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'PyInstaller'] + args,
                cwd=self.project_root,
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                print("OK: Build successful!")
                return True
            else:
                print("ERROR: Build failed!")
                return False
                
        except Exception as e:
            print(f"ERROR: Build error: {e}")
            return False
    
    def create_installer(self):
        """Create an installer for the executable"""
        print("\nCreating installer...")
        
        if self.platform == 'windows':
            # Create Inno Setup script
            self.create_inno_setup_script()
        elif self.platform == 'darwin':
            # Create DMG for macOS
            self.create_dmg()
        else:
            # Create AppImage or deb/rpm for Linux
            self.create_linux_package()
    
    def create_inno_setup_script(self):
        """Create Inno Setup script for Windows installer"""
        inno_script = '''
[Setup]
AppName=FileOrganizer
AppVersion=3.0.0
AppPublisher=FileOrganizer Team
AppPublisherURL=https://github.com/FileOrganizer
DefaultDirName={autopf}\FileOrganizer
DefaultGroupName=FileOrganizer
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=FileOrganizer_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\FileOrganizer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\FileOrganizer"; Filename: "{app}\FileOrganizer.exe"
Name: "{group}\{cm:UninstallProgram,FileOrganizer}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\FileOrganizer"; Filename: "{app}\FileOrganizer.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\FileOrganizer.exe"; Description: "{cm:LaunchProgram,FileOrganizer}"; Flags: nowait postinstall skipifsilent
'''
        
        setup_file = self.project_root / 'setup.iss'
        setup_file.write_text(inno_script)
        print(f"   Created {setup_file}")
        print("   Run Inno Setup Compiler to create installer")
    
    def create_dmg(self):
        """Create DMG for macOS"""
        print("   DMG creation for macOS - TODO")
        # Implementation for creating macOS DMG
        
    def create_linux_package(self):
        """Create Linux package"""
        print("   Linux package creation - TODO")
        # Implementation for creating Linux packages
    
    def print_summary(self):
        """Print build summary"""
        print("\n" + "="*50)
        print("BUILD SUMMARY")
        print("="*50)
        
        exe_path = self.dist_dir / 'FileOrganizer.exe'
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"OK: Executable: {exe_path}")
            print(f"Size: {size_mb:.2f} MB")
            print(f"Platform: {self.platform}")
            print(f"Debug: {self.debug}")
            print(f"Compressed: {self.compress}")
        else:
            print("ERROR: No executable found")
            
        print("="*50)
    
    def run(self):
        """Run the complete build process"""
        print("FileOrganizer EXE Builder")
        print("="*50)
        
        if not self.check_requirements():
            return False
            
        self.clean_build()
        self.prepare_resources()
        self.optimize_imports()
        
        if self.build_executable():
            self.create_installer()
            self.print_summary()
            return True
        
        return False

def main():
    """Main entry point for build script"""
    parser = argparse.ArgumentParser(description='Build FileOrganizer executable')
    parser.add_argument('--debug', action='store_true', help='Build in debug mode')
    parser.add_argument('--no-clean', action='store_true', help='Don\'t clean previous builds')
    parser.add_argument('--no-compress', action='store_true', help='Disable UPX compression')
    parser.add_argument('--installer', action='store_true', help='Create installer after build')
    
    args = parser.parse_args()
    
    builder = ExeBuilder(
        debug=args.debug,
        clean=not args.no_clean,
        compress=not args.no_compress
    )
    
    success = builder.run()
    
    if success:
        print("\nBuild completed successfully!")
        print(f"Output directory: {builder.dist_dir}")
    else:
        print("\nBuild failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()