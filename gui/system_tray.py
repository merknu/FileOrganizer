"""
System Tray Integration for FileOrganizer

Provides background operation with system tray icon and notification support.
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QSystemTrayIcon, QMenu, QAction, QApplication, 
                           QMessageBox, QWidget, QVBoxLayout, QLabel,
                           QPushButton, QHBoxLayout, QCheckBox, QSpinBox,
                           QGroupBox, QGridLayout, QFileDialog, QTextEdit,
                           QDialog, QProgressBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot, QSettings
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json

# Import statistics manager
try:
    from .tray_statistics import StatisticsManager
    STATISTICS_AVAILABLE = True
except ImportError:
    STATISTICS_AVAILABLE = False

# Import main window and processing components
try:
    from .main_window import FileOrganizerMainWindow
    from .processing_thread import ProcessingThread
    MAIN_WINDOW_AVAILABLE = True
except ImportError:
    MAIN_WINDOW_AVAILABLE = False

class TrayNotificationWidget(QWidget):
    """Custom notification widget for system tray"""
    
    def __init__(self, title: str, message: str, duration: int = 5000):
        super().__init__()
        self.duration = duration
        self.setup_ui(title, message)
        self.setup_timer()
        
        # Make window frameless and always on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
    def setup_ui(self, title: str, message: str):
        """Setup notification UI"""
        self.setFixedSize(320, 80)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Style the widget
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(45, 45, 45, 240);
                border-radius: 8px;
                color: white;
            }
            QLabel {
                background-color: transparent;
                border: none;
            }
        """)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(title_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setFont(QFont("Segoe UI", 9))
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
    def setup_timer(self):
        """Setup auto-close timer"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.close)
        self.timer.start(self.duration)
        
    def mousePressEvent(self, event):
        """Close on click"""
        self.close()

class BackgroundProcessorDialog(QDialog):
    """Dialog for configuring background file processing"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Background Processing Settings")
        self.setModal(True)
        self.resize(500, 400)
        self.settings = QSettings("FileOrganizer", "BackgroundProcessor")
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Watch folders section
        watch_group = QGroupBox("Watch Folders")
        watch_layout = QVBoxLayout(watch_group)
        
        # Folder list
        self.folders_text = QTextEdit()
        self.folders_text.setMaximumHeight(100)
        self.folders_text.setPlaceholderText("Add folders to watch (one per line)")
        watch_layout.addWidget(self.folders_text)
        
        # Folder controls
        folder_controls = QHBoxLayout()
        add_folder_btn = QPushButton("Add Folder...")
        add_folder_btn.clicked.connect(self.add_watch_folder)
        clear_folders_btn = QPushButton("Clear All")
        clear_folders_btn.clicked.connect(self.clear_watch_folders)
        folder_controls.addWidget(add_folder_btn)
        folder_controls.addWidget(clear_folders_btn)
        folder_controls.addStretch()
        watch_layout.addLayout(folder_controls)
        
        layout.addWidget(watch_group)
        
        # Processing options
        options_group = QGroupBox("Processing Options")
        options_layout = QGridLayout(options_group)
        
        # Auto-process new files
        self.auto_process_checkbox = QCheckBox("Automatically process new files")
        self.auto_process_checkbox.setChecked(True)
        options_layout.addWidget(self.auto_process_checkbox, 0, 0, 1, 2)
        
        # Check interval
        options_layout.addWidget(QLabel("Check interval (minutes):"), 1, 0)
        self.check_interval_spin = QSpinBox()
        self.check_interval_spin.setRange(1, 60)
        self.check_interval_spin.setValue(5)
        options_layout.addWidget(self.check_interval_spin, 1, 1)
        
        # Minimum file age
        options_layout.addWidget(QLabel("Minimum file age (seconds):"), 2, 0)
        self.min_age_spin = QSpinBox()
        self.min_age_spin.setRange(1, 3600)
        self.min_age_spin.setValue(30)
        self.min_age_spin.setToolTip("Wait this long before processing new files")
        options_layout.addWidget(self.min_age_spin, 2, 1)
        
        # Show notifications
        self.show_notifications_checkbox = QCheckBox("Show processing notifications")
        self.show_notifications_checkbox.setChecked(True)
        options_layout.addWidget(self.show_notifications_checkbox, 3, 0, 1, 2)
        
        # Run on startup
        self.run_on_startup_checkbox = QCheckBox("Start monitoring when application starts")
        self.run_on_startup_checkbox.setChecked(False)
        options_layout.addWidget(self.run_on_startup_checkbox, 4, 0, 1, 2)
        
        layout.addWidget(options_group)
        
        # Status section
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Background processing: Stopped")
        self.status_label.setFont(QFont("", 9, QFont.Bold))
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Monitoring")
        self.start_button.clicked.connect(self.start_monitoring)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop Monitoring")
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        button_layout.addStretch()
        
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
    def add_watch_folder(self):
        """Add a folder to watch"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Watch")
        if folder:
            current_text = self.folders_text.toPlainText().strip()
            if current_text:
                current_text += "\n"
            current_text += folder
            self.folders_text.setPlainText(current_text)
    
    def clear_watch_folders(self):
        """Clear all watch folders"""
        self.folders_text.clear()
    
    def get_watch_folders(self) -> List[str]:
        """Get list of folders to watch"""
        text = self.folders_text.toPlainText().strip()
        if not text:
            return []
        return [line.strip() for line in text.split('\n') if line.strip()]
    
    def start_monitoring(self):
        """Start background monitoring"""
        folders = self.get_watch_folders()
        if not folders:
            QMessageBox.warning(self, "No Folders", "Please add at least one folder to watch.")
            return
            
        self.status_label.setText("Background processing: Running")
        self.status_label.setStyleSheet("color: green;")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Emit signal to parent to start monitoring
        if hasattr(self.parent(), 'start_background_monitoring'):
            self.parent().start_background_monitoring(folders, {
                'auto_process': self.auto_process_checkbox.isChecked(),
                'check_interval': self.check_interval_spin.value(),
                'min_age': self.min_age_spin.value(),
                'show_notifications': self.show_notifications_checkbox.isChecked()
            })
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.status_label.setText("Background processing: Stopped")
        self.status_label.setStyleSheet("color: red;")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # Emit signal to parent to stop monitoring
        if hasattr(self.parent(), 'stop_background_monitoring'):
            self.parent().stop_background_monitoring()
    
    def save_settings(self):
        """Save settings to persistent storage"""
        self.settings.setValue("watch_folders", self.folders_text.toPlainText())
        self.settings.setValue("auto_process", self.auto_process_checkbox.isChecked())
        self.settings.setValue("check_interval", self.check_interval_spin.value())
        self.settings.setValue("min_age", self.min_age_spin.value())
        self.settings.setValue("show_notifications", self.show_notifications_checkbox.isChecked())
        self.settings.setValue("run_on_startup", self.run_on_startup_checkbox.isChecked())
        
        QMessageBox.information(self, "Settings Saved", "Background processing settings have been saved.")
    
    def load_settings(self):
        """Load settings from persistent storage"""
        self.folders_text.setPlainText(self.settings.value("watch_folders", ""))
        self.auto_process_checkbox.setChecked(self.settings.value("auto_process", True, bool))
        self.check_interval_spin.setValue(self.settings.value("check_interval", 5, int))
        self.min_age_spin.setValue(self.settings.value("min_age", 30, int))
        self.show_notifications_checkbox.setChecked(self.settings.value("show_notifications", True, bool))
        self.run_on_startup_checkbox.setChecked(self.settings.value("run_on_startup", False, bool))

class FileWatcher(QThread):
    """Background thread for watching folders and processing files"""
    
    file_detected = pyqtSignal(str)  # New file detected
    processing_started = pyqtSignal(int)  # Number of files to process
    processing_finished = pyqtSignal(dict)  # Processing results
    status_changed = pyqtSignal(str)  # Status message
    
    def __init__(self, folders: List[str], config: Dict[str, Any], stats_manager=None):
        super().__init__()
        self.folders = folders
        self.config = config
        self.running = False
        self.logger = logging.getLogger(__name__)
        self.known_files = set()
        self.stats_manager = stats_manager
        
    def run(self):
        """Main watching loop"""
        self.running = True
        self.status_changed.emit("Starting file monitoring...")
        
        # Initial scan
        self.scan_folders()
        
        while self.running:
            try:
                # Check for new files
                new_files = self.check_for_new_files()
                
                if new_files and self.config.get('auto_process', True):
                    self.status_changed.emit(f"Processing {len(new_files)} new files...")
                    self.processing_started.emit(len(new_files))
                    
                    # Process new files
                    results = self.process_files(new_files)
                    self.processing_finished.emit(results)
                    
                    self.status_changed.emit("Monitoring for new files...")
                
                # Wait for next check
                self.msleep(self.config.get('check_interval', 5) * 60 * 1000)  # Convert minutes to milliseconds
                
            except Exception as e:
                self.logger.error(f"File watcher error: {e}")
                self.status_changed.emit(f"Error: {str(e)}")
                self.msleep(5000)  # Wait 5 seconds before retrying
    
    def scan_folders(self):
        """Initial scan of all folders"""
        self.status_changed.emit("Scanning folders...")
        
        for folder in self.folders:
            if not os.path.exists(folder):
                continue
                
            try:
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        self.known_files.add(file_path)
            except Exception as e:
                self.logger.error(f"Error scanning folder {folder}: {e}")
    
    def check_for_new_files(self) -> List[str]:
        """Check for new files in watched folders"""
        new_files = []
        min_age = self.config.get('min_age', 30)
        current_time = datetime.now().timestamp()
        
        for folder in self.folders:
            if not os.path.exists(folder):
                continue
                
            try:
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # Skip if already known
                        if file_path in self.known_files:
                            continue
                        
                        # Check file age
                        try:
                            file_stat = os.stat(file_path)
                            if current_time - file_stat.st_mtime < min_age:
                                continue  # File too new
                        except OSError:
                            continue  # Can't access file
                        
                        # New file found
                        new_files.append(file_path)
                        self.known_files.add(file_path)
                        self.file_detected.emit(file_path)
                        
            except Exception as e:
                self.logger.error(f"Error checking folder {folder}: {e}")
        
        return new_files
    
    def process_files(self, files: List[str]) -> Dict[str, Any]:
        """Process the detected files"""
        processed = 0
        errors = 0
        total_size = 0
        
        for file_path in files:
            try:
                # Update statistics with current file
                if self.stats_manager:
                    self.stats_manager.set_current_activity("Processing file", file_path)
                
                # Get file info
                file_size = 0
                try:
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                except:
                    pass
                
                # Simulate processing (replace with actual processing logic)
                processing_start = self.currentMSecsSinceEpoch() / 1000.0
                self.msleep(100)  # Small delay for simulation
                processing_time = (self.currentMSecsSinceEpoch() / 1000.0) - processing_start
                
                # Record successful processing
                if self.stats_manager:
                    source_folder = os.path.dirname(file_path)
                    self.stats_manager.record_processing_event(
                        file_path=file_path,
                        action="organized",
                        source_folder=source_folder,
                        destination_folder=source_folder + "/Organized",  # Placeholder
                        file_size=file_size,
                        processing_time=processing_time
                    )
                
                processed += 1
                
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {e}")
                
                # Record error in statistics
                if self.stats_manager:
                    source_folder = os.path.dirname(file_path)
                    self.stats_manager.record_processing_event(
                        file_path=file_path,
                        action="error",
                        source_folder=source_folder,
                        file_size=file_size,
                        processing_time=0.0
                    )
                
                errors += 1
        
        # Update activity back to monitoring
        if self.stats_manager:
            self.stats_manager.set_monitoring_status(True, self.folders)
        
        return {
            'files_processed': processed,
            'errors': errors,
            'total_files': len(files),
            'total_size_mb': total_size / (1024 * 1024)
        }
    
    def stop(self):
        """Stop the file watcher"""
        self.running = False
        self.status_changed.emit("Stopping file monitoring...")

class SystemTrayApp(QApplication):
    """Main system tray application"""
    
    def __init__(self, argv, app_config: Dict[str, Any]):
        super().__init__(argv)
        self.app_config = app_config
        self.main_window = None
        self.file_watcher = None
        self.background_dialog = None
        
        self.logger = logging.getLogger(__name__)
        self.setQuitOnLastWindowClosed(False)  # Keep running when main window closes
        
        # Initialize statistics manager
        if STATISTICS_AVAILABLE:
            self.stats_manager = StatisticsManager()
            self.stats_manager.tooltip_updated.connect(self.update_tray_tooltip)
            self.logger.info("Statistics manager initialized")
        else:
            self.stats_manager = None
            self.logger.warning("Statistics manager not available")
        
        self.setup_tray_icon()
        self.create_tray_menu()
        
        # Load settings and check if should start monitoring
        self.settings = QSettings("FileOrganizer", "SystemTray")
        if self.settings.value("start_monitoring_on_startup", False, bool):
            QTimer.singleShot(2000, self.show_background_settings)  # Delay to let app fully start
    
    def setup_tray_icon(self):
        """Setup the system tray icon"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "System Tray", 
                               "System tray is not available on this system.")
            return False
        
        # Create tray icon
        self.tray_icon = QSystemTrayIcon()
        
        # Create icon (simple colored circle if no icon file available)
        icon = self.create_tray_icon()
        self.tray_icon.setIcon(icon)
        
        self.tray_icon.setToolTip("FileOrganizer - Background File Organization")
        
        # Connect signals
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        return True
    
    def create_tray_icon(self) -> QIcon:
        """Create system tray icon"""
        # Try to load icon from file first
        icon_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'resources', 'icon.png'),
            os.path.join(os.path.dirname(__file__), '..', 'resources', 'tray_icon.png'),
        ]
        
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                return QIcon(icon_path)
        
        # Create a simple icon if no file available
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw a folder-like icon
        painter.setBrush(QColor(70, 130, 200))  # Blue color
        painter.setPen(QColor(50, 90, 150))
        
        # Folder shape
        painter.drawRoundedRect(4, 12, 24, 16, 2, 2)
        painter.drawRoundedRect(4, 8, 10, 4, 1, 1)
        
        # Add "F" for FileOrganizer
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(10, 24, "F")
        
        painter.end()
        
        return QIcon(pixmap)
    
    def create_tray_menu(self):
        """Create the system tray context menu"""
        self.tray_menu = QMenu()
        
        # Show main window action
        show_action = QAction("Show FileOrganizer", self)
        show_action.triggered.connect(self.show_main_window)
        self.tray_menu.addAction(show_action)
        
        # Hide main window action
        hide_action = QAction("Hide FileOrganizer", self)
        hide_action.triggered.connect(self.hide_main_window)
        self.tray_menu.addAction(hide_action)
        
        self.tray_menu.addSeparator()
        
        # Background processing
        background_action = QAction("Background Processing...", self)
        background_action.triggered.connect(self.show_background_settings)
        self.tray_menu.addAction(background_action)
        
        # Quick organize action
        organize_action = QAction("Quick Organize Folder...", self)
        organize_action.triggered.connect(self.quick_organize)
        self.tray_menu.addAction(organize_action)
        
        self.tray_menu.addSeparator()
        
        # Settings submenu
        settings_menu = self.tray_menu.addMenu("Settings")
        
        # GPU settings
        gpu_settings_action = QAction("GPU Settings...", self)
        gpu_settings_action.triggered.connect(self.show_gpu_settings)
        settings_menu.addAction(gpu_settings_action)
        
        # Theme settings
        theme_menu = settings_menu.addMenu("Theme")
        light_action = QAction("Light Theme", self)
        light_action.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addAction(light_action)
        
        dark_action = QAction("Dark Theme", self)
        dark_action.triggered.connect(lambda: self.set_theme("dark"))
        theme_menu.addAction(dark_action)
        
        # Startup option
        self.startup_action = QAction("Start with Windows", self)
        self.startup_action.setCheckable(True)
        self.startup_action.triggered.connect(self.toggle_startup)
        settings_menu.addAction(self.startup_action)
        
        self.tray_menu.addSeparator()
        
        # About action
        about_action = QAction("About FileOrganizer", self)
        about_action.triggered.connect(self.show_about)
        self.tray_menu.addAction(about_action)
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_application)
        self.tray_menu.addAction(exit_action)
        
        # Set menu to tray icon
        self.tray_icon.setContextMenu(self.tray_menu)
    
    def show_tray_icon(self):
        """Show the system tray icon"""
        if hasattr(self, 'tray_icon'):
            self.tray_icon.show()
            return True
        return False
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window()
        elif reason == QSystemTrayIcon.Trigger:
            # Single click - could show a quick status or toggle main window
            if self.main_window and self.main_window.isVisible():
                self.hide_main_window()
            else:
                self.show_main_window()
    
    def show_main_window(self):
        """Show the main application window"""
        try:
            if not MAIN_WINDOW_AVAILABLE:
                self.show_notification("Error", "Main window components not available")
                return
                
            if self.main_window is None:
                self.main_window = FileOrganizerMainWindow(self.app_config)
                
                # Connect main window close event to hide instead of quit
                self.main_window.closeEvent = self.main_window_close_event
            
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            
            self.show_notification("FileOrganizer", "Application window opened")
            
        except Exception as e:
            self.logger.error(f"Error showing main window: {e}")
            self.show_notification("Error", f"Could not open main window: {str(e)}")
    
    def hide_main_window(self):
        """Hide the main application window"""
        if self.main_window:
            self.main_window.hide()
            self.show_notification("FileOrganizer", "Application minimized to system tray")
    
    def main_window_close_event(self, event):
        """Override main window close to hide instead of quit"""
        if self.main_window:
            self.main_window.hide()
            event.ignore()
            self.show_notification("FileOrganizer", "Application minimized to system tray")
    
    def show_background_settings(self):
        """Show background processing settings"""
        try:
            if self.background_dialog is None:
                self.background_dialog = BackgroundProcessorDialog(self)
            
            self.background_dialog.show()
            self.background_dialog.raise_()
            self.background_dialog.activateWindow()
            
        except Exception as e:
            self.logger.error(f"Error showing background settings: {e}")
            self.show_notification("Error", f"Could not open background settings: {str(e)}")
    
    def start_background_monitoring(self, folders: List[str], config: Dict[str, Any]):
        """Start background file monitoring"""
        try:
            if self.file_watcher and self.file_watcher.isRunning():
                self.file_watcher.stop()
                self.file_watcher.wait()
            
            self.file_watcher = FileWatcher(folders, config, self.stats_manager)
            self.file_watcher.file_detected.connect(self.on_file_detected)
            self.file_watcher.processing_started.connect(self.on_processing_started)
            self.file_watcher.processing_finished.connect(self.on_processing_finished)
            self.file_watcher.status_changed.connect(self.on_status_changed)
            
            self.file_watcher.start()
            
            # Update statistics manager with monitoring status
            if self.stats_manager:
                self.stats_manager.set_monitoring_status(True, folders)
            
            folder_names = [os.path.basename(f) for f in folders]
            self.show_notification("Background Monitoring", 
                                 f"Started monitoring: {', '.join(folder_names[:3])}")
            
        except Exception as e:
            self.logger.error(f"Error starting background monitoring: {e}")
            self.show_notification("Error", f"Could not start monitoring: {str(e)}")
    
    def stop_background_monitoring(self):
        """Stop background file monitoring"""
        try:
            if self.file_watcher and self.file_watcher.isRunning():
                self.file_watcher.stop()
                self.file_watcher.wait()
            
            # Update statistics manager with monitoring status
            if self.stats_manager:
                self.stats_manager.set_monitoring_status(False)
                
            self.show_notification("Background Monitoring", "Monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping background monitoring: {e}")
    
    @pyqtSlot(str)
    def on_file_detected(self, file_path: str):
        """Handle new file detection"""
        if self.settings.value("show_file_notifications", True, bool):
            filename = os.path.basename(file_path)
            self.show_notification("New File Detected", f"Found: {filename}")
    
    @pyqtSlot(int)
    def on_processing_started(self, count: int):
        """Handle processing start"""
        self.show_notification("Processing Files", f"Processing {count} files...")
    
    @pyqtSlot(dict)
    def on_processing_finished(self, results: Dict[str, Any]):
        """Handle processing completion"""
        processed = results.get('files_processed', 0)
        errors = results.get('errors', 0)
        
        if errors > 0:
            self.show_notification("Processing Complete", 
                                 f"Processed {processed} files with {errors} errors")
        else:
            self.show_notification("Processing Complete", f"Successfully processed {processed} files")
    
    @pyqtSlot(str)
    def on_status_changed(self, status: str):
        """Handle status change"""
        # Update tooltip with current status (will be overridden by statistics manager if available)
        if not self.stats_manager:
            self.tray_icon.setToolTip(f"FileOrganizer - {status}")
    
    @pyqtSlot(str)
    def update_tray_tooltip(self, tooltip_text: str):
        """Update the system tray tooltip with statistics"""
        try:
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.setToolTip(tooltip_text)
        except Exception as e:
            self.logger.error(f"Error updating tray tooltip: {e}")
    
    def quick_organize(self):
        """Quick organize a selected folder"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            folder = QFileDialog.getExistingDirectory(None, "Select Folder to Organize")
            if folder:
                # This would integrate with the main processing logic
                self.show_notification("Quick Organize", f"Organizing: {os.path.basename(folder)}")
                # TODO: Implement actual quick organize functionality
                
        except Exception as e:
            self.logger.error(f"Error in quick organize: {e}")
            self.show_notification("Error", f"Quick organize failed: {str(e)}")
    
    def show_gpu_settings(self):
        """Show GPU settings dialog"""
        try:
            # Create main window temporarily if needed to access GPU settings
            if self.main_window is None:
                self.main_window = FileOrganizerMainWindow(self.app_config)
            
            self.main_window.show_gpu_settings()
            
        except Exception as e:
            self.logger.error(f"Error showing GPU settings: {e}")
            self.show_notification("Error", f"Could not open GPU settings: {str(e)}")
    
    def set_theme(self, theme_name: str):
        """Set application theme"""
        try:
            if self.main_window and hasattr(self.main_window, 'theme_manager'):
                self.main_window.set_theme(theme_name)
                self.show_notification("Theme Changed", f"Applied {theme_name} theme")
            else:
                # Apply theme for future windows
                self.settings.setValue("theme", theme_name)
                self.show_notification("Theme Changed", f"Theme will apply when window opens")
                
        except Exception as e:
            self.logger.error(f"Error setting theme: {e}")
    
    def toggle_startup(self):
        """Toggle startup with Windows"""
        try:
            from startup_manager import StartupManager
            manager = StartupManager()
            
            enabled = self.startup_action.isChecked()
            
            if enabled:
                success = manager.enable_startup()
            else:
                success = manager.disable_startup()
            
            if success:
                self.settings.setValue("start_with_windows", enabled)
                status = "enabled" if enabled else "disabled"
                self.show_notification("Startup Setting", f"Start with Windows {status}")
            else:
                # Revert checkbox if operation failed
                self.startup_action.setChecked(not enabled)
                self.show_notification("Startup Error", "Failed to update Windows startup setting")
                
        except ImportError:
            # Fallback to settings only
            enabled = self.startup_action.isChecked()
            self.settings.setValue("start_with_windows", enabled)
            status = "enabled" if enabled else "disabled"
            self.show_notification("Startup Setting", f"Start with Windows {status} (registry not updated)")
        except Exception as e:
            self.logger.error(f"Error toggling startup: {e}")
            self.show_notification("Startup Error", f"Error updating startup: {str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(None, "About FileOrganizer",
                         "FileOrganizer v3.0 - System Tray Edition\n\n"
                         "Background file organization with GPU acceleration.\n\n"
                         "Features:\n"
                         "• System tray operation\n"
                         "• Background file monitoring\n"
                         "• GPU-accelerated processing\n"
                         "• Real-time notifications\n"
                         "• Theme support\n\n"
                         "Right-click the tray icon for options.")
    
    def show_notification(self, title: str, message: str, duration: int = 3000):
        """Show system tray notification"""
        try:
            if hasattr(self, 'tray_icon'):
                # Use system tray notification if available
                self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, duration)
            else:
                # Fallback to custom notification widget
                notification = TrayNotificationWidget(title, message, duration)
                
                # Position notification in bottom-right corner
                screen = self.primaryScreen().availableGeometry()
                x = screen.width() - notification.width() - 20
                y = screen.height() - notification.height() - 20
                notification.move(x, y)
                notification.show()
                
        except Exception as e:
            self.logger.error(f"Error showing notification: {e}")
    
    def exit_application(self):
        """Exit the application"""
        try:
            # Stop background monitoring
            if self.file_watcher and self.file_watcher.isRunning():
                self.file_watcher.stop()
                self.file_watcher.wait(3000)  # Wait up to 3 seconds
            
            # Close main window if open
            if self.main_window:
                self.main_window.close()
            
            # Hide tray icon
            if hasattr(self, 'tray_icon'):
                self.tray_icon.hide()
            
            self.quit()
            
        except Exception as e:
            self.logger.error(f"Error during exit: {e}")
            self.quit()  # Force quit anyway

def create_system_tray_app(app_config: Dict[str, Any]) -> SystemTrayApp:
    """Create and configure system tray application"""
    
    # Ensure system tray is available
    if not QSystemTrayIcon.isSystemTrayAvailable():
        raise RuntimeError("System tray is not available on this system")
    
    # Create application
    app = SystemTrayApp(sys.argv, app_config)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    return app

if __name__ == "__main__":
    # Test configuration
    test_config = {
        'gpu_config': {
            'enable_gpu': True,
            'backend': 'auto'
        },
        'processing': {
            'max_workers': 4
        }
    }
    
    try:
        app = create_system_tray_app(test_config)
        
        if app.setup_tray_icon():
            app.show_tray_icon()
            print("FileOrganizer is running in the system tray")
            print("Right-click the tray icon to access features")
            
            sys.exit(app.exec_())
        else:
            print("Could not create system tray icon")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error starting system tray application: {e}")
        sys.exit(1)