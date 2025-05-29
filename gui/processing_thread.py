# Path: gui/processing_thread.py
# Enhanced processing thread with better error handling and progress tracking
import logging
import time
from collections import defaultdict
from typing import List, Dict, Any, Optional, Callable
from PyQt5.QtCore import QThread, pyqtSignal, QMutex

from file_handler.file_utils import organize_files


class ProcessingThread(QThread):
    """Enhanced processing thread for file organization."""
    
    # Signals
    processing_finished = pyqtSignal(dict)  # Emits summary dictionary
    progress_changed = pyqtSignal(int)      # Emits progress percentage (0-100)
    status_changed = pyqtSignal(str)        # Emits status message
    error_occurred = pyqtSignal(str)        # Emits error message
    file_processed = pyqtSignal(str)        # Emits filename of processed file
    
    def __init__(self, folders: List[str], app_config: Dict[str, Any], 
                 recursive: bool = True, preview_mode: bool = False, 
                 callback: Optional[Callable] = None):
        """
        Initialize the processing thread.
        
        Args:
            folders: List of folder paths to process
            app_config: Application configuration dictionary
            recursive: Whether to process subdirectories
            preview_mode: If True, only preview changes without moving files
            callback: Optional callback function for progress updates
        """
        super().__init__()
        
        self.folders = folders
        self.app_config = app_config
        self.recursive = recursive
        self.preview_mode = preview_mode
        self.callback = callback
        
        # Thread control
        self._stop_requested = False
        self._mutex = QMutex()
        
        # Progress tracking
        self.total_files = 0
        self.processed_files = 0
        self.current_folder = ""
        
        # Results
        self.summary = defaultdict(int)
        
        # Logging
        self.logger = logging.getLogger(__name__)
    
    def stop(self):
        """Request the thread to stop processing."""
        with QMutex():
            self._stop_requested = True
        self.logger.info("Stop requested for processing thread")
    
    def is_stop_requested(self) -> bool:
        """Check if stop has been requested."""
        return self._stop_requested
    
    def count_files_in_folders(self) -> int:
        """Count total files to be processed for progress tracking."""
        total = 0
        for folder in self.folders:
            if self.is_stop_requested():
                break
            try:
                total += self._count_files_in_folder(folder)
            except Exception as e:
                self.logger.warning(f"Could not count files in {folder}: {e}")
        return total
    
    def _count_files_in_folder(self, folder: str) -> int:
        """Count files in a single folder."""
        import os
        count = 0
        try:
            if self.recursive:
                for root, dirs, files in os.walk(folder):
                    if self.is_stop_requested():
                        break
                    count += len(files)
            else:
                items = os.listdir(folder)
                for item in items:
                    if os.path.isfile(os.path.join(folder, item)):
                        count += 1
        except Exception as e:
            self.logger.error(f"Error counting files in {folder}: {e}")
        return count
    
    def update_progress(self):
        """Update progress and emit signals."""
        if self.total_files > 0:
            progress = min(100, int((self.processed_files / self.total_files) * 100))
            self.progress_changed.emit(progress)
        
        if self.callback:
            try:
                self.callback()
            except Exception as e:
                self.logger.warning(f"Error in callback: {e}")
    
    def process_single_folder(self, folder: str) -> Dict[str, int]:
        """
        Process a single folder and return summary.
        
        Args:
            folder: Path to folder to process
            
        Returns:
            Dictionary with processing summary
        """
        self.status_changed.emit(f"Processing folder: {folder}")
        self.current_folder = folder
        
        try:
            # Create a custom callback for this folder
            def folder_callback():
                self.processed_files += 1
                self.file_processed.emit(f"Processed file {self.processed_files}/{self.total_files}")
                self.update_progress()
                
                # Check for stop request
                if self.is_stop_requested():
                    raise InterruptedError("Processing stopped by user")
            
            # Call the organize_files function with correct signature
            folder_summary = organize_files(
                folder=folder,
                app_config=self.app_config,
                recursive=self.recursive,
                preview_mode=self.preview_mode,
                callback=folder_callback
            )
            
            self.logger.info(f"Processed folder {folder}: {folder_summary}")
            return folder_summary
            
        except InterruptedError:
            self.logger.info(f"Processing of folder {folder} was interrupted")
            raise
        except Exception as e:
            self.logger.error(f"Error processing folder {folder}: {e}")
            return {"error": 1, "error_message": str(e)}
    
    def run(self):
        """Main thread execution method."""
        self.logger.info(f"Starting processing thread for {len(self.folders)} folders")
        self.status_changed.emit("Initializing...")
        
        try:
            # Reset counters
            self.processed_files = 0
            self.summary = defaultdict(int)
            
            # Count total files for progress tracking
            self.status_changed.emit("Counting files...")
            self.total_files = self.count_files_in_folders()
            self.logger.info(f"Total files to process: {self.total_files}")
            
            if self.is_stop_requested():
                self.status_changed.emit("Processing cancelled")
                return
            
            # Process each folder
            for i, folder in enumerate(self.folders):
                if self.is_stop_requested():
                    self.logger.info("Processing stopped by user request")
                    self.status_changed.emit("Processing stopped")
                    break
                
                self.logger.info(f"Processing folder {i+1}/{len(self.folders)}: {folder}")
                
                try:
                    folder_summary = self.process_single_folder(folder)
                    
                    # Accumulate summary
                    for key, value in folder_summary.items():
                        self.summary[key] += value
                    
                    # Brief pause to allow UI updates
                    self.msleep(10)
                    
                except InterruptedError:
                    self.logger.info("Processing interrupted")
                    break
                except Exception as e:
                    self.logger.error(f"Failed to process folder {folder}: {e}")
                    self.summary["failed_folders"] += 1
                    self.summary["errors"] += 1
                    
                    # Continue with next folder instead of stopping
                    continue
            
            # Final status update
            if not self.is_stop_requested():
                if self.preview_mode:
                    self.status_changed.emit("Preview completed")
                else:
                    self.status_changed.emit("Processing completed")
                
                self.logger.info(f"Processing completed. Summary: {dict(self.summary)}")
            
        except Exception as e:
            self.logger.error(f"Unexpected error in processing thread: {e}")
            self.error_occurred.emit(f"Unexpected error: {str(e)}")
            
        finally:
            # Always emit the finished signal with summary
            self.processing_finished.emit(dict(self.summary))
            self.logger.info("Processing thread finished")
    
    def get_progress_info(self) -> Dict[str, Any]:
        """Get current progress information."""
        return {
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "current_folder": self.current_folder,
            "folders_total": len(self.folders),
            "preview_mode": self.preview_mode
        }


