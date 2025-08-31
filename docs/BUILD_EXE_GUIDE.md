# Building FileOrganizer Executables

This comprehensive guide covers building standalone executables for FileOrganizer using the new repository structure and automated build system.

## 🎯 Quick Start

### One-Command Build
```bash
# Build both FileOrganizer and SystemTray executables
cd build/
python build_exe.py

# Build with specific options
python build_exe.py --debug --no-compress
```

### Using GitHub Actions (Automated)
1. Push a version tag: `git tag v3.1.0 && git push origin v3.1.0`
2. GitHub automatically builds for Windows, Linux, and macOS
3. Releases are created automatically with binaries

## 📁 New Repository Structure

The reorganized repository supports efficient building:

```
FileOrganizer/
├── src/                          # All source code
├── build/                        # Build scripts and spec files
│   ├── build_exe.py              # Main build script
│   ├── FileOrganizer.spec        # PyInstaller spec for main app
│   ├── FileOrganizer_SystemTray.spec # Spec for system tray
│   └── requirements-exe.txt      # Build-specific requirements
├── releases/latest/              # Built executables
└── .github/workflows/            # Automated builds
```

## 🛠️ Prerequisites

### Required Software
- Python 3.8+ 
- PyInstaller: `pip install pyinstaller`
- Project dependencies: `pip install -r build/requirements-exe.txt`

