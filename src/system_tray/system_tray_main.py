#!/usr/bin/env python3
"""
FileOrganizer System Tray Entry Point
This is the main entry point for the system tray version of FileOrganizer
"""

import sys
import os
from pathlib import Path

# Add the project directory to Python path
project_root = Path(__file__).parent.parent.parent  # Go to project root from src/system_tray/
src_root = project_root / 'src'
sys.path.insert(0, str(src_root))
sys.path.insert(0, str(project_root))

# Import the system tray manager
from system_tray.system_tray_manager import main

if __name__ == "__main__":
    main()