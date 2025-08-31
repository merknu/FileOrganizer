#!/usr/bin/env python3
"""
Standalone launcher for the Audio Transfer Tool
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from audio_transfer import main

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Audio Transfer Tool")
    app.setStyle("Fusion")
    
    # Launch the audio transfer tool
    main()