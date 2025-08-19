"""
Drag and Drop Interface Widget for FileOrganizer

Modern, intuitive drag-and-drop functionality for file and folder selection.
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QListWidget, QListWidgetItem, 
                           QFrame, QGroupBox, QGridLayout, QProgressBar,
                           QFileDialog, QMessageBox, QScrollArea,
                           QSizePolicy, QApplication, QMenu, QAction)
from PyQt5.QtCore import (Qt, pyqtSignal, QMimeData, QUrl, QTimer, 
                         QPropertyAnimation, QEasingCurve, QRect, pyqtSlot)
from PyQt5.QtGui import (QPainter, QColor, QPen, QBrush, QFont, QPixmap, 
                        QDragEnterEvent, QDropEvent, QPalette, QLinearGradient,
                        QIcon, QMovie)
from typing import List, Dict, Any, Optional, Set
import logging
import mimetypes


class AnimatedDropZone(QFrame):
    """Animated drop zone with visual feedback"""
    
    files_dropped = pyqtSignal(list)  # List of file/directory paths
    
    def __init__(self, title: str = "Drop Files Here", subtitle: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self.is_dragging = False
        self.animation_progress = 0.0
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
        self.setup_animations()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
    
    def setup_ui(self):
        """Setup the drop zone UI"""
        self.setMinimumSize(300, 200)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setLineWidth(2)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Set base style
        self.setStyleSheet("""
            AnimatedDropZone {
                border: 2px dashed #aaa;
                border-radius: 10px;
                background-color: #f8f9fa;
            }
            AnimatedDropZone:hover {
                border-color: #007acc;
                background-color: #e3f2fd;
            }
        """)
    
    def setup_animations(self):
        """Setup animation timer for visual effects"""
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.setInterval(50)  # 20 FPS
    
    def paintEvent(self, event):
        """Custom paint event for the drop zone"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget rect
        rect = self.rect()
        
        # Background gradient
        if self.is_dragging:
            gradient = QLinearGradient(0, 0, 0, rect.height())
            gradient.setColorAt(0, QColor(227, 242, 253, 200))
            gradient.setColorAt(1, QColor(187, 222, 251, 200))
            painter.fillRect(rect, QBrush(gradient))
        else:
            painter.fillRect(rect, QColor(248, 249, 250))
        
        # Border
        border_color = QColor(0, 122, 204) if self.is_dragging else QColor(170, 170, 170)
        painter.setPen(QPen(border_color, 2, Qt.DashLine))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 10, 10)
        
        # Main icon/text area
        center_x = rect.width() // 2
        center_y = rect.height() // 2
        
        # Draw upload icon (simplified folder icon)
        icon_size = 64
        if self.is_dragging:
            icon_size = int(64 + 16 * self.animation_progress)
        
        icon_rect = QRect(center_x - icon_size//2, center_y - icon_size//2 - 20, 
                         icon_size, icon_size)
        
        # Folder icon
        painter.setBrush(QBrush(QColor(100, 181, 246) if self.is_dragging else QColor(158, 158, 158)))
        painter.setPen(QPen(QColor(33, 150, 243) if self.is_dragging else QColor(117, 117, 117), 2))
        
        # Draw folder shape
        folder_rect = icon_rect.adjusted(8, 16, -8, -8)
        tab_rect = QRect(folder_rect.left(), folder_rect.top() - 8, 
                        folder_rect.width() // 3, 8)
        
        painter.drawRect(tab_rect)
        painter.drawRect(folder_rect)
        
        # Title text
        painter.setPen(QPen(QColor(33, 33, 33)))
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        painter.setFont(title_font)
        
        title_rect = QRect(0, center_y + 40, rect.width(), 30)
        painter.drawText(title_rect, Qt.AlignCenter, self.title)
        
        # Subtitle text
        if self.subtitle:
            painter.setPen(QPen(QColor(117, 117, 117)))
            subtitle_font = QFont("Segoe UI", 10)
            painter.setFont(subtitle_font)
            
            subtitle_rect = QRect(0, center_y + 70, rect.width(), 20)
            painter.drawText(subtitle_rect, Qt.AlignCenter, self.subtitle)
        
        # Animated elements during drag
        if self.is_dragging:
            # Pulsing border effect
            pulse_alpha = int(100 + 55 * self.animation_progress)
            painter.setPen(QPen(QColor(0, 122, 204, pulse_alpha), 3))
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 12, 12)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            # Check if dropped items are files or directories
            urls = event.mimeData().urls()
            valid_items = []
            
            for url in urls:
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if os.path.exists(path):
                        valid_items.append(path)
            
            if valid_items:
                event.acceptProposedAction()
                self.is_dragging = True
                self.start_drag_animation()
                self.update()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """Handle drag move event"""
        if self.is_dragging:
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        self.is_dragging = False
        self.stop_drag_animation()
        self.update()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = []
            
            for url in urls:
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if os.path.exists(path):
                        file_paths.append(path)
            
            if file_paths:
                self.logger.info(f"Files dropped: {file_paths}")
                self.files_dropped.emit(file_paths)
                event.acceptProposedAction()
            else:
                event.ignore()
        
        self.is_dragging = False
        self.stop_drag_animation()
        self.update()
    
    def start_drag_animation(self):
        """Start drag animation"""
        if not self.animation_timer.isActive():
            self.animation_progress = 0.0
            self.animation_timer.start()
    
    def stop_drag_animation(self):
        """Stop drag animation"""
        self.animation_timer.stop()
        self.animation_progress = 0.0
    
    def update_animation(self):
        """Update animation frame"""
        self.animation_progress += 0.1
        if self.animation_progress >= 1.0:
            self.animation_progress = 0.0
        self.update()


