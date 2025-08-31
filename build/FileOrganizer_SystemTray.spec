# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.parent.absolute()
src_path = project_root / 'src'

# Add src directory to Python path
sys.path.insert(0, str(src_path))

block_cipher = None

a = Analysis(
    [str(src_path / 'system_tray' / 'system_tray_main.py')],
    pathex=[str(project_root), str(src_path)],
    binaries=[],
    datas=[
        (str(src_path / 'gui'), 'gui'),
        (str(src_path / 'file_handler'), 'file_handler'),
        (str(src_path / 'event'), 'event'),
        (str(src_path / 'transfers'), 'transfers'),
        (str(src_path / 'system_tray'), 'system_tray'),
        (str(project_root / 'config'), 'config'),
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'PyQt5.QtNetwork',
        'mutagen',
        'mutagen.mp3',
        'mutagen.flac', 
        'mutagen.mp4',
        'mutagen.oggvorbis',
        'mutagen.id3',
        'PIL',
        'PIL.Image',
        'PIL.ExifTags',
        'subprocess',
        'shutil',
        'json',
        'logging',
        'concurrent.futures',
        'threading',
        'hashlib',
        'os',
        'sys',
        'pathlib',
        'datetime',
        'tempfile',
        'winshell',
        'winreg',
        'src.system_tray.system_tray_main',
        'src.system_tray.system_tray_manager', 
        'src.core.main',
        'src.gui.main_window',
        'src.transfers.audio_transfer',
        'src.transfers.video_transfer',
        'src.transfers.downloads_organizer',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy', 
        'pandas',
        'scipy',
        'jupyter',
        'IPython',
        'notebook',
        'tk',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FileOrganizer_SystemTray',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # System tray should not show console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add system tray icon path
)

# Create app bundle for macOS
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='FileOrganizer_SystemTray.app',
        icon=None,  # Add icon path for macOS
        bundle_identifier='com.fileorganizer.systemtray',
    )