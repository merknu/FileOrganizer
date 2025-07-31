"""
Photo Transfer Window - Advanced GUI for selective file transfers
Supports date range selection, error handling, and resume capability
"""

import sys
import os
import json
import hashlib
import shutil
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QFileDialog, QProgressBar, QTextEdit, QDateEdit,
                             QCheckBox, QTableWidget, QTableWidgetItem,
                             QMessageBox, QGroupBox, QComboBox, QSpinBox,
                             QAbstractItemView, QHeaderView)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QDate
from PyQt5.QtGui import QFont, QIcon

class TransferProgress:
    """Tracks transfer progress and maintains todo list"""
    def __init__(self, progress_file="transfer_progress.json"):
        self.progress_file = progress_file
        self.data = self.load_progress()
    
    def load_progress(self) -> Dict:
        """Load progress from file"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "completed": [],
            "failed": [],
            "pending": [],
            "partial": [],
            "last_source": "",
            "last_destination": "",
            "total_files": 0,
            "total_size": 0,
            "transferred_size": 0
        }
    
    def save_progress(self):
        """Save progress to file"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving progress: {e}")
    
    def add_completed(self, file_path: str, size: int):
        """Add file to completed list"""
        self.data["completed"].append({
            "path": file_path,
            "size": size,
            "timestamp": datetime.now().isoformat()
        })
        self.data["transferred_size"] += size
        self.save_progress()
    
    def add_failed(self, file_path: str, error: str):
        """Add file to failed list"""
        self.data["failed"].append({
            "path": file_path,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        self.save_progress()
    
    def add_partial(self, file_path: str, transferred: int, total: int):
        """Add partially transferred file"""
        self.data["partial"].append({
            "path": file_path,
            "transferred": transferred,
            "total": total,
            "timestamp": datetime.now().isoformat()
        })
        self.save_progress()
    
    def clear_progress(self):
        """Clear all progress data"""
        self.data = {
            "completed": [],
            "failed": [],
            "pending": [],
            "partial": [],
            "last_source": "",
            "last_destination": "",
            "total_files": 0,
            "total_size": 0,
            "transferred_size": 0
        }
        self.save_progress()


class TransferWorker(QThread):
    """Worker thread for file transfers"""
    progress_update = pyqtSignal(int)
    status_update = pyqtSignal(str)
    file_completed = pyqtSignal(str, int)
    file_failed = pyqtSignal(str, str)
    transfer_complete = pyqtSignal()
    
    def __init__(self, files: List[Dict], destination: str, progress_tracker: TransferProgress):
        super().__init__()
        self.files = files
        self.destination = destination
        self.progress_tracker = progress_tracker
        self.is_running = True
        self.current_file = None
        self.retry_count = 3  # Number of retries for failed transfers
        
    def run(self):
        """Main transfer loop"""
        total_files = len(self.files)
        
        for index, file_info in enumerate(self.files):
            if not self.is_running:
                break
                
            source_path = file_info['path']
            self.current_file = source_path
            
            # Calculate destination path preserving folder structure
            relative_path = os.path.basename(source_path)
            dest_path = os.path.join(self.destination, relative_path)
            
            # Skip if already completed
            completed_files = [f['path'] for f in self.progress_tracker.data['completed']]
            if source_path in completed_files:
                self.status_update.emit(f"Skipping already transferred: {relative_path}")
                continue
            
            # Retry logic
            retry_count = 0
            max_retries = self.retry_count
            
            while retry_count <= max_retries:
                try:
                    self.status_update.emit(f"Transferring ({index+1}/{total_files}): {relative_path}")
                    
                    # Check if file exists and needs verification
                    if os.path.exists(dest_path):
                        if self.verify_file_integrity(source_path, dest_path):
                            self.status_update.emit(f"File already exists and verified: {relative_path}")
                            self.file_completed.emit(source_path, file_info['size'])
                            self.progress_tracker.add_completed(source_path, file_info['size'])
                            break
                        else:
                            self.status_update.emit(f"Existing file corrupted, re-transferring: {relative_path}")
                            os.remove(dest_path)
                    
                    # Create destination directory if needed
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    # Copy file with progress tracking
                    self.copy_with_progress(source_path, dest_path, file_info['size'])
                    
                    # Verify transfer
                    if self.verify_file_integrity(source_path, dest_path):
                        self.file_completed.emit(source_path, file_info['size'])
                        self.progress_tracker.add_completed(source_path, file_info['size'])
                        break
                    else:
                        raise Exception("File verification failed")
                        
                except Exception as e:
                    retry_count += 1
                    error_msg = str(e)
                    
                    if retry_count <= max_retries:
                        self.status_update.emit(f"Error transferring {relative_path}: {error_msg}. Retry {retry_count}/{max_retries}")
                        # Clean up partial file
                        if os.path.exists(dest_path):
                            try:
                                os.remove(dest_path)
                            except:
                                pass
                    else:
                        self.status_update.emit(f"Failed after {max_retries} retries: {relative_path}")
                        self.file_failed.emit(source_path, error_msg)
                        self.progress_tracker.add_failed(source_path, error_msg)
                        break
            
            # Update progress
            progress = int((index + 1) / total_files * 100)
            self.progress_update.emit(progress)
        
        self.transfer_complete.emit()
    
    def copy_with_progress(self, source: str, destination: str, total_size: int):
        """Copy file with progress tracking"""
        chunk_size = 1024 * 1024  # 1MB chunks
        
        with open(source, 'rb') as src, open(destination, 'wb') as dst:
            bytes_copied = 0
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                dst.write(chunk)
                bytes_copied += len(chunk)
                
                # Save partial progress periodically
                if bytes_copied % (10 * chunk_size) == 0:  # Every 10MB
                    self.progress_tracker.add_partial(source, bytes_copied, total_size)
    
    def verify_file_integrity(self, source: str, destination: str) -> bool:
        """Verify file integrity by comparing sizes and checksums"""
        try:
            # First check sizes
            source_size = os.path.getsize(source)
            dest_size = os.path.getsize(destination)
            
            if source_size != dest_size:
                return False
            
            # For large files, just compare sizes to save time
            if source_size > 100 * 1024 * 1024:  # 100MB
                return True
            
            # For smaller files, compare checksums
            return self.calculate_checksum(source) == self.calculate_checksum(destination)
            
        except Exception:
            return False
    
    def calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def stop(self):
        """Stop the transfer"""
        self.is_running = False


class PhotoTransferWindow(QMainWindow):
    """Main window for photo transfer application"""
    
    def __init__(self):
        super().__init__()
        self.progress_tracker = TransferProgress()
        self.transfer_worker = None
        self.selected_files = []
        self.init_ui()
        self.load_last_session()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Advanced Photo Transfer Tool")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Source selection
        source_group = QGroupBox("Source Location")
        source_layout = QHBoxLayout()
        
        self.source_path = QLineEdit()
        self.source_path.setPlaceholderText("Select source folder (e.g., phone camera folder)")
        source_layout.addWidget(self.source_path)
        
        self.browse_source_btn = QPushButton("Browse")
        self.browse_source_btn.clicked.connect(self.browse_source)
        source_layout.addWidget(self.browse_source_btn)
        
        source_group.setLayout(source_layout)
        main_layout.addWidget(source_group)
        
        # Destination selection
        dest_group = QGroupBox("Destination Location")
        dest_layout = QHBoxLayout()
        
        self.dest_path = QLineEdit()
        self.dest_path.setPlaceholderText("Select destination folder (e.g., external hard drive)")
        dest_layout.addWidget(self.dest_path)
        
        self.browse_dest_btn = QPushButton("Browse")
        self.browse_dest_btn.clicked.connect(self.browse_destination)
        dest_layout.addWidget(self.browse_dest_btn)
        
        dest_group.setLayout(dest_layout)
        main_layout.addWidget(dest_group)
        
        # Filter options
        filter_group = QGroupBox("Filter Options")
        filter_layout = QVBoxLayout()
        
        # Date range selection
        date_layout = QHBoxLayout()
        self.date_filter_checkbox = QCheckBox("Filter by date range")
        self.date_filter_checkbox.stateChanged.connect(self.toggle_date_filter)
        date_layout.addWidget(self.date_filter_checkbox)
        
        date_layout.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setEnabled(False)
        date_layout.addWidget(self.date_from)
        
        date_layout.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setEnabled(False)
        date_layout.addWidget(self.date_to)
        
        filter_layout.addLayout(date_layout)
        
        # File type filter
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("File types:"))
        self.file_type_combo = QComboBox()
        self.file_type_combo.addItems(["All Images", "JPEG only", "PNG only", "RAW files", "Videos", "All files"])
        type_layout.addWidget(self.file_type_combo)
        
        self.scan_btn = QPushButton("Scan Files")
        self.scan_btn.clicked.connect(self.scan_files)
        type_layout.addWidget(self.scan_btn)
        
        filter_layout.addLayout(type_layout)
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # File list
        files_group = QGroupBox("Files to Transfer")
        files_layout = QVBoxLayout()
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(5)
        self.file_table.setHorizontalHeaderLabels(["Select", "Filename", "Size", "Date", "Status"])
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.horizontalHeader().setStretchLastSection(True)
        files_layout.addWidget(self.file_table)
        
        # Selection buttons
        selection_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all_files)
        selection_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all_files)
        selection_layout.addWidget(self.deselect_all_btn)
        
        self.selected_count_label = QLabel("0 files selected (0 MB)")
        selection_layout.addWidget(self.selected_count_label)
        selection_layout.addStretch()
        
        files_layout.addLayout(selection_layout)
        files_group.setLayout(files_layout)
        main_layout.addWidget(files_group)
        
        # Progress section
        progress_group = QGroupBox("Transfer Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        progress_layout.addWidget(self.status_text)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Transfer")
        self.start_btn.clicked.connect(self.start_transfer)
        control_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_transfer)
        self.pause_btn.setEnabled(False)
        control_layout.addWidget(self.pause_btn)
        
        self.resume_btn = QPushButton("Resume Previous")
        self.resume_btn.clicked.connect(self.resume_transfer)
        control_layout.addWidget(self.resume_btn)
        
        self.clear_btn = QPushButton("Clear Progress")
        self.clear_btn.clicked.connect(self.clear_progress)
        control_layout.addWidget(self.clear_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Apply styles
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                padding: 5px 15px;
                border-radius: 3px;
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
    
    def browse_source(self):
        """Browse for source folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.source_path.setText(folder)
            self.progress_tracker.data["last_source"] = folder
            self.progress_tracker.save_progress()
    
    def browse_destination(self):
        """Browse for destination folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_path.setText(folder)
            self.progress_tracker.data["last_destination"] = folder
            self.progress_tracker.save_progress()
    
    def toggle_date_filter(self, state):
        """Enable/disable date filter controls"""
        enabled = state == Qt.Checked
        self.date_from.setEnabled(enabled)
        self.date_to.setEnabled(enabled)
    
    def scan_files(self):
        """Scan source folder for files"""
        source = self.source_path.text()
        if not source or not os.path.exists(source):
            QMessageBox.warning(self, "Warning", "Please select a valid source folder")
            return
        
        self.file_table.setRowCount(0)
        self.selected_files.clear()
        
        # Get file extensions based on filter
        extensions = self.get_file_extensions()
        
        # Get date range if enabled
        date_from = self.date_from.date().toPyDate() if self.date_filter_checkbox.isChecked() else None
        date_to = self.date_to.date().toPyDate() if self.date_filter_checkbox.isChecked() else None
        
        # Scan files
        files_found = []
        for root, dirs, files in os.walk(source):
            for file in files:
                file_path = os.path.join(root, file)
                
                # Check extension
                if extensions and not any(file.lower().endswith(ext) for ext in extensions):
                    continue
                
                # Check date
                try:
                    file_stat = os.stat(file_path)
                    file_date = datetime.fromtimestamp(file_stat.st_mtime).date()
                    
                    if date_from and file_date < date_from:
                        continue
                    if date_to and file_date > date_to:
                        continue
                    
                    files_found.append({
                        'path': file_path,
                        'name': file,
                        'size': file_stat.st_size,
                        'date': file_date,
                        'status': 'Pending'
                    })
                except Exception as e:
                    print(f"Error scanning {file_path}: {e}")
        
        # Populate table
        self.populate_file_table(files_found)
        self.update_selected_count()
    
    def get_file_extensions(self):
        """Get file extensions based on selected filter"""
        filter_type = self.file_type_combo.currentText()
        if filter_type == "All Images":
            return ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.raw', '.heic']
        elif filter_type == "JPEG only":
            return ['.jpg', '.jpeg']
        elif filter_type == "PNG only":
            return ['.png']
        elif filter_type == "RAW files":
            return ['.raw', '.cr2', '.nef', '.arw', '.dng']
        elif filter_type == "Videos":
            return ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        else:  # All files
            return []
    
    def populate_file_table(self, files):
        """Populate the file table with scanned files"""
        self.file_table.setRowCount(len(files))
        
        for row, file_info in enumerate(files):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.update_selected_count)
            self.file_table.setCellWidget(row, 0, checkbox)
            
            # Filename
            self.file_table.setItem(row, 1, QTableWidgetItem(file_info['name']))
            
            # Size
            size_mb = file_info['size'] / (1024 * 1024)
            self.file_table.setItem(row, 2, QTableWidgetItem(f"{size_mb:.2f} MB"))
            
            # Date
            self.file_table.setItem(row, 3, QTableWidgetItem(file_info['date'].strftime("%Y-%m-%d")))
            
            # Status
            self.file_table.setItem(row, 4, QTableWidgetItem(file_info['status']))
            
            # Store file info
            self.file_table.item(row, 1).setData(Qt.UserRole, file_info)
    
    def select_all_files(self):
        """Select all files in the table"""
        for row in range(self.file_table.rowCount()):
            checkbox = self.file_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
        self.update_selected_count()
    
    def deselect_all_files(self):
        """Deselect all files in the table"""
        for row in range(self.file_table.rowCount()):
            checkbox = self.file_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
        self.update_selected_count()
    
    def update_selected_count(self):
        """Update the selected files count and size"""
        selected_files = []
        total_size = 0
        
        for row in range(self.file_table.rowCount()):
            checkbox = self.file_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                file_info = self.file_table.item(row, 1).data(Qt.UserRole)
                selected_files.append(file_info)
                total_size += file_info['size']
        
        self.selected_files = selected_files
        size_mb = total_size / (1024 * 1024)
        self.selected_count_label.setText(f"{len(selected_files)} files selected ({size_mb:.2f} MB)")
    
    def start_transfer(self):
        """Start the file transfer"""
        if not self.selected_files:
            QMessageBox.warning(self, "Warning", "No files selected for transfer")
            return
        
        if not self.dest_path.text():
            QMessageBox.warning(self, "Warning", "Please select a destination folder")
            return
        
        # Update UI
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_text.clear()
        
        # Create and start worker thread
        self.transfer_worker = TransferWorker(
            self.selected_files,
            self.dest_path.text(),
            self.progress_tracker
        )
        
        # Connect signals
        self.transfer_worker.progress_update.connect(self.update_progress)
        self.transfer_worker.status_update.connect(self.update_status)
        self.transfer_worker.file_completed.connect(self.file_completed)
        self.transfer_worker.file_failed.connect(self.file_failed)
        self.transfer_worker.transfer_complete.connect(self.transfer_complete)
        
        # Start transfer
        self.transfer_worker.start()
    
    def pause_transfer(self):
        """Pause the transfer"""
        if self.transfer_worker:
            self.transfer_worker.stop()
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            self.update_status("Transfer paused")
    
    def resume_transfer(self):
        """Resume previous transfer"""
        # Load previous session
        if self.progress_tracker.data["pending"]:
            self.selected_files = self.progress_tracker.data["pending"]
            self.start_transfer()
        else:
            QMessageBox.information(self, "Info", "No pending transfers to resume")
    
    def clear_progress(self):
        """Clear all progress data"""
        reply = QMessageBox.question(self, "Confirm", "Clear all transfer progress?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.progress_tracker.clear_progress()
            self.status_text.clear()
            self.progress_bar.setValue(0)
            QMessageBox.information(self, "Success", "Progress cleared")
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        """Update status text"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def file_completed(self, file_path, size):
        """Handle file completion"""
        # Update table status
        for row in range(self.file_table.rowCount()):
            file_info = self.file_table.item(row, 1).data(Qt.UserRole)
            if file_info and file_info['path'] == file_path:
                self.file_table.item(row, 4).setText("Completed")
                self.file_table.item(row, 4).setBackground(Qt.green)
                break
    
    def file_failed(self, file_path, error):
        """Handle file failure"""
        # Update table status
        for row in range(self.file_table.rowCount()):
            file_info = self.file_table.item(row, 1).data(Qt.UserRole)
            if file_info and file_info['path'] == file_path:
                self.file_table.item(row, 4).setText(f"Failed: {error}")
                self.file_table.item(row, 4).setBackground(Qt.red)
                break
    
    def transfer_complete(self):
        """Handle transfer completion"""
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.update_status("Transfer complete!")
        
        # Show summary
        completed = len(self.progress_tracker.data["completed"])
        failed = len(self.progress_tracker.data["failed"])
        
        summary = f"Transfer Summary:\n"
        summary += f"Completed: {completed} files\n"
        summary += f"Failed: {failed} files\n"
        
        if failed > 0:
            summary += "\nFailed files:\n"
            for f in self.progress_tracker.data["failed"][-5:]:  # Show last 5
                summary += f"- {os.path.basename(f['path'])}: {f['error']}\n"
        
        QMessageBox.information(self, "Transfer Complete", summary)
    
    def load_last_session(self):
        """Load last session paths"""
        if self.progress_tracker.data["last_source"]:
            self.source_path.setText(self.progress_tracker.data["last_source"])
        if self.progress_tracker.data["last_destination"]:
            self.dest_path.setText(self.progress_tracker.data["last_destination"])
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.transfer_worker and self.transfer_worker.isRunning():
            reply = QMessageBox.question(self, "Confirm", "Transfer in progress. Stop and exit?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.transfer_worker.stop()
                self.transfer_worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    window = PhotoTransferWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()