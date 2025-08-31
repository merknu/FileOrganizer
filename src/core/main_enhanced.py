# Enhanced main application with detailed file operation feedback
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QLabel, QFileDialog, QMessageBox,
    QSystemTrayIcon, QMenu, QGroupBox, QGridLayout, QProgressBar,
    QTextEdit, QTabWidget, QTableWidget, QTableWidgetItem,
    QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QCheckBox, QSpinBox, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QIcon, QFont, QColor

# Import actual file processing modules
try:
    from config.config_handler import ConfigHandler
    from gui.main_window import FileOrganizerMainWindow
    from gui.photo_transfer_window import PhotoTransferWindow
    from transfers.downloads_organizer import DownloadsOrganizer
    from transfers.video_transfer import VideoTransferWindow
    from transfers.audio_transfer import AudioTransferWindow
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some modules not available: {e}")
    MODULES_AVAILABLE = False

logging.basicConfig(filename='file_organizer.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s')

if MODULES_AVAILABLE:
    CONFIG_FILE = 'config/config.json'
    config_handler = ConfigHandler(CONFIG_FILE)
    global_app_config = config_handler.config
else:
    global_app_config = {}


class FileOperationResult:
    """Class to store detailed results of file operations"""
    def __init__(self):
        self.processed_files = []
        self.moved_files = []
        self.copied_files = []
        self.deleted_files = []
        self.errors = []
        self.start_time = None
        self.end_time = None
        
    def add_moved_file(self, source: str, destination: str, size: int = 0):
        """Add a moved file to results"""
        self.moved_files.append({
            'source': source,
            'destination': destination,
            'size': size,
            'timestamp': datetime.now()
        })
        
    def add_error(self, file: str, error: str):
        """Add an error to results"""
        self.errors.append({
            'file': file,
            'error': error,
            'timestamp': datetime.now()
        })
        
    def get_summary(self) -> str:
        """Get summary of operations"""
        return f"""
Operation Summary:
• Files Processed: {len(self.processed_files)}
• Files Moved: {len(self.moved_files)}
• Files Copied: {len(self.copied_files)}
• Files Deleted: {len(self.deleted_files)}
• Errors: {len(self.errors)}
• Duration: {self.get_duration()}
        """
        
    def get_duration(self) -> str:
        """Get operation duration"""
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            return str(duration).split('.')[0]
        return "N/A"


class FileOperationWorker(QThread):
    """Worker thread for file operations"""
    progress = pyqtSignal(int, str)
    file_processed = pyqtSignal(dict)
    finished = pyqtSignal(FileOperationResult)
    
    def __init__(self, operation_type: str, files: List[str], options: Dict):
        super().__init__()
        self.operation_type = operation_type
        self.files = files
        self.options = options
        self.result = FileOperationResult()
        
    def run(self):
        """Run the file operation"""
        self.result.start_time = datetime.now()
        
        total_files = len(self.files)
        for i, file_path in enumerate(self.files):
            progress_percent = int((i + 1) / total_files * 100)
            self.progress.emit(progress_percent, f"Processing: {Path(file_path).name}")
            
            # Simulate file processing (replace with actual logic)
            try:
                if self.operation_type == "organize":
                    # Simulate organizing file
                    dest = self.get_organized_destination(file_path)
                    self.result.add_moved_file(file_path, dest, Path(file_path).stat().st_size)
                    self.file_processed.emit({
                        'action': 'moved',
                        'source': file_path,
                        'destination': dest,
                        'size': Path(file_path).stat().st_size
                    })
                elif self.operation_type == "convert":
                    # Simulate converting file
                    self.file_processed.emit({
                        'action': 'converted',
                        'file': file_path,
                        'status': 'success'
                    })
                    
            except Exception as e:
                self.result.add_error(file_path, str(e))
                self.file_processed.emit({
                    'action': 'error',
                    'file': file_path,
                    'error': str(e)
                })
        
        self.result.end_time = datetime.now()
        self.finished.emit(self.result)
    
    def get_organized_destination(self, file_path: str) -> str:
        """Get destination for organized file"""
        # Simple categorization logic
        file = Path(file_path)
        ext = file.suffix.lower()
        
        if ext in ['.jpg', '.png', '.gif', '.bmp']:
            category = 'Images'
        elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
            category = 'Videos'
        elif ext in ['.mp3', '.wav', '.flac', '.aac']:
            category = 'Audio'
        elif ext in ['.pdf', '.doc', '.docx', '.txt']:
            category = 'Documents'
        else:
            category = 'Other'
            
        return str(file.parent / category / file.name)


