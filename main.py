# Path: main.py
import sys
import time
import logging
from PyQt5.QtWidgets import QApplication
from watchdog.observers import Observer
from config.config_handler import ConfigHandler
from event.file_organizer_event import FileOrganizerEventHandler
from gui.main_window import FileOrganizerMainWindow

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = FileOrganizerMainWindow(global_app_config, process_folders)
    main_window.show()
    sys.exit(app.exec_())
