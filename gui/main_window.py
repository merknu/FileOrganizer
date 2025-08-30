# Path: gui/main_window.py
# Enhanced main window with better error handling and improved UI
import os
import logging
from typing import List, Optional, Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QLabel, QProgressBar, QMessageBox, QTextEdit, QSplitter, QCheckBox,
    QStatusBar, QMenuBar, QAction, QTabWidget, QGroupBox, QGridLayout,
    QDockWidget, QFrame, QToolBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QFont

from .processing_thread import ProcessingThread
from file_handler.file_utils import organize_files

# Import new GUI widgets with error handling
try:
    from .gpu_status_widget import GPUStatusWidget
    from .performance_monitor import PerformanceMonitorWidget
    from .gpu_settings_dialog import GPUSettingsDialog
    from .advanced_filters import AdvancedFiltersWidget
    from .drag_drop_widget import DragDropWidget
    from .preview_widget import PreviewWidget
    from .theme_manager import ThemeManager, ThemeToggleWidget
    ENHANCED_WIDGETS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Enhanced GUI widgets not available: {e}")
    ENHANCED_WIDGETS_AVAILABLE = False
    # Create dummy classes to prevent errors
    class GPUStatusWidget: pass
    class PerformanceMonitorWidget: pass
    class GPUSettingsDialog: pass
    class AdvancedFiltersWidget: pass
    class DragDropWidget: pass
    class PreviewWidget: pass
    class ThemeManager: pass
    class ThemeToggleWidget: pass


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
        
        # Initialize theme manager first (if available)
        if ENHANCED_WIDGETS_AVAILABLE:
            self.theme_manager = ThemeManager()
        else:
            self.theme_manager = None
        
        # UI Elements - Original
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
        
        # New enhanced GUI widgets
        self.gpu_status_widget: Optional[GPUStatusWidget] = None
        self.performance_monitor: Optional[PerformanceMonitorWidget] = None
        self.gpu_settings_dialog: Optional[GPUSettingsDialog] = None
        self.advanced_filters_widget: Optional[AdvancedFiltersWidget] = None
        self.drag_drop_widget: Optional[DragDropWidget] = None
        self.preview_widget: Optional[PreviewWidget] = None
        self.theme_toggle_widget: Optional[ThemeToggleWidget] = None
        
        # Status bar
        self.status_bar: Optional[QStatusBar] = None
        
        # Timer for UI updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        
        self.init_ui()
        self.setup_logging()
        self.connect_signals()
        self.validate_ui_components()
    
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
        """Initialize the enhanced user interface."""
        self.setWindowTitle('FileOrganizer - Enhanced with GPU Acceleration')
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        # Set application icon if available
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'icon.png')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            self.logger.warning(f"Could not load application icon: {e}")
        
        # Apply initial theme (if theme manager available)
        if self.theme_manager:
            from PyQt5.QtWidgets import QApplication
            self.theme_manager.apply_theme(QApplication.instance(), "light")
        
        # Create menu bar and toolbar
        self.create_menu_bar()
        self.create_toolbar()
        
        # Create dock widgets for enhanced features
        self.create_dock_widgets()
        
        # Create central widget with enhanced layout
        self.create_enhanced_central_widget()
        
        # Create status bar
        self.create_status_bar()
        
        # Connect signals for new widgets
        self.connect_enhanced_signals()
        
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
        
        gpu_settings_action = QAction('&GPU Settings...', self)
        gpu_settings_action.triggered.connect(self.show_gpu_settings)
        settings_menu.addAction(gpu_settings_action)
        
        theme_action = QAction('&Theme Settings...', self)
        theme_action.triggered.connect(self.show_theme_settings)
        settings_menu.addAction(theme_action)
        
        # View menu
        view_menu = menubar.addMenu('&View')
        
        toggle_gpu_action = QAction('GPU Status Panel', self)
        toggle_gpu_action.setCheckable(True)
        toggle_gpu_action.setChecked(True)
        toggle_gpu_action.triggered.connect(self.toggle_gpu_panel)
        view_menu.addAction(toggle_gpu_action)
        
        toggle_performance_action = QAction('Performance Monitor', self)
        toggle_performance_action.setCheckable(True)
        toggle_performance_action.setChecked(True)
        toggle_performance_action.triggered.connect(self.toggle_performance_panel)
        view_menu.addAction(toggle_performance_action)
        
        toggle_filters_action = QAction('Advanced Filters', self)
        toggle_filters_action.setCheckable(True)
        toggle_filters_action.setChecked(True)
        toggle_filters_action.triggered.connect(self.toggle_filters_panel)
        view_menu.addAction(toggle_filters_action)
        
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
        try:
            self.status_update.connect(self.update_status_message)
            self.progress_update.connect(self.update_progress)
        except Exception as e:
            self.logger.error(f"Error connecting signals: {e}")
    
    def validate_ui_components(self):
        """Validate that all critical UI components are initialized."""
        critical_components = [
            ('select_folders_button', self.select_folders_button),
            ('start_processing_button', self.start_processing_button),
            ('preview_button', self.preview_button),
            ('stop_button', self.stop_button),
            ('status_label', self.status_label),
            ('progress_bar', self.progress_bar),
            ('recursive_checkbox', self.recursive_checkbox),
            ('preview_text_edit', self.preview_text_edit),
            ('before_text_edit', self.before_text_edit),
            ('after_text_edit', self.after_text_edit)
        ]
        
        # Add enhanced components
        enhanced_components = [
            ('drag_drop_widget', self.drag_drop_widget),
            ('gpu_status_widget', self.gpu_status_widget),
            ('performance_monitor', self.performance_monitor),
            ('advanced_filters_widget', self.advanced_filters_widget),
            ('preview_widget', self.preview_widget),
            ('theme_toggle_widget', self.theme_toggle_widget)
        ]
        
        all_components = critical_components + enhanced_components
        
        missing_components = []
        for name, component in all_components:
            if component is None:
                if name in [c[0] for c in critical_components]:
                    # Critical components
                    missing_components.append(name)
                    self.logger.error(f"Critical UI component not initialized: {name}")
                else:
                    # Enhanced components (warn but don't fail)
                    self.logger.warning(f"Enhanced UI component not initialized: {name}")
        
        if missing_components:
            error_msg = f"Missing critical UI components: {', '.join(missing_components)}"
            self.logger.error(error_msg)
            # Try to show error message if possible
            try:
                QMessageBox.critical(self, "UI Initialization Error", error_msg)
            except:
                pass
    
    def update_button_states(self):
        """Update button enabled/disabled states."""
        has_folders = len(self.selected_folders) > 0
        
        # Safely update button states with None checks
        if self.preview_button:
            self.preview_button.setEnabled(has_folders and not self.is_processing)
        if self.start_processing_button:
            self.start_processing_button.setEnabled(has_folders and not self.is_processing)
        if self.stop_button:
            self.stop_button.setEnabled(self.is_processing)
        if self.select_folders_button:
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
        
        # Validate UI elements exist
        if not self.recursive_checkbox or not self.progress_bar:
            self.show_error_message("UI Error", "UI components not properly initialized.")
            return
        
        try:
            self.is_processing = True
            self.update_button_states()
            self.progress_bar.setVisible(True)
            self.status_update.emit("Generating preview...")
            
            # Stop any existing thread
            if self.processing_thread and self.processing_thread.isRunning():
                self.processing_thread.stop()
                self.processing_thread.wait(1000)
            
            # Start processing thread in preview mode
            self.processing_thread = ProcessingThread(
                folders=self.selected_folders,
                app_config=self.app_config,
                recursive=self.recursive_checkbox.isChecked(),
                preview_mode=True,
                callback=self.on_file_processed
            )
            
            # Validate thread was created successfully
            if self.processing_thread is None:
                raise Exception("Failed to create processing thread")
            
            # Connect signals
            self.processing_thread.processing_finished.connect(self.on_preview_finished)
            self.processing_thread.error_occurred.connect(self.on_error_occurred)
            self.processing_thread.file_processed.connect(self.on_file_processed_signal)
            self.processing_thread.status_changed.connect(self.update_status_message)
            
            # Start the thread
            self.processing_thread.start()
            
            # Start update timer
            self.update_timer.start(500)  # Update every 500ms
        
        except Exception as e:
            self.logger.error(f"Error starting preview: {e}")
            self.show_error_message("Preview Error", str(e))
            self.is_processing = False
            self.progress_bar.setVisible(False) if self.progress_bar else None
            self.update_button_states()
    
    def on_start_processing_button_clicked(self):
        """Handle start processing button click."""
        if not self.selected_folders:
            self.show_warning_message("No folders selected", "Please select folders first.")
            return
        
        # Validate UI elements exist
        if not self.recursive_checkbox or not self.progress_bar:
            self.show_error_message("UI Error", "UI components not properly initialized.")
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
            
            # Stop any existing thread
            if self.processing_thread and self.processing_thread.isRunning():
                self.processing_thread.stop()
                self.processing_thread.wait(1000)
            
            # Start processing thread
            self.processing_thread = ProcessingThread(
                folders=self.selected_folders,
                app_config=self.app_config,
                recursive=self.recursive_checkbox.isChecked(),
                preview_mode=False,
                callback=self.on_file_processed
            )
            
            # Validate thread was created successfully
            if self.processing_thread is None:
                raise Exception("Failed to create processing thread")
            
            # Connect signals
            self.processing_thread.processing_finished.connect(self.on_processing_finished)
            self.processing_thread.error_occurred.connect(self.on_error_occurred)
            self.processing_thread.file_processed.connect(self.on_file_processed_signal)
            self.processing_thread.status_changed.connect(self.update_status_message)
            
            # Start the thread
            self.processing_thread.start()
            
            # Start update timer
            self.update_timer.start(500)
        
        except Exception as e:
            self.logger.error(f"Error starting processing: {e}")
            self.show_error_message("Processing Error", str(e))
            self.is_processing = False
            self.progress_bar.setVisible(False) if self.progress_bar else None
            self.update_button_states()
    
    def on_stop_button_clicked(self):
        """Handle stop button click."""
        try:
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
        except Exception as e:
            self.logger.error(f"Error stopping processing: {e}")
            self.show_error_message("Stop Error", f"Error stopping processing: {str(e)}")
    
    def on_file_processed(self):
        """Handle file processed callback."""
        self.processed_files_count += 1
    
    def on_file_processed_signal(self, filename: str):
        """Handle file processed signal from thread."""
        self.processed_files_count += 1
        if self.status_bar:
            self.status_bar.showMessage(f"Processing: {filename}")
    
    def on_preview_finished(self, summary: Dict[str, Any]):
        """Handle preview completion."""
        try:
            self.is_processing = False
            self.update_button_states()
            if self.progress_bar:
                self.progress_bar.setVisible(False)
            self.update_timer.stop()
            
            # Display preview results
            if summary:
                preview_text = "Preview Results:\n\n"
                for key, value in summary.items():
                    preview_text += f"{key.replace('_', ' ').title()}: {value}\n"
            else:
                preview_text = "No preview results available.\n"
            
            if self.preview_text_edit:
                self.preview_text_edit.setPlainText(preview_text)
            self.status_update.emit("Preview completed")
            
        except Exception as e:
            self.logger.error(f"Error handling preview completion: {e}")
            self.show_error_message("Preview Error", f"Error displaying preview results: {str(e)}")
    
    def on_processing_finished(self, summary: Dict[str, Any]):
        """Handle processing completion."""
        try:
            self.is_processing = False
            self.update_button_states()
            if self.progress_bar:
                self.progress_bar.setVisible(False)
            self.update_timer.stop()
            
            # Display results
            if summary:
                result_text = "Processing Results:\n\n"
                for key, value in summary.items():
                    result_text += f"{key.replace('_', ' ').title()}: {value}\n"
            else:
                result_text = "No processing results available.\n"
            
            if self.after_text_edit:
                self.after_text_edit.setPlainText(result_text)
            self.status_update.emit("Processing completed successfully")
            
            # Show completion message
            QMessageBox.information(
                self, "Processing Complete",
                f"File organization completed!\n\nFiles processed: {self.processed_files_count}"
            )
            
        except Exception as e:
            self.logger.error(f"Error handling processing completion: {e}")
            self.show_error_message("Processing Error", f"Error displaying processing results: {str(e)}")
    
    def on_error_occurred(self, error_message: str):
        """Handle error from processing thread."""
        try:
            self.is_processing = False
            self.update_button_states()
            if self.progress_bar:
                self.progress_bar.setVisible(False)
            self.update_timer.stop()
            
            self.logger.error(f"Processing error: {error_message}")
            self.show_error_message("Processing Error", error_message)
            self.status_update.emit(f"Error: {error_message}")
        except Exception as e:
            self.logger.error(f"Error handling error: {e}")
            # Fallback error handling
            try:
                QMessageBox.critical(self, "Critical Error", f"Multiple errors occurred: {error_message}")
            except:
                pass  # Last resort - prevent infinite error loops
    
    def update_status_message(self, message: str):
        """Update status message."""
        self.status_label.setText(message)
        self.status_bar.showMessage(message)
    
    def update_progress(self, progress: int):
        """Update progress bar."""
        self.progress_bar.setValue(progress)
    
    def update_ui(self):
        """Periodic UI update."""
        try:
            if self.is_processing:
                # Update progress based on processed files
                if self.total_files_count > 0:
                    progress = min(100, int((self.processed_files_count / self.total_files_count) * 100))
                    self.progress_update.emit(progress)
        except Exception as e:
            self.logger.warning(f"Error in periodic UI update: {e}")
    
    def show_error_message(self, title: str, message: str):
        """Show error message dialog."""
        QMessageBox.critical(self, title, message)
    
    def show_warning_message(self, title: str, message: str):
        """Show warning message dialog."""
        QMessageBox.warning(self, title, message)
    
    def create_toolbar(self):
        """Create the main toolbar."""
        toolbar = self.addToolBar('Main')
        toolbar.setMovable(False)
        
        # Add common actions to toolbar
        select_action = toolbar.addAction('📂 Select')
        select_action.triggered.connect(self.on_select_folders_button_clicked)
        
        preview_action = toolbar.addAction('🔍 Preview')
        preview_action.triggered.connect(self.on_preview_button_clicked)
        
        start_action = toolbar.addAction('▶️ Start')
        start_action.triggered.connect(self.on_start_processing_button_clicked)
        
        stop_action = toolbar.addAction('⏹️ Stop')
        stop_action.triggered.connect(self.on_stop_button_clicked)
        
        toolbar.addSeparator()
        
        # Theme toggle buttons
        light_action = toolbar.addAction('☀️ Light')
        light_action.triggered.connect(lambda: self.set_theme('light'))
        
        dark_action = toolbar.addAction('🌙 Dark')
        dark_action.triggered.connect(lambda: self.set_theme('dark'))
        
        toolbar.addSeparator()
        
        # GPU controls
        gpu_settings_action = toolbar.addAction('⚙️ GPU')
        gpu_settings_action.triggered.connect(self.show_gpu_settings)
    
    def create_dock_widgets(self):
        """Create dockable widgets for enhanced features."""
        # Use global variable with explicit check
        global ENHANCED_WIDGETS_AVAILABLE
        if not globals().get('ENHANCED_WIDGETS_AVAILABLE', False):
            return
            
        try:
            # GPU Status Dock
            gpu_dock = QDockWidget('GPU Status', self)
            self.gpu_status_widget = GPUStatusWidget()
            gpu_dock.setWidget(self.gpu_status_widget)
            self.addDockWidget(Qt.RightDockWidgetArea, gpu_dock)
            
            # Performance Monitor Dock
            performance_dock = QDockWidget('Performance Monitor', self)
            self.performance_monitor = PerformanceMonitorWidget()
            performance_dock.setWidget(self.performance_monitor)
            self.addDockWidget(Qt.RightDockWidgetArea, performance_dock)
            
            # Advanced Filters Dock
            filters_dock = QDockWidget('Advanced Filters', self)
            self.advanced_filters_widget = AdvancedFiltersWidget()
            filters_dock.setWidget(self.advanced_filters_widget)
            self.addDockWidget(Qt.LeftDockWidgetArea, filters_dock)
            
            # Store dock references for toggling
            self.gpu_dock = gpu_dock
            self.performance_dock = performance_dock
            self.filters_dock = filters_dock
            
        except Exception as e:
            self.logger.error(f"Error creating dock widgets: {e}")
            # Disable enhanced features if creation fails
            ENHANCED_WIDGETS_AVAILABLE = False
    
    def create_enhanced_central_widget(self):
        """Create enhanced central widget with new components."""
        central_widget = QWidget(self)
        central_widget.setAcceptDrops(True)
        self.setCentralWidget(central_widget)
        
        # Create main layout with splitter
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        central_widget.setLayout(main_layout)
        
        # Create horizontal splitter for main content
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Drag & Drop and Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Add drag-drop widget (if available)
        if ENHANCED_WIDGETS_AVAILABLE:
            try:
                self.drag_drop_widget = DragDropWidget()
                left_layout.addWidget(self.drag_drop_widget)
            except Exception as e:
                self.logger.error(f"Error creating drag-drop widget: {e}")
                self.drag_drop_widget = None
        
        # Add original control panel (smaller now)
        control_panel = self.create_control_panel()
        left_layout.addWidget(control_panel)
        
        # Add progress section
        progress_section = self.create_progress_section()
        left_layout.addWidget(progress_section)
        
        main_splitter.addWidget(left_widget)
        
        # Right side - Enhanced Preview and Tabs
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Create enhanced tab widget
        enhanced_tab_widget = self.create_enhanced_tab_widget()
        right_layout.addWidget(enhanced_tab_widget)
        
        main_splitter.addWidget(right_widget)
        
        # Set splitter proportions (left smaller, right larger)
        main_splitter.setSizes([400, 800])
        
        main_layout.addWidget(main_splitter)
    
    def create_enhanced_tab_widget(self) -> QTabWidget:
        """Create enhanced tabbed interface."""
        tab_widget = QTabWidget()
        
        # Enhanced Preview tab with new preview widget
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        
        if ENHANCED_WIDGETS_AVAILABLE:
            try:
                self.preview_widget = PreviewWidget()
                preview_layout.addWidget(self.preview_widget)
            except Exception as e:
                self.logger.error(f"Error creating preview widget: {e}")
                self.preview_widget = None
                # Add fallback text
                fallback_label = QLabel("Enhanced preview not available - using basic preview")
                preview_layout.addWidget(fallback_label)
        
        tab_widget.addTab(preview_tab, "🔍 Smart Preview")
        
        # Keep original preview for compatibility
        original_preview_tab = QWidget()
        original_preview_layout = QVBoxLayout(original_preview_tab)
        
        self.preview_text_edit = QTextEdit()
        self.preview_text_edit.setReadOnly(True)
        self.preview_text_edit.setFont(QFont("Consolas", 10))
        original_preview_layout.addWidget(self.preview_text_edit)
        
        tab_widget.addTab(original_preview_tab, "📝 Text Preview")
        
        # Before/After comparison tab (enhanced)
        comparison_tab = QWidget()
        comparison_layout = QVBoxLayout(comparison_tab)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Before section
        before_group = QGroupBox("📁 Current Structure")
        before_layout = QVBoxLayout(before_group)
        self.before_text_edit = QTextEdit()
        self.before_text_edit.setReadOnly(True)
        self.before_text_edit.setFont(QFont("Consolas", 9))
        before_layout.addWidget(self.before_text_edit)
        splitter.addWidget(before_group)
        
        # After section
        after_group = QGroupBox("🎯 Organized Structure")
        after_layout = QVBoxLayout(after_group)
        self.after_text_edit = QTextEdit()
        self.after_text_edit.setReadOnly(True)
        self.after_text_edit.setFont(QFont("Consolas", 9))
        after_layout.addWidget(self.after_text_edit)
        splitter.addWidget(after_group)
        
        comparison_layout.addWidget(splitter)
        tab_widget.addTab(comparison_tab, "📊 Before/After")
        
        # Theme settings tab
        if ENHANCED_WIDGETS_AVAILABLE and self.theme_manager:
            try:
                self.theme_toggle_widget = ThemeToggleWidget(self.theme_manager)
                tab_widget.addTab(self.theme_toggle_widget, "🎨 Themes")
            except Exception as e:
                self.logger.error(f"Error creating theme widget: {e}")
                self.theme_toggle_widget = None
        
        return tab_widget
    
    def connect_enhanced_signals(self):
        """Connect signals for enhanced widgets."""
        try:
            # Drag-drop widget signals
            if self.drag_drop_widget:
                self.drag_drop_widget.files_changed.connect(self.on_drag_drop_files_changed)
                self.drag_drop_widget.start_processing.connect(self.on_drag_drop_start_processing)
            
            # GPU status widget signals
            if self.gpu_status_widget:
                self.gpu_status_widget.gpu_settings_requested.connect(self.show_gpu_settings)
                self.gpu_status_widget.gpu_benchmark_requested.connect(self.run_gpu_benchmark)
                self.gpu_status_widget.gpu_toggle_requested.connect(self.on_gpu_toggle)
            
            # Preview widget signals
            if self.preview_widget:
                self.preview_widget.apply_organization.connect(self.apply_preview_organization)
                self.preview_widget.preview_generated.connect(self.on_preview_stats_updated)
            
            # Theme widget signals
            if self.theme_toggle_widget:
                self.theme_toggle_widget.theme_changed.connect(self.on_theme_changed)
            
            # Performance monitor
            if self.performance_monitor:
                # Connect to processing events
                pass
            
        except Exception as e:
            self.logger.error(f"Error connecting enhanced signals: {e}")
    
    @pyqtSlot(list)
    def on_drag_drop_files_changed(self, files: List[str]):
        """Handle files changed from drag-drop widget."""
        self.selected_folders = [f for f in files if os.path.isdir(f)]
        if self.selected_folders:
            folder_names = [os.path.basename(path) for path in self.selected_folders]
            self.status_update.emit(f"Selected from drag-drop: {', '.join(folder_names)}")
            self.update_button_states()
            self.update_before_structure()
    
    @pyqtSlot(list)
    def on_drag_drop_start_processing(self, files: List[str]):
        """Handle start processing from drag-drop widget."""
        self.selected_folders = [f for f in files if os.path.isdir(f)]
        if self.selected_folders:
            # Auto-start processing from drag-drop
            self.on_start_processing_button_clicked()
    
    @pyqtSlot()
    def show_gpu_settings(self):
        """Show GPU settings dialog."""
        try:
            if not hasattr(self, 'gpu_settings_dialog') or self.gpu_settings_dialog is None:
                gpu_config = self.gpu_status_widget.get_gpu_config() if self.gpu_status_widget else {}
                self.gpu_settings_dialog = GPUSettingsDialog(gpu_config, self)
                self.gpu_settings_dialog.settings_applied.connect(self.on_gpu_settings_applied)
            
            self.gpu_settings_dialog.show()
            self.gpu_settings_dialog.raise_()
            self.gpu_settings_dialog.activateWindow()
            
        except Exception as e:
            self.logger.error(f"Error showing GPU settings: {e}")
            QMessageBox.warning(self, "GPU Settings", f"Error opening GPU settings: {str(e)}")
    
    @pyqtSlot()
    def run_gpu_benchmark(self):
        """Run GPU benchmark."""
        try:
            self.show_gpu_settings()
            if self.gpu_settings_dialog:
                # Switch to benchmark tab and run
                self.gpu_settings_dialog.tab_widget.setCurrentIndex(3)  # Benchmark tab
                self.gpu_settings_dialog.run_benchmark()
        except Exception as e:
            self.logger.error(f"Error running GPU benchmark: {e}")
            QMessageBox.warning(self, "Benchmark Error", f"Error running benchmark: {str(e)}")
    
    @pyqtSlot(bool)
    def on_gpu_toggle(self, enabled: bool):
        """Handle GPU toggle."""
        self.logger.info(f"GPU acceleration {'enabled' if enabled else 'disabled'}")
        # Update app configuration
        if 'gpu_config' not in self.app_config:
            self.app_config['gpu_config'] = {}
        self.app_config['gpu_config']['enable_gpu'] = enabled
    
    @pyqtSlot(dict)
    def on_gpu_settings_applied(self, settings: Dict[str, Any]):
        """Handle GPU settings application."""
        self.logger.info(f"GPU settings applied: {settings}")
        # Update app configuration with new GPU settings
        self.app_config['gpu_config'] = settings
        
        # Update GPU status widget if available
        if self.gpu_status_widget:
            # Refresh GPU status
            self.gpu_status_widget.initialize_gpu()
    
    @pyqtSlot(list)
    def apply_preview_organization(self, preview_items: List[Any]):
        """Apply organization from preview widget."""
        try:
            # This would implement the actual file organization
            # based on the preview results
            self.logger.info(f"Applying organization for {len(preview_items)} items")
            # Implementation would go here
        except Exception as e:
            self.logger.error(f"Error applying preview organization: {e}")
    
    @pyqtSlot(dict)
    def on_preview_stats_updated(self, stats: Dict[str, Any]):
        """Handle preview statistics update."""
        try:
            # Update performance monitor with preview stats
            if self.performance_monitor:
                # Convert preview stats to performance stats format
                perf_stats = {
                    'total_files': stats.get('total_files', 0),
                    'conflicts': stats.get('conflicts', 0)
                }
                # This could be enhanced to show preview-specific metrics
        except Exception as e:
            self.logger.error(f"Error updating preview stats: {e}")
    
    @pyqtSlot(str)
    def on_theme_changed(self, theme_name: str):
        """Handle theme change."""
        try:
            self.logger.info(f"Theme changed to: {theme_name}")
            # Theme is already applied by the theme manager
            # Could add additional theme-specific logic here
        except Exception as e:
            self.logger.error(f"Error handling theme change: {e}")
    
    def set_theme(self, theme_name: str):
        """Set application theme."""
        from PyQt5.QtWidgets import QApplication
        if self.theme_manager.apply_theme(QApplication.instance(), theme_name):
            self.logger.info(f"Applied theme: {theme_name}")
    
    @pyqtSlot()
    def toggle_gpu_panel(self):
        """Toggle GPU status panel visibility."""
        if hasattr(self, 'gpu_dock'):
            self.gpu_dock.setVisible(not self.gpu_dock.isVisible())
    
    @pyqtSlot()
    def toggle_performance_panel(self):
        """Toggle performance monitor panel visibility."""
        if hasattr(self, 'performance_dock'):
            self.performance_dock.setVisible(not self.performance_dock.isVisible())
    
    @pyqtSlot()
    def toggle_filters_panel(self):
        """Toggle advanced filters panel visibility."""
        if hasattr(self, 'filters_dock'):
            self.filters_dock.setVisible(not self.filters_dock.isVisible())
    
    def show_theme_settings(self):
        """Show theme settings in a dialog."""
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout
            dialog = QDialog(self)
            dialog.setWindowTitle("Theme Settings")
            dialog.resize(500, 600)
            
            layout = QVBoxLayout(dialog)
            theme_widget = ThemeToggleWidget(self.theme_manager, dialog)
            layout.addWidget(theme_widget)
            
            dialog.exec_()
        except Exception as e:
            self.logger.error(f"Error showing theme settings: {e}")
    
    def show_config_dialog(self):
        """Show configuration dialog."""
        QMessageBox.information(
            self, "Configuration", 
            "Enhanced Configuration\n\n"
            "Use the menu options to configure:\n"
            "• GPU Settings (Settings → GPU Settings)\n"
            "• Theme Settings (Settings → Theme Settings)\n"
            "• View Panels (View menu)\n\n"
            "All settings are automatically saved."
        )
    
    def show_about_dialog(self):
        """Show about dialog."""
        enhanced_features = ""
        if ENHANCED_WIDGETS_AVAILABLE:
            enhanced_features = (
                "\n🚀 Enhanced Features:\n"
                "• GPU-accelerated file processing\n"
                "• Real-time performance monitoring\n"
                "• Advanced filtering and preview\n"
                "• Drag-and-drop interface\n"
                "• Dark/Light theme support\n"
                "• Interactive organization preview\n"
            )
        
        QMessageBox.about(
            self, "About FileOrganizer",
            f"FileOrganizer v3.0 - Enhanced Edition\n\n"
            f"A powerful Python application for organizing files with GPU acceleration.\n\n"
            f"Core Features:\n"
            f"• Organize files by type, size, and metadata\n"
            f"• Preview changes before applying\n"
            f"• Handle duplicates intelligently\n"
            f"• Recursive folder processing\n"
            f"• Multi-threaded processing\n"
            f"{enhanced_features}\n"
            f"Built with PyQt5, Python, and modern GPU acceleration libraries."
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
        try:
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
            
            # Stop timers
            if hasattr(self, 'update_timer') and self.update_timer:
                self.update_timer.stop()
            
            event.accept()
        except Exception as e:
            self.logger.error(f"Error during close event: {e}")
            event.accept()  # Accept anyway to prevent hanging
