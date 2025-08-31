#!/usr/bin/env python3
"""
Standalone launcher for the Video Transfer Tool
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from video_transfer import VideoTransferWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Video Transfer Tool")
    app.setStyle("Fusion")
    
    # Create and show the window
    window = VideoTransferWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())