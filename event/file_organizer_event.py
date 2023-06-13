# Path: event/file_organizer_event.py
from watchdog.events import FileSystemEventHandler
import concurrent.futures
import logging
from file_handler.file_utils import organize_files


class FileOrganizerEventHandler(FileSystemEventHandler):
    def __init__(self, folder_to_process, app_config, preview_mode=False, callback=None):  # Add callback=None
        self._folder_to_process = folder_to_process
        self._app_config = app_config
        self.preview_mode = preview_mode
        self.callback = callback

    def on_modified(self, event):
        if event.is_directory:
            return
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(organize_files, self._folder_to_process, self._app_config, recursive=True,
                                         preview_mode=self.preview_mode,
                                         callback=self.callback)  # Pass callback to organize_files
                summary = future.result()  # Capture the result
                if summary:
                    logging.error(f"Error(s) occurred during processing: {summary}")
        except Exception as e:
            logging.error(f"Error organizing files: {e}")
