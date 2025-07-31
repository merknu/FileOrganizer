#!/usr/bin/env python3
"""
Standalone launcher for the Photo Transfer Tool
Can be run directly without launching the full FileOrganizer suite
"""

import sys
from PyQt5.QtWidgets import QApplication
from gui.photo_transfer_window import PhotoTransferWindow

def main():
    """Main entry point for photo transfer tool"""
    app = QApplication(sys.argv)
    app.setApplicationName("Photo Transfer Tool")
    
    # Create and show the window
    window = PhotoTransferWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()