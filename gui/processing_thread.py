# Path: gui/processing_thread.py
import logging
from collections import defaultdict
from PyQt5.QtCore import QThread, pyqtSignal


class ProcessingThread(QThread):
    processing_finished = pyqtSignal(dict)  # Change processing_finished signal with dict argument
    file_processed = pyqtSignal(int)  # Add file_processed signal with int argument
    error_occurred = pyqtSignal(str)  # Add error_occurred signal with str argument

    def __init__(self, folders, app_config, process_folders, preview_mode=False, callback=None):
        super().__init__()
        self.folders = folders
        self.app_config = app_config
        self.process_folders = process_folders
        self.preview_mode = preview_mode
        self.callback = callback

    def run(self):
        summary = defaultdict(int)
        try:
            for i, folder in enumerate(self.folders):
                folder_summary = self.process_folders(folder, self.app_config, self.preview_mode)
                for key, value in folder_summary.items():
                    summary[key] += value
                progress = int((i + 1) / len(self.folders) * 100)
                self.file_processed.emit(progress)
        except Exception as e:
            logging.error(f"Error in ProcessingThread.run: {e}")
            self.error_occurred.emit(str(e))  # Emit the error_occurred signal with the error message
        finally:
            self.processing_finished.emit(summary)
