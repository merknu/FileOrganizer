# Path: main.py
import sys
import time
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, QMenuBar
from watchdog.observers import Observer
from config.config_handler import ConfigHandler
from event.file_organizer_event import FileOrganizerEventHandler
from gui.main_window import FileOrganizerMainWindow
from gui.photo_transfer_window import PhotoTransferWindow

logging.basicConfig(filename='file_organizer.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s')


CONFIG_FILE = 'config/config.json'
config_handler = ConfigHandler(CONFIG_FILE)
global_app_config = config_handler.config


def process_folders(folders, app_config, preview_mode=False):
    observers = []
    for folder in folders:
        event_handler = FileOrganizerEventHandler(folder, app_config, preview_mode=preview_mode)
        observer = Observer()
        observer.schedule(event_handler, folder, recursive=False)
        observer.start()
        observers.append(observer)
        if preview_mode and hasattr(main_window, 'preview_text_edit'):
            main_window.preview_text_edit.append(f"Organized folder: {folder}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
    for observer in observers:
        observer.join()


class MainApplication(QMainWindow):
    """Main application window with menu to choose tools"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileOrganizer Suite")
        self.setGeometry(100, 100, 800, 600)
        
        # Create menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Add actions
        organizer_action = QAction("File Organizer", self)
        organizer_action.triggered.connect(self.open_file_organizer)
        file_menu.addAction(organizer_action)
        
        transfer_action = QAction("Photo Transfer Tool", self)
        transfer_action.triggered.connect(self.open_photo_transfer)
        file_menu.addAction(transfer_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Show initial window
        self.file_organizer = FileOrganizerMainWindow(global_app_config, process_folders)
        self.setCentralWidget(self.file_organizer)
    
    def open_file_organizer(self):
        """Open the file organizer window"""
        self.file_organizer = FileOrganizerMainWindow(global_app_config, process_folders)
        self.setCentralWidget(self.file_organizer)
    
    def open_photo_transfer(self):
        """Open the photo transfer window"""
        self.photo_transfer = PhotoTransferWindow()
        self.setCentralWidget(self.photo_transfer)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--transfer":
        # Launch photo transfer directly
        window = PhotoTransferWindow()
    else:
        # Launch main application
        window = MainApplication()
    
    window.show()
    sys.exit(app.exec_())
