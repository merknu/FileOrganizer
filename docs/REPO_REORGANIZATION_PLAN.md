# Repository Reorganization Plan

## Current Structure Issues
- All files are scattered in the root directory
- No clear separation between source code and build/release files
- Missing proper release structure for EXE distribution

## Proposed New Structure

```
FileOrganizer/
├── src/                          # Main source code
│   ├── core/                     # Core FileOrganizer functionality
│   │   ├── main.py
│   │   ├── install.py
│   │   ├── portable.py
│   │   └── hotfix_main.py
│   ├── gui/                      # GUI components
│   │   └── (existing gui files)
│   ├── file_handler/             # File handling logic
│   │   └── (existing file_handler files)
│   ├── event/                    # Event system
│   │   └── (existing event files)
│   ├── transfers/                # Transfer modules (NEW)
│   │   ├── audio_transfer.py
│   │   ├── video_transfer.py
│   │   ├── downloads_organizer.py
│   │   ├── launch_audio_transfer.py
│   │   └── launch_video_transfer.py
│   ├── system_tray/              # System tray functionality (NEW)
│   │   ├── system_tray_main.py
│   │   └── system_tray_manager.py
│   └── utils/                    # Utility functions
│       └── (utility files)
├── build/                        # Build and compilation files (NEW)
│   ├── build_exe.py
│   ├── build_system_tray.py
│   ├── requirements-exe.txt
│   ├── FileOrganizer.spec
│   └── FileOrganizer_SystemTray.spec
├── scripts/                      # Launcher scripts (NEW)
│   ├── windows/
│   │   ├── START_HERE.bat
│   │   ├── LAUNCH_NOW.bat
│   │   ├── WORKING_LAUNCHER.bat
│   │   ├── LAUNCH_AUDIO_TRANSFER.bat
│   │   ├── LAUNCH_VIDEO_TRANSFER.bat
│   │   ├── MEDIA_TRANSFER_HUB.bat
│   │   └── TEST_DOWNLOADS_ORGANIZER.bat
│   └── unix/
│       ├── start_here.sh
│       └── media_transfer_hub.sh
├── releases/                     # Release files (NEW)
│   ├── v1.0.0/
│   │   ├── FileOrganizer.exe
│   │   ├── FileOrganizer_SystemTray.exe
│   │   └── README.md
│   └── latest/
│       ├── FileOrganizer.exe
│       ├── FileOrganizer_SystemTray.exe
│       └── README.md
├── tests/                        # Test files
│   ├── (existing test structure)
│   ├── test_downloads_organizer.py
│   └── test_enhanced_gui.py
├── docs/                         # Documentation (NEW)
│   ├── BUILD_EXE_GUIDE.md
│   ├── REFACTORING_PLAN_FOR_EXE.md
│   ├── SYSTEM_TRAY_SCENARIOS.md
│   └── OPENCL_HASHING.md
├── config/                       # Configuration files
│   └── (existing config files)
├── benchmarks/                   # Benchmark files
│   └── (existing benchmark files)
├── .github/                      # GitHub Actions (NEW)
│   └── workflows/
│       └── build-release.yml
├── README.md                     # Main README
├── LICENSE
└── requirements.txt
```

## Implementation Steps

1. Create new directory structure
2. Move files to appropriate locations
3. Update import statements
4. Create GitHub Actions for automated builds
5. Update documentation
6. Test the reorganized structure

## Benefits

- Clear separation of concerns
- Easy to find and maintain files
- Automated EXE builds via GitHub Actions
- Professional repository structure
- Easy for contributors to understand