class FileListItem(QWidget):
    """Custom widget for displaying files/folders in the list"""
    
    remove_requested = pyqtSignal(str)  # File path to remove
    
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the file item UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # File info
        file_info = Path(self.file_path)
        
        # Icon based on file type
        icon_label = QLabel()
        icon_text = self.get_file_icon(file_info)
        icon_label.setText(icon_text)
        icon_label.setFont(QFont("Segoe UI", 14))
        icon_label.setFixedWidth(30)
        layout.addWidget(icon_label)
        
        # File name and details
        details_layout = QVBoxLayout()
        
        # File name
        name_label = QLabel(file_info.name)
        name_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        details_layout.addWidget(name_label)
        
        # File details
        details_text = self.get_file_details(file_info)
        details_label = QLabel(details_text)
        details_label.setFont(QFont("Segoe UI", 8))
        details_label.setStyleSheet("color: #666;")
        details_layout.addWidget(details_label)
        
        layout.addLayout(details_layout)
        layout.addStretch()
        
        # Remove button
        remove_button = QPushButton("✕")
        remove_button.setFixedSize(24, 24)
        remove_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 12px;
                background-color: #ff4444;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        """)
        remove_button.clicked.connect(lambda: self.remove_requested.emit(self.file_path))
        layout.addWidget(remove_button)
    
    def get_file_icon(self, file_path: Path) -> str:
        """Get appropriate icon for file type"""
        if file_path.is_dir():
            return "📁"
        
        suffix = file_path.suffix.lower()
        
        # Image files
        if suffix in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return "🖼️"
        
        # Video files
        elif suffix in ['.mp4', '.avi', '.mov', '.wmv']:
            return "🎬"
        
        # Audio files
        elif suffix in ['.mp3', '.wav', '.flac', '.aac']:
            return "🎵"
        
        # Document files
        elif suffix in ['.pdf', '.doc', '.docx', '.txt']:
            return "📄"
        
        # Archive files
        elif suffix in ['.zip', '.rar', '.7z']:
            return "📦"
        
        # Code files
        elif suffix in ['.py', '.js', '.html', '.css']:
            return "💻"
        
        else:
            return "📄"
    
    def get_file_details(self, file_path: Path) -> str:
        """Get file details string"""
        try:
            if file_path.is_dir():
                # Count items in directory
                try:
                    item_count = len(list(file_path.iterdir()))
                    return f"Directory • {item_count} items • {file_path.parent}"
                except:
                    return f"Directory • {file_path.parent}"
            else:
                # File size and parent directory
                size = file_path.stat().st_size
                size_str = self.format_file_size(size)
                return f"{size_str} • {file_path.parent}"
        except:
            return str(file_path.parent)
    
    def format_file_size(self, size: int) -> str:
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class DragDropWidget(QWidget):
    """Main drag and drop widget with file list and controls"""
    
    files_changed = pyqtSignal(list)  # List of selected files/directories
    start_processing = pyqtSignal(list)  # Signal to start processing files
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.selected_paths = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the drag and drop interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("File and Folder Selection")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Browse button
        self.browse_button = QPushButton("📂 Browse...")
        self.browse_button.setMinimumWidth(100)
        self.browse_button.clicked.connect(self.browse_files)
        header_layout.addWidget(self.browse_button)
        
        layout.addLayout(header_layout)
        
        # Drop zone
        self.drop_zone = AnimatedDropZone(
            title="Drop Files or Folders Here",
            subtitle="Or click 'Browse' to select files manually"
        )
        self.drop_zone.files_dropped.connect(self.add_files)
        layout.addWidget(self.drop_zone)
        
        # Selected files list
        files_group = QGroupBox("Selected Files and Folders")
        files_layout = QVBoxLayout(files_group)
        
        # File list scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(150)
        self.scroll_area.setMaximumHeight(300)
        
        # Container for file items
        self.files_container = QWidget()
        self.files_layout = QVBoxLayout(self.files_container)
        self.files_layout.addStretch()
        
        self.scroll_area.setWidget(self.files_container)
        files_layout.addWidget(self.scroll_area)
        
        # File list controls
        controls_layout = QHBoxLayout()
        
        self.file_count_label = QLabel("No files selected")
        self.file_count_label.setFont(QFont("Segoe UI", 9))
        controls_layout.addWidget(self.file_count_label)
        
        controls_layout.addStretch()
        
        self.clear_button = QPushButton("Clear All")
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(self.clear_files)
        controls_layout.addWidget(self.clear_button)
        
        files_layout.addLayout(controls_layout)
        
        layout.addWidget(files_group)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        # Processing options
        self.recursive_checkbox = QCheckBox("Include subdirectories recursively")
        self.recursive_checkbox.setChecked(True)
        action_layout.addWidget(self.recursive_checkbox)
        
        action_layout.addStretch()
        
        # Start processing button
        self.process_button = QPushButton("🚀 Start Organization")
        self.process_button.setEnabled(False)
        self.process_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.process_button.clicked.connect(self.start_processing_files)
        action_layout.addWidget(self.process_button)
        
        layout.addLayout(action_layout)
        
        # Initially hide the files group
        files_group.setVisible(False)
        self.files_group = files_group
    
    @pyqtSlot()
    def browse_files(self):
        """Open file browser dialog"""
        # Create menu for browse options
        menu = QMenu(self)
        
        # Add files action
        add_files_action = QAction("Add Files...", self)
        add_files_action.triggered.connect(self.browse_files_dialog)
        menu.addAction(add_files_action)
        
        # Add folder action
        add_folder_action = QAction("Add Folder...", self)
        add_folder_action.triggered.connect(self.browse_folder_dialog)
        menu.addAction(add_folder_action)
        
        # Show menu at button position
        menu.exec_(self.browse_button.mapToGlobal(self.browse_button.rect().bottomLeft()))
    
    @pyqtSlot()
    def browse_files_dialog(self):
        """Open file selection dialog"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Files to Organize",
            os.path.expanduser("~"),
            "All Files (*.*)"
        )
        
        if files:
            self.add_files(files)
    
    @pyqtSlot()
    def browse_folder_dialog(self):
        """Open folder selection dialog"""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder to Organize",
            os.path.expanduser("~")
        )
        
        if folder:
            self.add_files([folder])
    
    @pyqtSlot(list)
    def add_files(self, file_paths: List[str]):
        """Add files/folders to the selection list"""
        added_count = 0
        
        for path in file_paths:
            if path not in self.selected_paths:
                self.selected_paths.append(path)
                self.add_file_item(path)
                added_count += 1
        
        if added_count > 0:
            self.update_ui_state()
            self.logger.info(f"Added {added_count} new files/folders")
        else:
            QMessageBox.information(self, "No New Files", 
                                  "All selected files/folders are already in the list.")
    
    def add_file_item(self, file_path: str):
        """Add a file item to the visual list"""
        # Create file item widget
        file_item = FileListItem(file_path)
        file_item.remove_requested.connect(self.remove_file)
        
        # Insert before the stretch at the end
        self.files_layout.insertWidget(self.files_layout.count() - 1, file_item)
    
    @pyqtSlot(str)
    def remove_file(self, file_path: str):
        """Remove a file from the selection"""
        if file_path in self.selected_paths:
            self.selected_paths.remove(file_path)
            
            # Remove from UI
            for i in range(self.files_layout.count()):
                item = self.files_layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if isinstance(widget, FileListItem) and widget.file_path == file_path:
                        widget.deleteLater()
                        break
            
            self.update_ui_state()
            self.logger.info(f"Removed file: {file_path}")
    
    @pyqtSlot()
    def clear_files(self):
        """Clear all selected files"""
        reply = QMessageBox.question(self, "Clear Files", 
                                   "Remove all selected files and folders from the list?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.selected_paths.clear()
            
            # Clear UI items
            for i in reversed(range(self.files_layout.count())):
                item = self.files_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), FileListItem):
                    item.widget().deleteLater()
            
            self.update_ui_state()
            self.logger.info("Cleared all selected files")
    
    def update_ui_state(self):
        """Update UI state based on selected files"""
        file_count = len(self.selected_paths)
        
        # Update file count label
        if file_count == 0:
            self.file_count_label.setText("No files selected")
            self.files_group.setVisible(False)
        elif file_count == 1:
            self.file_count_label.setText("1 item selected")
            self.files_group.setVisible(True)
        else:
            self.file_count_label.setText(f"{file_count} items selected")
            self.files_group.setVisible(True)
        
        # Enable/disable buttons
        has_files = file_count > 0
        self.clear_button.setEnabled(has_files)
        self.process_button.setEnabled(has_files)
        
        # Emit files changed signal
        self.files_changed.emit(self.selected_paths[:])
    
    @pyqtSlot()
    def start_processing_files(self):
        """Start processing the selected files"""
        if not self.selected_paths:
            QMessageBox.warning(self, "No Files Selected", 
                              "Please select files or folders to organize.")
            return
        
        # Validate that all paths still exist
        valid_paths = []
        invalid_paths = []
        
        for path in self.selected_paths:
            if os.path.exists(path):
                valid_paths.append(path)
            else:
                invalid_paths.append(path)
        
        if invalid_paths:
            QMessageBox.warning(self, "Invalid Paths", 
                              f"The following paths no longer exist and will be skipped:\\n\\n" +
                              "\\n".join(invalid_paths))
            
            # Remove invalid paths
            for path in invalid_paths:
                self.remove_file(path)
        
        if valid_paths:
            processing_config = {
                'recursive': self.recursive_checkbox.isChecked()
            }
            
            self.logger.info(f"Starting processing of {len(valid_paths)} paths")
            self.start_processing.emit(valid_paths)
        else:
            QMessageBox.warning(self, "No Valid Files", 
                              "No valid files or folders found to process.")
    
    def get_selected_paths(self) -> List[str]:
        """Get list of selected file/folder paths"""
        return self.selected_paths[:]
    
    def set_selected_paths(self, paths: List[str]):
        """Set the selected paths (used for loading saved sessions)"""
        self.clear_files()
        if paths:
            self.add_files(paths)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Create test window
    window = DragDropWidget()
    window.setWindowTitle("Drag and Drop Interface Test")
    window.resize(600, 700)
    window.show()
    
    # Connect to signals
    def on_files_changed(files):
        print(f"Files changed: {files}")
    
    def on_start_processing(files):
        print(f"Start processing: {files}")
    
    window.files_changed.connect(on_files_changed)
    window.start_processing.connect(on_start_processing)
    
    sys.exit(app.exec_())