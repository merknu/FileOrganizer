# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for FileOrganizer System Tray Version
This spec file is optimized for system tray operation with scenario support
"""

import sys
import os
from pathlib import Path

# Get the absolute path to the project root
project_root = Path(os.path.abspath(SPECPATH))

block_cipher = None

a = Analysis(
    ['system_tray_main.py'],  # System tray entry point
    pathex=[str(project_root)],
    binaries=[
        # Add any binary dependencies here
        # Example: ('ffmpeg.exe', '.') for Windows ffmpeg
    ],
    datas=[
        # Include all GUI files
        ('gui/*.py', 'gui'),
        ('gui/*.ui', 'gui'),  # If you have UI files
        
        # Include file handler modules
        ('file_handler/*.py', 'file_handler'),
        
        # Include event modules  
        ('event/*.py', 'event'),
        
        # Include config files
        ('config/*.json', 'config'),
        ('config/*.yaml', 'config'),
        
        # Include scenario system
        ('system_tray_manager.py', '.'),
        
        # Include transfer tools
        ('audio_transfer.py', '.'),
        ('video_transfer.py', '.'), 
        ('photo_transfer.py', '.'),
        
        # Include resources
        # ('resources/icons/*.png', 'resources/icons'),
        # ('resources/icons/*.ico', 'resources/icons'),
        # ('resources/scenarios/*.json', 'resources/scenarios'),
    ],
    hiddenimports=[
        # PyQt5 modules for GUI and system tray
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        
        # Audio/Video processing for scenarios
        'mutagen',
        'mutagen.mp3',
        'mutagen.mp4', 
        'mutagen.flac',
        'mutagen.oggvorbis',
        
        # Image processing for photo scenarios
        'PIL',
        'PIL.Image',
        'PIL.ExifTags',
        'PIL.ImageDraw',
        
        # File watching and monitoring
        'watchdog',
        'watchdog.observers',
        'watchdog.events',
        
        # System tray and threading
        'threading',
        'queue',
        'subprocess',
        
        # JSON handling for scenarios
        'json',
        'pathlib',
        
        # Standard library modules
        'shutil',
        'hashlib',
        'logging',
        'datetime',
        'collections',
        'itertools',
        'functools',
        
        # FileOrganizer modules
        'file_handler.file_utils',
        'gui.main_window',
        'gui.photo_transfer_window',
        'gui.processing_thread',
        'event.file_organizer_event',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'scipy',
        'pandas',
        'numpy.testing',
        'tkinter',  # Use PyQt5 only
        'test',
        'tests',
        'unittest',
        'doctest',
        'pydoc',
        'xml.etree.ElementTree',
        'email',
        'http',
        'urllib3',
        'requests',  # Exclude unless needed for cloud features
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out unnecessary binaries to reduce size
excluded_binaries = [
    'opengl32sw.dll',  # Software OpenGL
    'Qt5Pdf.dll',
    'Qt5Quick.dll', 
    'Qt5Qml.dll',
    'Qt5QmlModels.dll',
    'Qt5VirtualKeyboard.dll',
    'Qt5WebEngine.dll',
    'Qt5WebEngineCore.dll',
    'd3dcompiler_47.dll',
    'libGLESv2.dll',  # Not needed for system tray
    'libEGL.dll',
]

a.binaries = [binary for binary in a.binaries if binary[0] not in excluded_binaries]

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# Create single-file executable optimized for system tray
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FileOrganizer',
    debug=False,  # Set to True for debugging
    bootloader_ignore_signals=False,
    strip=False,  # Keep symbols for better error reporting
    upx=True,  # Enable compression
    upx_exclude=[
        'vcruntime140.dll',
        'python3.dll',
        'python38.dll',
        'python39.dll', 
        'python310.dll',
        'python311.dll',
        'python312.dll',
        'Qt5Core.dll',  # Don't compress Qt core
        'Qt5Gui.dll',
        'Qt5Widgets.dll',
    ],
    runtime_tmpdir=None,
    console=False,  # No console window for tray app
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon='resources/tray_icon.ico' if os.path.exists('resources/tray_icon.ico') else None,
)

# Optional: Create installer-friendly directory version
# Uncomment below and comment out single-file exe above for directory distribution

# exe = EXE(
#     pyz,
#     a.scripts,
#     [],
#     exclude_binaries=True,
#     name='FileOrganizer',
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=True,
#     console=False,
#     disable_windowed_traceback=False,
#     target_arch=None,
#     codesign_identity=None,
#     entitlements_file=None,
#     icon='resources/tray_icon.ico',
# )

# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles, 
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='FileOrganizer_SystemTray',
# )