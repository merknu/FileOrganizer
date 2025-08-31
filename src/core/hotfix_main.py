#!/usr/bin/env python3
"""
FileOrganizer - Quick Launch with Hotfixes
==========================================

This is a patched version that fixes the GUI launch issue
and provides a simplified interface for immediate use.
"""

import os
import sys
import logging
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging():
    """Setup basic logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def launch_simple_gui():
    """Launch a simplified GUI version"""
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
        from PyQt5.QtWidgets import QLabel, QPushButton, QFileDialog, QTextEdit, QMessageBox
        from PyQt5.QtCore import Qt, QThread, pyqtSignal
        
        class SimpleFileOrganizerGUI(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("FileOrganizer - Simple Mode")
                self.setGeometry(100, 100, 800, 600)
                
                # Central widget
                central_widget = QWidget()
                self.setCentralWidget(central_widget)
                layout = QVBoxLayout(central_widget)
                
                # Title
                title = QLabel("🗂️ FileOrganizer - Simple Mode")
                title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
                layout.addWidget(title)
                
                # Source folder selection
                self.source_label = QLabel("No folder selected")
                layout.addWidget(QLabel("Select folder to organize:"))
                layout.addWidget(self.source_label)
                
                source_btn = QPushButton("Browse Folder")
                source_btn.clicked.connect(self.select_folder)
                layout.addWidget(source_btn)
                
                # Action buttons
                btn_layout = QVBoxLayout()
                
                preview_btn = QPushButton("🔍 Preview Organization")
                preview_btn.clicked.connect(self.preview_organization)
                btn_layout.addWidget(preview_btn)
                
                organize_btn = QPushButton("🗂️ Organize Files")
                organize_btn.clicked.connect(self.organize_files)
                btn_layout.addWidget(organize_btn)
                
                photo_btn = QPushButton("📸 Launch Photo Transfer Tool")
                photo_btn.clicked.connect(self.launch_photo_transfer)
                btn_layout.addWidget(photo_btn)
                
                audio_btn = QPushButton("🎵 Launch Audio Transfer Tool")
                audio_btn.clicked.connect(self.launch_audio_transfer)
                btn_layout.addWidget(audio_btn)
                
                layout.addLayout(btn_layout)
                
                # Log area
                layout.addWidget(QLabel("Activity Log:"))
                self.log_area = QTextEdit()
                self.log_area.setMaximumHeight(200)
                layout.addWidget(self.log_area)
                
                # Status
                self.status_label = QLabel("Ready")
                layout.addWidget(self.status_label)
                
                self.selected_folder = None
                self.log("FileOrganizer started in simple mode")
                
            def log(self, message):
                """Add message to log area"""
                self.log_area.append(f"[{self.get_timestamp()}] {message}")
                
            def get_timestamp(self):
                """Get current timestamp"""
                from datetime import datetime
                return datetime.now().strftime("%H:%M:%S")
                
            def select_folder(self):
                """Select folder to organize"""
                folder = QFileDialog.getExistingDirectory(self, "Select Folder to Organize")
                if folder:
                    self.selected_folder = folder
                    self.source_label.setText(f"Selected: {folder}")
                    self.log(f"Selected folder: {folder}")
                    
            def preview_organization(self):
                """Preview file organization"""
                if not self.selected_folder:
                    QMessageBox.warning(self, "Warning", "Please select a folder first")
                    return
                    
                try:
                    self.status_label.setText("Previewing...")
                    self.log("Starting preview...")
                    
                    # Import and use file organization
                    from file_handler.file_utils import organize_files
                    from config.config_handler import ConfigHandler
                    
                    # Load config
                    config_path = Path("config/config.json")
                    if config_path.exists():
                        config = ConfigHandler(str(config_path)).config
                    else:
                        # Use default config
                        config = {
                            "file_categories": {
                                "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
                                "Audio": [".mp3", ".wav", ".flac", ".m4a"],
                                "Documents": [".pdf", ".doc", ".docx", ".txt"],
                                "Video": [".mp4", ".avi", ".mov", ".mkv"]
                            },
                            "default_duplicate_action": "k"
                        }
                    
                    # Preview organization
                    summary = organize_files(self.selected_folder, config, preview_mode=True)
                    
                    self.log(f"Preview completed: {summary}")
                    self.status_label.setText("Preview completed")
                    
                    QMessageBox.information(self, "Preview Results", 
                                          f"Preview completed!\n\nResults: {summary}")
                    
                except Exception as e:
                    error_msg = f"Preview failed: {str(e)}"
                    self.log(error_msg)
                    self.status_label.setText("Preview failed")
                    QMessageBox.critical(self, "Error", error_msg)
                    
            def organize_files(self):
                """Organize files"""
                if not self.selected_folder:
                    QMessageBox.warning(self, "Warning", "Please select a folder first")
                    return
                    
                # Confirm action
                reply = QMessageBox.question(self, "Confirm", 
                                           "This will move files in the selected folder. Continue?",
                                           QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return
                    
                try:
                    self.status_label.setText("Organizing files...")
                    self.log("Starting file organization...")
                    
                    # Import and use file organization
                    from file_handler.file_utils import organize_files
                    from config.config_handler import ConfigHandler
                    
                    # Load config
                    config_path = Path("config/config.json")
                    if config_path.exists():
                        config = ConfigHandler(str(config_path)).config
                    else:
                        # Use default config
                        config = {
                            "file_categories": {
                                "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
                                "Audio": [".mp3", ".wav", ".flac", ".m4a"],
                                "Documents": [".pdf", ".doc", ".docx", ".txt"],
                                "Video": [".mp4", ".avi", ".mov", ".mkv"]
                            },
                            "default_duplicate_action": "k"
                        }
                    
                    # Organize files
                    summary = organize_files(self.selected_folder, config, preview_mode=False)
                    
                    self.log(f"Organization completed: {summary}")
                    self.status_label.setText("Organization completed")
                    
                    QMessageBox.information(self, "Success", 
                                          f"Files organized successfully!\n\nResults: {summary}")
                    
                except Exception as e:
                    error_msg = f"Organization failed: {str(e)}"
                    self.log(error_msg)
                    self.status_label.setText("Organization failed")
                    QMessageBox.critical(self, "Error", error_msg)
                    
            def launch_photo_transfer(self):
                """Launch photo transfer tool"""
                try:
                    self.log("Launching photo transfer tool...")
                    import subprocess
                    subprocess.Popen([sys.executable, "photo_transfer.py"])
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to launch photo transfer: {e}")
                    
            def launch_audio_transfer(self):
                """Launch audio transfer tool"""
                try:
                    self.log("Launching audio transfer tool...")
                    import subprocess
                    subprocess.Popen([sys.executable, "audio_transfer.py"])
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to launch audio transfer: {e}")
        
        # Create and run application
        app = QApplication(sys.argv)
        window = SimpleFileOrganizerGUI()
        window.show()
        
        return app.exec_()
        
    except Exception as e:
        print(f"Failed to launch GUI: {e}")
        return False

def launch_photo_transfer():
    """Launch photo transfer tool directly"""
    try:
        print("📸 Launching Photo Transfer Tool...")
        import photo_transfer
        return True
    except Exception as e:
        print(f"Failed to launch photo transfer: {e}")
        return False

def launch_audio_transfer():
    """Launch audio transfer tool directly"""
    try:
        print("🎵 Launching Audio Transfer Tool...")
        import audio_transfer
        return True
    except Exception as e:
        print(f"Failed to launch audio transfer: {e}")
        return False

def main():
    """Main entry point with multiple fallback options"""
    print("🗂️ FileOrganizer - Quick Launch")
    print("=" * 40)
    
    setup_logging()
    
    # Check if PyQt5 is available for GUI
    try:
        import PyQt5
        print("✅ PyQt5 available - launching GUI...")
        success = launch_simple_gui()
        if success:
            return 0
    except ImportError:
        print("⚠️ PyQt5 not available")
    
    # Fallback to photo transfer tool
    print("📸 Trying photo transfer tool...")
    if launch_photo_transfer():
        return 0
    
    # Fallback to audio transfer tool
    print("🎵 Trying audio transfer tool...")
    if launch_audio_transfer():
        return 0
    
    # Final fallback - command line instructions
    print("\n❌ GUI launch failed. Manual options:")
    print("\nTry these commands:")
    print("  python photo_transfer.py     # Photo transfer tool")
    print("  python audio_transfer.py     # Audio transfer tool")
    print("  python portable.py          # Portable mode")
    print("  python run.py               # Smart launcher")
    print("\nOr fix the installation:")
    print("  python -m pip install --upgrade PyQt5")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())