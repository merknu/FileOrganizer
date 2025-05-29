# Path: gui/main_window.py
# Enhanced main window with better error handling and improved UI
import os
import logging
from typing import List, Optional, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QLabel, QProgressBar, QMessageBox, QTextEdit, QSplitter, QCheckBox,
    QStatusBar, QMenuBar, QAction, QTabWidget, QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont

from .processing_thread import ProcessingThread
from file_handler.file_utils import organize_files


class FileOrganizerMainWindow(QMainWindow):
    """Enhanced main window for File Organizer application."""
    
    # Custom signals
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    
    def __init__(self, app_config: Dict[str, Any]):
        super().__init__()
        self.app_config = app_config
        self.selected_folders: List[str] = []
        self.processing_thread: Optional[ProcessingThread] = None
        self.is_processing = False
        self.processed_files_count = 0
        self.total_files_count = 0
        
        # UI Elements
        self.select_folders_button: Optional[QPushButton] = None
        self.start_processing_button: Optional[QPushButton] = None
        self.preview_button: Optional[QPushButton] = None
        self.stop_button: Optional[QPushButton] = None
        self.before_text_edit: Optional[QTextEdit] = None
        self.after_text_edit: Optional[QTextEdit] = None
        self.preview_text_edit: Optional[QTextEdit] = None
        self.status_label: Optional[QLabel] = None
        self.progress_bar: Optional[QProgressBar] = None
        self.recursive_checkbox: Optional[QCheckBox] = None
        self.auto_confirm_checkbox: Optional[QCheckBox] = None
        
        # Status bar
        self.status_bar: Optional[QStatusBar] = None
        
        # Timer for UI updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        
        self.init_ui()
        self.setup_logging()
        self.connect_signals()
    
    def setup_logging(self):
        """Setup logging for the main window."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('File Organizer - Enhanced')
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Set application icon if available
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'icon.png')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            self.logger.warning(f"Could not load application icon: {e}")
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create central widget
        central_widget = QWidget(self)
        central_widget.setAcceptDrops(True)
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        central_widget.setLayout(main_layout)
        
        # Create control panel
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # Create progress section
        progress_section = self.create_progress_section()
        main_layout.addWidget(progress_section)
        
        # Create tabs for different views
        tab_widget = self.create_tab_widget()
        main_layout.addWidget(tab_widget)
        
        # Create status bar
        self.create_status_bar()
        
        # Set initial state
        self.update_button_states()
    
    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        select_action = QAction('&Select Folders', self)
        select_action.triggered.connect(self.on_select_folders_button_clicked)
        file_menu.addAction(select_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Settings menu
        settings_menu = menubar.addMenu('&Settings')
        
        config_action = QAction('&Configuration', self)
        config_action.triggered.connect(self.show_config_dialog)
        settings_menu.addAction(config_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
    
    def create_control_panel(self) -> QGroupBox:
        """Create the control panel with buttons and options."""
        control_panel = QGroupBox("Control Panel")
        layout = QGridLayout()
        
        # Folder selection
        self.select_folders_button = QPushButton("Select Folders", self)
        self.select_folders_button.clicked.connect(self.on_select_folders_button_clicked)
        layout.addWidget(self.select_folders_button, 0, 0)
        
        # Options
        self.recursive_checkbox = QCheckBox("Process subfolders recursively")
        self.recursive_checkbox.setChecked(True)
        layout.addWidget(self.recursive_checkbox, 0, 1)
        
        self.auto_confirm_checkbox = QCheckBox("Auto-confirm duplicates (use default action)")
        self.auto_confirm_checkbox.setChecked(True)
        layout.addWidget(self.auto_confirm_checkbox, 0, 2)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.preview_button = QPushButton("Preview Changes", self)
        self.preview_button.clicked.connect(self.on_preview_button_clicked)
        button_layout.addWidget(self.preview_button)
        
        self.start_processing_button = QPushButton("Start Processing", self)
        self.start_processing_button.clicked.connect(self.on_start_processing_button_clicked)
        button_layout.addWidget(self.start_processing_button)
        
        self.stop_button = QPushButton("Stop", self)
        self.stop_button.clicked.connect(self.on_stop_button_clicked)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout, 1, 0, 1, 3)
        
        control_panel.setLayout(layout)
        return control_panel
    
    def create_progress_section(self) -> QGroupBox:
        """Create the progress display section."""
        progress_section = QGroupBox("Progress")
        layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("Select folders to process")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        progress_section.setLayout(layout)
        return progress_section
    
    def create_tab_widget(self) -> QTabWidget:
        """Create tabbed interface for different views."""
        tab_widget = QTabWidget()
        
        # Preview tab
        preview_tab = QWidget()
        preview_layout = QVBoxLayout()
        
        self.preview_text_edit = QTextEdit()
        self.preview_text_edit.setReadOnly(True)
        self.preview_text_edit.setFont(QFont("Consolas", 10))
        preview_layout.addWidget(self.preview_text_edit)
        
        preview_tab.setLayout(preview_layout)
        tab_widget.addTab(preview_tab, "Preview")
        
        # Before/After comparison tab
        comparison_tab = QWidget()
        comparison_layout = QVBoxLayout()
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Before section
        before_group = QGroupBox("Before")
        before_layout = QVBoxLayout()
        self.before_text_edit = QTextEdit()
        self.before_text_edit.setReadOnly(True)
        self.before_text_edit.setFont(QFont("Consolas", 10))
        before_layout.addWidget(self.before_text_edit)
        before_group.setLayout(before_layout)
        splitter.addWidget(before_group)
        
        # After section
        after_group = QGroupBox("After")
        after_layout = QVBoxLayout()
        self.after_text_edit = QTextEdit()
        self.after_text_edit.setReadOnly(True)
        self.after_text_edit.setFont(QFont("Consolas", 10))
        after_layout.addWidget(self.after_text_edit)
        after_group.setLayout(after_layout)
        splitter.addWidget(after_group)
        
        comparison_layout.addWidget(splitter)
        comparison_tab.setLayout(comparison_layout)
        tab_widget.addTab(comparison_tab, "Before/After")
        
        return tab_widget
    
    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def connect_signals(self):
        """Connect custom signals."""
        self.status_update.connect(self.update_status_message)
        self.progress_update.connect(self.update_progress)
    
    def update_button_states(self):
        """Update button enabled/disabled states."""
        has_folders = len(self.selected_folders) > 0
        
        self.preview_button.setEnabled(has_folders and not self.is_processing)
        self.start_processing_button.setEnabled(has_folders and not self.is_processing)
        self.stop_button.setEnabled(self.is_processing)
        self.select_folders_button.setEnabled(not self.is_processing)
    
    def on_select_folders_button_clicked(self):
        """Handle folder selection."""
        try:
            dialog = QFileDialog()
            dialog.setFileMode(QFileDialog.Directory)
            dialog.setOption(QFileDialog.ShowDirsOnly, True)
            
            if dialog.exec_():
                selected_paths = dialog.selectedFiles()
                if selected_paths:
                    self.selected_folders = selected_paths
                    folder_names = [os.path.basename(path) for path in selected_paths]
                    self.status_label.setText(f"Selected folder(s): {', '.join(folder_names)}")
                    self.status_bar.showMessage(f"Selected {len(selected_paths)} folder(s)")
                    self.update_button_states()
                    
                    # Update before text with folder structure
                    self.update_before_structure()
                else:
                    self.status_label.setText("No folders selected")
                    self.status_bar.showMessage("No folders selected")
        
        except Exception as e:
            self.logger.error(f"Error selecting folders: {e}")
            self.show_error_message("Error selecting folders", str(e))
    
    def update_before_structure(self):
        """Update the 'before' text with current folder structure."""
        if not self.selected_folders:
            return
        
        try:
            structure_text = "Current folder structure:\n\n"
            for folder in self.selected_folders:
                structure_text += f"📁 {folder}\n"
                try:
                    for root, dirs, files in os.walk(folder):
                        level = root.replace(folder, '').count(os.sep)
                        indent = '  ' * level
                        structure_text += f"{indent}📁 {os.path.basename(root)}/\n"
                        subindent = '  ' * (level + 1)
                        for file in files[:10]:  # Limit to first 10 files
                            structure_text += f"{subindent}📄 {file}\n"
                        if len(files) > 10:
                            structure_text += f"{subindent}... and {len(files) - 10} more files\n"
                        structure_text += "\n"
                except Exception as e:
                    structure_text += f"  Error reading folder: {e}\n"
            
            self.before_text_edit.setPlainText(structure_text)
        
        except Exception as e:
            self.logger.error(f"Error updating before structure: {e}")
    
    def on_preview_button_clicked(self):
        """Handle preview button click."""
        if not self.selected_folders:
            self.show_warning_message("No folders selected", "Please select folders first.")
            return
        
        try:
            self.is_processing = True
            self.update_button_states()
            self.progress_bar.setVisible(True)
            self.status_update.emit("Generating preview...")
            
            # Start processing thread in preview mode
            self.processing_thread = ProcessingThread(
                folders=self.selected_folders,
                app_config=self.app_config,
                recursive=self.recursive_checkbox.isChecked(),
                preview_mode=True,
                callback=self.on_file_processed
            )
            
            self.processing_thread.processing_finished.connect(self.on_preview_finished)
            self.processing_thread.error_occurred.connect(self.on_error_occurred)
            self.processing_thread.start()
            
            # Start update timer
            self.update_timer.start(500)  # Update every 500ms
        
        except Exception as e:
            self.logger.error(f"Error starting preview: {e}")
            self.show_error_message("Preview Error", str(e))
            self.is_processing = False
            self.update_button_states()
    
    def on_start_processing_button_clicked(self):
        """Handle start processing button click."""
        if not self.selected_folders:
            self.show_warning_message("No folders selected", "Please select folders first.")
            return
        
        # Confirm action
        reply = QMessageBox.question(
            self, "Confirm Processing",
            "Are you sure you want to start organizing files? This will move files to new locations.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            self.is_processing = True
            self.update_button_states()
            self.progress_bar.setVisible(True)
            self.processed_files_count = 0
            self.status_update.emit("Processing files...")
            
            # Start processing thread
            self.processing_thread = ProcessingThread(
                folders=self.selected_folders,
                app_config=self.app_config,
                recursive=self.recursive_checkbox.isChecked(),
                preview_mode=False,
                callback=self.on_file_processed
            )
            
            self.processing_thread.processing_finished.connect(self.on_processing_finished)
            self.processing_thread.error_occurred.connect(self.on_error_occurred)
            self.processing_thread.start()
            
            # Start update timer
            self.update_timer.start(500)
        
        except Exception as e:
            self.logger.error(f"Error starting processing: {e}")
            self.show_error_message("Processing Error", str(e))
            self.is_processing = False
            self.update_button_states()
    
    def on_stop_button_clicked(self):
        """Handle stop button click."""
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self, "Confirm Stop",
                "Are you sure you want to stop processing?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.processing_thread.stop()
                self.status_update.emit("Stopping...")
    
    def on_file_processed(self):
        """Handle file processed callback."""
        self.processed_files_count += 1
    
    def on_preview_finished(self, summary: Dict[str, Any]):
        """Handle preview completion."""
        try:
            self.is_processing = False
            self.update_button_states()
            self.progress_bar.setVisible(False)
            self.update_timer.stop()
            
            # Display preview results
            preview_text = "Preview Results:\n\n"
            for key, value in summary.items():
                preview_text += f"{key.replace('_', ' ').title()}: {value}\n"
            
            self.preview_text_edit.setPlainText(preview_text)
            self.status_update.emit("Preview completed")
            
        except Exception as e:
            self.logger.error(f"Error handling preview completion: {e}")
    
    def on_processing_finished(self, summary: Dict[str, Any]):
        """Handle processing completion."""
        try:
            self.is_processing = False
            self.update_button_states()
            self.progress_bar.setVisible(False)
            self.update_timer.stop()
            
            # Display results
            result_text = "Processing Results:\n\n"
            for key, value in summary.items():
                result_text += f"{key.replace('_', ' ').title()}: {value}\n"
            
            self.after_text_edit.setPlainText(result_text)
            self.status_update.emit("Processing completed successfully")
            
            # Show completion message
            QMessageBox.information(
                self, "Processing Complete",
                f"File organization completed!\n\nFiles processed: {self.processed_files_count}"
            )
            
        except Exception as e:
            self.logger.error(f"Error handling processing completion: {e}")
    
    def on_error_occurred(self, error_message: str):
        """Handle error from processing thread."""
        self.is_processing = False
        self.update_button_states()
        self.progress_bar.setVisible(False)
        self.update_timer.stop()
        
        self.logger.error(f"Processing error: {error_message}")
        self.show_error_message("Processing Error", error_message)
        self.status_update.emit(f"Error: {error_message}")
    
    def update_status_message(self, message: str):
        """Update status message."""
        self.status_label.setText(message)
        self.status_bar.showMessage(message)
    
    def update_progress(self, progress: int):
        """Update progress bar."""
        self.progress_bar.setValue(progress)
    
    def update_ui(self):
        """Periodic UI update."""
        if self.is_processing:
            # Update progress based on processed files
            if self.total_files_count > 0:
                progress = min(100, int((self.processed_files_count / self.total_files_count) * 100))
                self.progress_update.emit(progress)
    
    def show_error_message(self, title: str, message: str):
        """Show error message dialog."""
        QMessageBox.critical(self, title, message)
    
    def show_warning_message(self, title: str, message: str):
        """Show warning message dialog."""
        QMessageBox.warning(self, title, message)
    
    def show_config_dialog(self):
        """Show configuration dialog."""
        QMessageBox.information(self, "Configuration", "Configuration dialog not yet implemented.")
    
    def show_about_dialog(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About File Organizer",
            "File Organizer v2.0\n\n"
            "A Python application for organizing files automatically.\n\n"
            "Features:\n"
            "• Organize files by type, size, and metadata\n"
            "• Preview changes before applying\n"
            "• Handle duplicates intelligently\n"
            "• Recursive folder processing\n\n"
            "Built with PyQt5 and Python."
        )
    
    def dragEnterEvent(self, event):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move events."""
        event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop events."""
        try:
            urls = [url.toLocalFile() for url in event.mimeData().urls()]
            folders = [url for url in urls if os.path.isdir(url)]
            
            if folders:
                self.selected_folders = folders
                folder_names = [os.path.basename(path) for path in folders]
                self.status_update.emit(f"Dropped folder(s): {', '.join(folder_names)}")
                self.update_button_states()
                self.update_before_structure()
                event.acceptProposedAction()
            else:
                self.show_warning_message("Invalid Drop", "Please drop folders, not files.")
                event.ignore()
        
        except Exception as e:
            self.logger.error(f"Error handling drop event: {e}")
            event.ignore()
    
    def closeEvent(self, event):
        """Handle application close event."""
        if self.is_processing:
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "Processing is currently running. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                event.ignore()
                return
            
            # Stop processing thread
            if self.processing_thread and self.processing_thread.isRunning():
                self.processing_thread.stop()
                self.processing_thread.wait(3000)  # Wait up to 3 seconds
        
        event.accept()