class ResultsWidget(QWidget):
    """Widget to display detailed operation results"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the results UI"""
        layout = QVBoxLayout(self)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            'Action', 'Source File', 'Destination', 'Size', 'Time'
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.results_table)
        
        # Summary text
        self.summary_text = QTextEdit()
        self.summary_text.setMaximumHeight(100)
        self.summary_text.setReadOnly(True)
        layout.addWidget(self.summary_text)
        
    def add_file_result(self, result: dict):
        """Add a file operation result to the table"""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # Action
        action = result.get('action', 'unknown')
        action_item = QTableWidgetItem(action)
        if action == 'error':
            action_item.setBackground(QColor(255, 200, 200))
        elif action == 'moved':
            action_item.setBackground(QColor(200, 255, 200))
        self.results_table.setItem(row, 0, action_item)
        
        # Source
        source = result.get('source', result.get('file', ''))
        self.results_table.setItem(row, 1, QTableWidgetItem(Path(source).name))
        
        # Destination
        dest = result.get('destination', '-')
        self.results_table.setItem(row, 2, QTableWidgetItem(dest))
        
        # Size
        size = result.get('size', 0)
        if size > 0:
            size_str = self.format_size(size)
        else:
            size_str = '-'
        self.results_table.setItem(row, 3, QTableWidgetItem(size_str))
        
        # Time
        time_str = datetime.now().strftime('%H:%M:%S')
        self.results_table.setItem(row, 4, QTableWidgetItem(time_str))
        
    def format_size(self, size: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
        
    def set_summary(self, summary: str):
        """Set the summary text"""
        self.summary_text.setText(summary)
        
    def clear_results(self):
        """Clear all results"""
        self.results_table.setRowCount(0)
        self.summary_text.clear()


class EnhancedMainApplication(QMainWindow):
    """Enhanced FileOrganizer with detailed feedback and no auto-hide"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileOrganizer - Enhanced")
        self.setGeometry(100, 100, 1200, 800)
        
        # Track current operation
        self.current_worker = None
        
        # Initialize system tray (but don't auto-hide)
        self.init_system_tray()
        
        # Create main interface
        self.init_ui()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Make sure window starts visible and stays on top initially
        self.show()
        self.raise_()
        self.activateWindow()
        self.setWindowState(Qt.WindowActive)
    
    def init_system_tray(self):
        """Initialize system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show FileOrganizer", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("FileOrganizer Enhanced")
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()
    
    def init_ui(self):
        """Create the enhanced main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with splitter
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("FileOrganizer - Enhanced Edition")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Create splitter for main content and results
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # Top widget with tabs
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        top_layout.addWidget(self.progress_bar)
        
        # Current operation label
        self.operation_label = QLabel("")
        self.operation_label.setVisible(False)
        top_layout.addWidget(self.operation_label)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        top_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_file_org_tab()
        self.create_video_tab()
        self.create_audio_tab()
        
        splitter.addWidget(top_widget)
        
        # Results widget
        results_group = QGroupBox("Operation Results - Detailed View")
        results_layout = QVBoxLayout(results_group)
        
        self.results_widget = ResultsWidget()
        results_layout.addWidget(self.results_widget)
        
        splitter.addWidget(results_group)
        
        # Set splitter sizes (60% top, 40% bottom)
        splitter.setSizes([480, 320])
    
    def create_file_org_tab(self):
        """Create enhanced file organization tab"""
        file_tab = QWidget()
        layout = QVBoxLayout(file_tab)
        
        # Quick actions
        quick_group = QGroupBox("Quick File Organization")
        quick_layout = QGridLayout(quick_group)
        
        # Row 1
        select_files_btn = QPushButton("📁 Select Files to Organize")
        select_files_btn.clicked.connect(self.select_files_to_organize)
        quick_layout.addWidget(select_files_btn, 0, 0)
        
        select_folder_btn = QPushButton("📂 Select Folder to Organize")
        select_folder_btn.clicked.connect(self.select_folder_to_organize)
        quick_layout.addWidget(select_folder_btn, 0, 1)
        
        # Row 2
        downloads_btn = QPushButton("⬇️ Organize Downloads Folder")
        downloads_btn.clicked.connect(self.organize_downloads)
        quick_layout.addWidget(downloads_btn, 1, 0)
        
        desktop_btn = QPushButton("🖥️ Organize Desktop")
        desktop_btn.clicked.connect(self.organize_desktop)
        quick_layout.addWidget(desktop_btn, 1, 1)
        
        layout.addWidget(quick_group)
        
        # Organization options
        options_group = QGroupBox("Organization Options")
        options_layout = QGridLayout(options_group)
        
        self.group_by_type = QCheckBox("Group by file type")
        self.group_by_type.setChecked(True)
        options_layout.addWidget(self.group_by_type, 0, 0)
        
        self.group_by_date = QCheckBox("Group by date")
        options_layout.addWidget(self.group_by_date, 0, 1)
        
        self.remove_duplicates = QCheckBox("Remove duplicates")
        options_layout.addWidget(self.remove_duplicates, 1, 0)
        
        self.create_backup = QCheckBox("Create backup before organizing")
        options_layout.addWidget(self.create_backup, 1, 1)
        
        layout.addWidget(options_group)
        
        self.tab_widget.addTab(file_tab, "📁 File Organization")
    
    def create_video_tab(self):
        """Create enhanced video processing tab"""
        video_tab = QWidget()
        layout = QVBoxLayout(video_tab)
        
        video_group = QGroupBox("Video Processing")
        video_layout = QGridLayout(video_group)
        
        select_videos_btn = QPushButton("🎬 Select Video Files")
        select_videos_btn.clicked.connect(self.select_videos)
        video_layout.addWidget(select_videos_btn, 0, 0)
        
        convert_videos_btn = QPushButton("🔄 Convert/Compress Videos")
        convert_videos_btn.clicked.connect(self.open_video_converter)
        video_layout.addWidget(convert_videos_btn, 0, 1)
        
        organize_videos_btn = QPushButton("📚 Organize Video Library")
        organize_videos_btn.clicked.connect(self.organize_videos)
        video_layout.addWidget(organize_videos_btn, 1, 0)
        
        layout.addWidget(video_group)
        self.tab_widget.addTab(video_tab, "🎬 Video Processing")
    
    def create_audio_tab(self):
        """Create enhanced audio processing tab"""
        audio_tab = QWidget()
        layout = QVBoxLayout(audio_tab)
        
        audio_group = QGroupBox("Audio Processing")
        audio_layout = QGridLayout(audio_group)
        
        select_audio_btn = QPushButton("🎵 Select Audio Files")
        select_audio_btn.clicked.connect(self.select_audio)
        audio_layout.addWidget(select_audio_btn, 0, 0)
        
        convert_audio_btn = QPushButton("🔄 Convert Audio Format")
        convert_audio_btn.clicked.connect(self.open_audio_converter)
        audio_layout.addWidget(convert_audio_btn, 0, 1)
        
        organize_audio_btn = QPushButton("📚 Organize Music Library")
        organize_audio_btn.clicked.connect(self.organize_audio)
        audio_layout.addWidget(organize_audio_btn, 1, 0)
        
        layout.addWidget(audio_group)
        self.tab_widget.addTab(audio_tab, "🎵 Audio Processing")
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        clear_results_action = QAction("Clear Results", self)
        clear_results_action.triggered.connect(self.results_widget.clear_results)
        file_menu.addAction(clear_results_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        always_on_top_action = QAction("Always on Top", self)
        always_on_top_action.setCheckable(True)
        always_on_top_action.triggered.connect(self.toggle_always_on_top)
        view_menu.addAction(always_on_top_action)
    
    def show_window(self):
        """Show and activate the main window"""
        self.show()
        self.raise_()
        self.activateWindow()
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            if self.isVisible():
                self.hide()
            else:
                self.show_window()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.current_worker and self.current_worker.isRunning():
            reply = QMessageBox.question(
                self, "Operation in Progress",
                "An operation is currently running. Do you want to cancel it and exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
                
        if self.tray_icon.isVisible():
            QMessageBox.information(self, "FileOrganizer",
                                  "Application was minimized to tray.\n"
                                  "Right-click the tray icon to exit completely.")
            self.hide()
            event.ignore()
        else:
            event.accept()
    
    def changeEvent(self, event):
        """Handle window state changes"""
        if event.type() == event.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                # Optionally hide to tray when minimized
                # QTimer.singleShot(0, self.hide)
                pass  # Keep visible in taskbar when minimized
        super().changeEvent(event)
    
    def toggle_always_on_top(self, checked):
        """Toggle always on top window flag"""
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()
    
    # File operation methods with detailed feedback
    def select_files_to_organize(self):
        """Select individual files to organize with detailed feedback"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files to Organize", 
                                               "", "All Files (*.*)")
        if files:
            self.start_file_operation("organize", files)
    
    def select_folder_to_organize(self):
        """Select folder to organize"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Organize")
        if folder:
            # Get all files in folder
            folder_path = Path(folder)
            files = [str(f) for f in folder_path.rglob('*') if f.is_file()]
            if files:
                self.start_file_operation("organize", files)
            else:
                QMessageBox.information(self, "No Files", "No files found in the selected folder.")
    
    def organize_downloads(self):
        """Organize downloads folder with detailed feedback"""
        if MODULES_AVAILABLE:
            try:
                organizer = DownloadsOrganizer()
                # TODO: Connect to results display
                results = organizer.organize_downloads(dry_run=False)
                self.display_downloads_results(results)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to organize downloads: {str(e)}")
        else:
            # Simulate for demo
            downloads = Path.home() / 'Downloads'
            if downloads.exists():
                files = [str(f) for f in downloads.glob('*') if f.is_file()][:10]  # Limit for demo
                if files:
                    self.start_file_operation("organize", files)
    
    def organize_desktop(self):
        """Organize desktop with detailed feedback"""
        desktop = Path.home() / 'Desktop'
        if desktop.exists():
            files = [str(f) for f in desktop.glob('*') if f.is_file()]
            if files:
                self.start_file_operation("organize", files)
    
    def start_file_operation(self, operation_type: str, files: List[str]):
        """Start a file operation with progress tracking"""
        if self.current_worker and self.current_worker.isRunning():
            QMessageBox.warning(self, "Operation in Progress",
                              "Another operation is already running. Please wait for it to complete.")
            return
        
        # Clear previous results
        self.results_widget.clear_results()
        
        # Show progress UI
        self.progress_bar.setVisible(True)
        self.operation_label.setVisible(True)
        self.progress_bar.setValue(0)
        self.operation_label.setText(f"Starting {operation_type} operation...")
        
        # Get options
        options = {
            'group_by_type': self.group_by_type.isChecked(),
            'group_by_date': self.group_by_date.isChecked(),
            'remove_duplicates': self.remove_duplicates.isChecked(),
            'create_backup': self.create_backup.isChecked()
        }
        
        # Create and start worker
        self.current_worker = FileOperationWorker(operation_type, files, options)
        self.current_worker.progress.connect(self.update_progress)
        self.current_worker.file_processed.connect(self.on_file_processed)
        self.current_worker.finished.connect(self.on_operation_finished)
        self.current_worker.start()
        
        # Keep window visible and in front
        self.show_window()
    
    @pyqtSlot(int, str)
    def update_progress(self, percent: int, message: str):
        """Update progress bar and message"""
        self.progress_bar.setValue(percent)
        self.operation_label.setText(message)
        self.statusBar().showMessage(message)
    
    @pyqtSlot(dict)
    def on_file_processed(self, result: dict):
        """Handle file processed signal"""
        self.results_widget.add_file_result(result)
        # Auto-scroll to latest result
        self.results_widget.results_table.scrollToBottom()
    
    @pyqtSlot(FileOperationResult)
    def on_operation_finished(self, result: FileOperationResult):
        """Handle operation finished signal"""
        # Hide progress UI
        self.progress_bar.setVisible(False)
        self.operation_label.setVisible(False)
        
        # Show summary
        self.results_widget.set_summary(result.get_summary())
        
        # Show completion message
        if result.errors:
            QMessageBox.warning(self, "Operation Completed with Errors",
                              f"Operation completed with {len(result.errors)} errors.\n"
                              f"Check the results table for details.")
        else:
            QMessageBox.information(self, "Operation Completed",
                                  "Operation completed successfully!\n"
                                  f"Processed {len(result.moved_files)} files.")
        
        self.statusBar().showMessage("Operation completed")
        self.current_worker = None
    
    def display_downloads_results(self, results: dict):
        """Display results from DownloadsOrganizer"""
        # Convert results to our format
        for category, files in results.get('organized', {}).items():
            for file_info in files:
                self.results_widget.add_file_result({
                    'action': 'moved',
                    'source': file_info['source'],
                    'destination': file_info['destination'],
                    'size': file_info.get('size', 0)
                })
    
    def select_videos(self):
        """Select and process video files"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Video Files", 
                                               "", "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv)")
        if files:
            self.start_file_operation("process_video", files)
    
    def select_audio(self):
        """Select and process audio files"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Audio Files", 
                                               "", "Audio Files (*.mp3 *.wav *.flac *.aac *.ogg *.wma)")
        if files:
            self.start_file_operation("process_audio", files)
    
    def organize_videos(self):
        """Organize video library"""
        folder = QFileDialog.getExistingDirectory(self, "Select Video Library Folder")
        if folder:
            folder_path = Path(folder)
            video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']
            files = [str(f) for f in folder_path.rglob('*') 
                    if f.is_file() and f.suffix.lower() in video_extensions]
            if files:
                self.start_file_operation("organize_videos", files)
    
    def organize_audio(self):
        """Organize music library"""
        folder = QFileDialog.getExistingDirectory(self, "Select Music Library Folder")
        if folder:
            folder_path = Path(folder)
            audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma']
            files = [str(f) for f in folder_path.rglob('*') 
                    if f.is_file() and f.suffix.lower() in audio_extensions]
            if files:
                self.start_file_operation("organize_audio", files)
    
    def open_video_converter(self):
        """Open video converter window"""
        if MODULES_AVAILABLE:
            try:
                self.video_window = VideoTransferWindow()
                self.video_window.show()
            except:
                QMessageBox.information(self, "Video Converter", 
                                      "Video converter will open here")
        else:
            QMessageBox.information(self, "Video Converter", 
                                  "Video converter module not available")
    
    def open_audio_converter(self):
        """Open audio converter window"""
        if MODULES_AVAILABLE:
            try:
                self.audio_window = AudioTransferWindow()
                self.audio_window.show()
            except:
                QMessageBox.information(self, "Audio Converter", 
                                      "Audio converter will open here")
        else:
            QMessageBox.information(self, "Audio Converter", 
                                  "Audio converter module not available")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("FileOrganizer Enhanced")
    
    # Create and show the enhanced main window
    window = EnhancedMainApplication()
    window.show()
    
    sys.exit(app.exec_())