### Optional Optimization Tools
- **UPX** (50-70% size reduction): Download from [UPX Releases](https://github.com/upx/upx/releases)
- **Platform tools**: Windows SDK, Xcode Command Line Tools, Linux build-essentials

## 🚀 Build Methods

### Method 1: Automated Build Script (Recommended)

The enhanced build script handles the new structure automatically:

```bash
cd build/

# Standard production build
python build_exe.py

# Debug build with console output (for troubleshooting)
python build_exe.py --debug

# Build without cleaning previous outputs
python build_exe.py --no-clean

# Build without UPX compression (faster but larger)
python build_exe.py --no-compress

# Build with installer generation
python build_exe.py --installer
```

**Features of the Build Script:**
- ✅ Automatic path detection for new structure
- ✅ Optimized PyInstaller spec files
- ✅ Cross-platform compatibility
- ✅ UPX compression integration
- ✅ Version info generation
- ✅ Resource bundling
- ✅ Error handling and diagnostics

### Method 2: Using Spec Files

The optimized spec files work with the new structure:

```bash
cd build/

# Build main FileOrganizer application
pyinstaller FileOrganizer.spec

# Build System Tray version
pyinstaller FileOrganizer_SystemTray.spec
```

### Method 3: Manual PyInstaller

For custom builds:

```bash
# From project root
pyinstaller \
  --onefile \
  --windowed \
  --name="FileOrganizer" \
  --add-data="src/gui:gui" \
  --add-data="src/file_handler:file_handler" \
  --add-data="config:config" \
  --hidden-import="PyQt5.QtCore" \
  --hidden-import="src.core.main" \
  --icon="assets/icon.ico" \
  src/core/main.py
```

## 📋 Spec Files Configuration

### Enhanced FileOrganizer.spec

Optimized for the new structure:

```python
# Automatic path detection
project_root = Path(__file__).parent.parent.absolute()
src_path = project_root / 'src'

a = Analysis(
    [str(src_path / 'core' / 'main.py')],
    pathex=[str(project_root), str(src_path)],
    datas=[
        (str(src_path / 'gui'), 'gui'),
        (str(src_path / 'file_handler'), 'file_handler'),
        (str(src_path / 'transfers'), 'transfers'),
        (str(project_root / 'config'), 'config'),
    ],
    hiddenimports=[
        'src.core.main',
        'src.gui.main_window',
        'src.transfers.downloads_organizer',
        # ... other imports
    ],
)
```

### SystemTray Spec Features

Optimized for background operation:

```python
exe = EXE(
    # ...
    console=False,  # No console window
    name='FileOrganizer_SystemTray',
    # System tray optimizations
)
```

## ⚡ Build Optimization

### Size Optimization

1. **UPX Compression** (enabled by default):
   ```bash
   python build_exe.py  # Uses UPX automatically
   ```

2. **Module Exclusions**:
   ```python
   excludes=[
       'matplotlib', 'numpy', 'pandas', 'jupyter',
       'tk', 'tkinter',  # GUI frameworks not used
   ]
   ```

3. **Smart Resource Bundling**:
   - Only includes necessary files from `src/`
   - Excludes test files and development tools
   - Optimized data file inclusion

### Performance Optimization

- **One-file builds** for easy distribution
- **Optimized import paths** for faster startup
- **Resource caching** during build
- **Platform-specific optimizations**

## 🖥️ Platform-Specific Builds

### Windows
```bash
python build_exe.py
# Creates: releases/latest/FileOrganizer.exe (~20-35 MB)
#         releases/latest/FileOrganizer_SystemTray.exe (~18-30 MB)
```

**Features:**
- Windows version info embedded
- Icon integration
- No console window for SystemTray
- UPX compression applied

### macOS
```bash
python build_exe.py
# Creates: releases/latest/FileOrganizer.app
#         releases/latest/FileOrganizer_SystemTray.app
```

**Features:**
- App bundle creation
- Bundle identifier: `com.fileorganizer.app`
- Retina icon support
- Code signing ready

### Linux
```bash
python build_exe.py
# Creates: releases/latest/FileOrganizer
#         releases/latest/FileOrganizer_SystemTray
```

**Features:**
- Standalone binaries
- No system dependencies
- Works across distributions

## 🔧 Troubleshooting

### Common Issues

1. **Import Errors**:
   ```
   ModuleNotFoundError: No module named 'src.transfers.downloads_organizer'
   ```
   **Solution**: Ensure all src modules are in `hiddenimports`

2. **Path Issues**:
   ```
   FileNotFoundError: config.json not found
   ```
   **Solution**: Check `datas` paths in spec file

3. **PyQt5 Platform Errors**:
   ```
   qt.qpa.plugin: Could not load platform plugin
   ```
   **Solution**: Ensure all PyQt5 modules included

### Debug Mode

```bash
# Enable detailed logging
python build_exe.py --debug

# Manual debug build
pyinstaller --debug=all --console build/FileOrganizer.spec
```

### Build Testing

Test matrix for releases:
- ✅ Clean Windows 10/11 systems
- ✅ Various Linux distributions
- ✅ macOS versions 10.14+
- ✅ Systems without Python installed
- ✅ Virtual machines

## 🤖 Automated Building (GitHub Actions)

### Workflow Features

The `.github/workflows/build-release.yml` provides:

- **Multi-platform builds**: Windows, Linux, macOS simultaneously
- **Automatic releases**: On version tags (`v1.0.0`)
- **Artifact management**: Organized release assets
- **Quality checks**: Build validation and testing
- **Release notes**: Auto-generated from commits

### Triggering Builds

```bash
# Create and push version tag
git tag v3.1.0
git push origin v3.1.0

# Or trigger manually via GitHub web interface
```

### Build Matrix

| Platform | Executable | Size (approx) | Features |
|----------|------------|---------------|----------|
| Windows | `FileOrganizer.exe` | 25MB | Full GUI, all features |
| Windows | `FileOrganizer_SystemTray.exe` | 22MB | System tray, scenarios |
| Linux | `FileOrganizer-linux` | 30MB | GTK support, all features |
| Linux | `FileOrganizer_SystemTray-linux` | 28MB | Background operation |
| macOS | `FileOrganizer.app` | 35MB | Native app bundle |
| macOS | `FileOrganizer_SystemTray.app` | 32MB | Menu bar integration |

## 📦 Distribution

### Release Structure

```
releases/latest/
├── FileOrganizer.exe              # Windows main app
├── FileOrganizer_SystemTray.exe   # Windows system tray
├── FileOrganizer-linux            # Linux binary
├── FileOrganizer_SystemTray-linux # Linux system tray
├── FileOrganizer.app/             # macOS app bundle
├── FileOrganizer_SystemTray.app/  # macOS system tray
└── README.md                      # Release notes
```

### Installation Instructions

**Windows:**
1. Download appropriate EXE from releases
2. Run directly - no installation needed
3. For system tray: Run `FileOrganizer_SystemTray.exe`

**Linux:**
1. Download binary: `wget https://github.com/user/repo/releases/latest/download/FileOrganizer-linux`
2. Make executable: `chmod +x FileOrganizer-linux`
3. Run: `./FileOrganizer-linux`

**macOS:**
1. Download app bundle
2. Move to Applications folder
3. Run from Applications or Launchpad

## 🎯 Advanced Topics

### Custom Build Configurations

Create custom spec files for specialized builds:

```python
# build/FileOrganizer_Minimal.spec
# Minimal build without GPU acceleration
excludes=[
    'opencl', 'pyopencl', 'gpu_acceleration'
]
```

### Development Builds

```bash
# Quick development build (no optimization)
python build_exe.py --debug --no-compress --no-clean
```

### Continuous Integration

The build system integrates with:
- **GitHub Actions** (primary)
- **Travis CI** (optional)
- **AppVeyor** (Windows-specific)
- **GitLab CI** (self-hosted)

## 📚 Resources

- [New Build System Documentation](BUILD_EXE_GUIDE.md)
- [System Tray Scenarios Guide](SYSTEM_TRAY_SCENARIOS.md)
- [PyInstaller Documentation](https://pyinstaller.readthedocs.io/)
- [GitHub Actions Guide](https://docs.github.com/en/actions)
- [UPX Compression](https://upx.github.io/)

## 🎉 Success Indicators

A successful build should produce:

- ✅ **Executables** in `releases/latest/`
- ✅ **Size** under 35MB per executable
- ✅ **Startup time** under 3 seconds
- ✅ **All features working** without Python installed
- ✅ **Cross-platform compatibility**
- ✅ **No missing dependencies** errors