class BatchProcessingThread(ProcessingThread):
    """Extended processing thread for batch operations."""
    
    batch_progress = pyqtSignal(int, int)  # current_batch, total_batches
    
    def __init__(self, folder_batches: List[List[str]], app_config: Dict[str, Any],
                 recursive: bool = True, preview_mode: bool = False,
                 callback: Optional[Callable] = None):
        """
        Initialize batch processing thread.
        
        Args:
            folder_batches: List of folder batches to process
            app_config: Application configuration
            recursive: Process subdirectories
            preview_mode: Preview only mode
            callback: Progress callback
        """
        # Flatten the batches for the parent class
        all_folders = [folder for batch in folder_batches for folder in batch]
        super().__init__(all_folders, app_config, recursive, preview_mode, callback)
        
        self.folder_batches = folder_batches
        self.current_batch = 0
    
    def run(self):
        """Run batch processing."""
        self.logger.info(f"Starting batch processing: {len(self.folder_batches)} batches")
        
        try:
            for batch_idx, folder_batch in enumerate(self.folder_batches):
                if self.is_stop_requested():
                    break
                
                self.current_batch = batch_idx + 1
                self.batch_progress.emit(self.current_batch, len(self.folder_batches))
                
                # Process this batch
                self.folders = folder_batch
                super().run()
                
                # Brief pause between batches
                self.msleep(100)
            
        except Exception as e:
            self.logger.error(f"Error in batch processing: {e}")
            self.error_occurred.emit(f"Batch processing error: {str(e)}")
        
        finally:
            self.processing_finished.emit(dict(self.summary))


# Utility functions for thread management
def create_processing_thread(folders: List[str], config: Dict[str, Any], 
                           **kwargs) -> ProcessingThread:
    """Factory function to create a processing thread."""
    return ProcessingThread(folders, config, **kwargs)


def estimate_processing_time(folders: List[str], recursive: bool = True) -> int:
    """
    Estimate processing time in seconds.
    
    Args:
        folders: List of folders to process
        recursive: Whether processing is recursive
        
    Returns:
        Estimated time in seconds
    """
    import os
    
    total_files = 0
    for folder in folders:
        try:
            if recursive:
                for root, dirs, files in os.walk(folder):
                    total_files += len(files)
            else:
                items = os.listdir(folder)
                total_files += sum(1 for item in items 
                                 if os.path.isfile(os.path.join(folder, item)))
        except Exception:
            # Assume average if we can't count
            total_files += 100
    
    # Rough estimate: 50 files per second
    return max(1, total_files // 50)
