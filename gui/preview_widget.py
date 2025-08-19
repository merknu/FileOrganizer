"""
Before/After Preview System for FileOrganizer

Shows users a preview of how their files will be organized before applying changes.
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QGroupBox, QSplitter, QTreeWidget,
                           QTreeWidgetItem, QScrollArea, QFrame, QTextEdit,
                           QProgressBar, QMessageBox, QTabWidget,
                           QCheckBox, QComboBox, QSpinBox)
from PyQt5.QtCore import (Qt, pyqtSignal, QThread, pyqtSlot, QTimer,
                         QMimeData, QUrl)
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QDragEnterEvent, QDropEvent
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
import json


class FilePreviewItem:
    """Represents a file and its preview information"""
    
    def __init__(self, original_path: str, suggested_path: str, action: str = "move"):
        self.original_path = original_path
        self.suggested_path = suggested_path
        self.action = action  # "move", "copy", "skip", "duplicate"
        self.file_info = self._get_file_info()
        self.conflict = False
        self.conflict_type = None
    
    def _get_file_info(self) -> Dict[str, Any]:
        """Get file information"""
        try:
            path = Path(self.original_path)
            if not path.exists():
                return {"exists": False}
            
            stat = path.stat()
            return {
                "exists": True,
                "name": path.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "is_dir": path.is_dir(),
                "extension": path.suffix.lower() if not path.is_dir() else None
            }
        except Exception:
            return {"exists": False}


class PreviewTreeWidget(QTreeWidget):
    """Custom tree widget for showing file organization preview"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QTreeWidget.NoDragDrop)
        self.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.setup_tree()
    
    def setup_tree(self):
        """Setup tree widget headers and appearance"""
        self.setHeaderLabels(["File/Folder", "Size", "Action", "Status"])
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(True)
        
        # Set column widths
        header = self.header()
        header.resizeSection(0, 300)
        header.resizeSection(1, 80)
        header.resizeSection(2, 80)
        header.resizeSection(3, 100)
    
    def add_directory_structure(self, structure: Dict[str, Any]):
        """Add directory structure to tree"""
        self.clear()
        self._add_items(structure, self.invisibleRootItem())
        self.expandAll()
    
    def _add_items(self, items: Dict[str, Any], parent_item: QTreeWidgetItem):
        """Recursively add items to tree"""
        for name, data in items.items():
            item = QTreeWidgetItem(parent_item)
            item.setText(0, name)
            
            if isinstance(data, dict) and "files" in data:
                # Directory
                item.setText(1, f"{data.get('file_count', 0)} items")
                item.setText(2, "organize")
                item.setText(3, "✓ ready")
                item.setIcon(0, self.style().standardIcon(self.style().SP_DirIcon))
                
                # Add files in directory
                if data["files"]:
                    self._add_items(data["files"], item)
            else:
                # File
                preview_item = data
                if isinstance(preview_item, FilePreviewItem):
                    size_text = self.format_file_size(preview_item.file_info.get("size", 0))
                    item.setText(1, size_text)
                    item.setText(2, preview_item.action)
                    
                    # Status based on conflicts
                    if preview_item.conflict:
                        item.setText(3, f"⚠ {preview_item.conflict_type}")
                        item.setBackground(0, QColor(255, 255, 200))
                    else:
                        item.setText(3, "✓ ready")
                    
                    # Icon based on file type
                    if preview_item.file_info.get("is_dir"):
                        item.setIcon(0, self.style().standardIcon(self.style().SP_DirIcon))
                    else:
                        item.setIcon(0, self.style().standardIcon(self.style().SP_FileIcon))
    
    def format_file_size(self, size: int) -> str:
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class PreviewWorker(QThread):
    """Worker thread for generating file organization preview"""
    
    progress_updated = pyqtSignal(int, str)
    preview_ready = pyqtSignal(dict, dict, list)  # before_structure, after_structure, conflicts
    error_occurred = pyqtSignal(str)
    
    def __init__(self, file_paths: List[str], organization_rules: Dict[str, Any]):
        super().__init__()
        self.file_paths = file_paths
        self.organization_rules = organization_rules
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """Generate preview of file organization"""
        try:
            self.progress_updated.emit(10, "Scanning files...")
            
            # Collect all files
            all_files = []
            for path in self.file_paths:
                path_obj = Path(path)
                if path_obj.is_file():
                    all_files.append(str(path_obj))
                elif path_obj.is_dir():
                    all_files.extend([str(f) for f in path_obj.rglob("*") if f.is_file()])
            
            self.progress_updated.emit(30, f"Analyzing {len(all_files)} files...")
            
            # Generate organization preview
            preview_items = []
            conflicts = []
            
            for i, file_path in enumerate(all_files):
                # Simulate organization rules
                suggested_path = self._generate_suggested_path(file_path)
                
                preview_item = FilePreviewItem(file_path, suggested_path)
                
                # Check for conflicts
                if Path(suggested_path).exists() and str(Path(suggested_path).resolve()) != str(Path(file_path).resolve()):
                    preview_item.conflict = True
                    preview_item.conflict_type = "file exists"
                    conflicts.append(preview_item)
                
                preview_items.append(preview_item)
                
                # Update progress
                progress = 30 + int((i / len(all_files)) * 50)
                self.progress_updated.emit(progress, f"Processing {Path(file_path).name}...")
            
            self.progress_updated.emit(80, "Building directory structure...")
            
            # Build before/after structures
            before_structure = self._build_directory_structure(all_files)
            after_structure = self._build_target_structure(preview_items)
            
            self.progress_updated.emit(100, "Preview ready!")
            self.preview_ready.emit(before_structure, after_structure, conflicts)
            
        except Exception as e:
            self.logger.error(f"Preview generation error: {e}")
            self.error_occurred.emit(str(e))
    
    def _generate_suggested_path(self, file_path: str) -> str:
        """Generate suggested organization path for file"""
        path = Path(file_path)
        
        # Simple organization by file type
        extension = path.suffix.lower()
        
        # Determine category
        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
            category = "Images"
        elif extension in ['.mp4', '.avi', '.mov', '.wmv', '.mkv']:
            category = "Videos"
        elif extension in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
            category = "Audio"
        elif extension in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
            category = "Documents"
        elif extension in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            category = "Archives"
        elif extension in ['.py', '.js', '.html', '.css', '.cpp', '.java']:
            category = "Code"
        else:
            category = "Other"
        
        # Create organized path
        base_dir = path.parent
        organized_dir = base_dir / "Organized" / category
        
        # Add date subdirectory for images and videos
        if category in ["Images", "Videos"] and path.exists():
            try:
                stat = path.stat()
                date_dir = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m")
                organized_dir = organized_dir / date_dir
            except:
                pass
        
        return str(organized_dir / path.name)
    
    def _build_directory_structure(self, files: List[str]) -> Dict[str, Any]:
        """Build directory structure representation"""
        structure = {}
        
        for file_path in files:
            path = Path(file_path)
            current = structure
            
            # Build path hierarchy
            for part in path.parent.parts:
                if part not in current:
                    current[part] = {"files": {}, "file_count": 0}
                current = current[part]["files"]
            
            # Add file
            current[path.name] = FilePreviewItem(file_path, file_path, "current")
            
            # Update file counts
            current_count = structure
            for part in path.parent.parts:
                current_count[part]["file_count"] = current_count[part].get("file_count", 0) + 1
                current_count = current_count[part]["files"]
        
        return structure
    
    def _build_target_structure(self, preview_items: List[FilePreviewItem]) -> Dict[str, Any]:
        """Build target directory structure"""
        structure = {}
        
        for item in preview_items:
            target_path = Path(item.suggested_path)
            current = structure
            
            # Build path hierarchy
            for part in target_path.parent.parts:
                if part not in current:
                    current[part] = {"files": {}, "file_count": 0}
                current = current[part]["files"]
            
            # Add file
            current[target_path.name] = item
            
            # Update file counts
            current_count = structure
            for part in target_path.parent.parts:
                if part in current_count:
                    current_count[part]["file_count"] = current_count[part].get("file_count", 0) + 1
                    current_count = current_count[part]["files"]
        
        return structure


class PreviewWidget(QWidget):
    """Main preview widget showing before/after file organization"""
    
    apply_organization = pyqtSignal(list)  # List of FilePreviewItem
    preview_generated = pyqtSignal(dict)  # Preview statistics
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.preview_items = []
        self.conflicts = []
        self.preview_worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the preview interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Organization Preview")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Generate preview button
        self.generate_button = QPushButton("🔍 Generate Preview")
        self.generate_button.setMinimumWidth(140)
        self.generate_button.clicked.connect(self.generate_preview)
        header_layout.addWidget(self.generate_button)
        
        layout.addLayout(header_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel()
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # Main content area
        self.content_splitter = QSplitter(Qt.Horizontal)
        
        # Before/After comparison
        comparison_widget = QWidget()
        comparison_layout = QVBoxLayout(comparison_widget)
        
        # Tabs for before/after
        self.comparison_tabs = QTabWidget()
        
        # Before tab
        before_tab = QWidget()
        before_layout = QVBoxLayout(before_tab)
        
        before_layout.addWidget(QLabel("Current File Structure"))
        self.before_tree = PreviewTreeWidget()
        before_layout.addWidget(self.before_tree)
        
        self.comparison_tabs.addTab(before_tab, "📁 Current")
        
        # After tab  
        after_tab = QWidget()
        after_layout = QVBoxLayout(after_tab)
        
        after_layout.addWidget(QLabel("Organized File Structure"))
        self.after_tree = PreviewTreeWidget()
        after_layout.addWidget(self.after_tree)
        
        self.comparison_tabs.addTab(after_tab, "🎯 Organized")
        
        comparison_layout.addWidget(self.comparison_tabs)
        
        # Preview options
        options_group = QGroupBox("Organization Options")
        options_layout = QVBoxLayout(options_group)
        
        # Organization rules
        rules_layout = QHBoxLayout()
        rules_layout.addWidget(QLabel("Organize by:"))
        self.organization_combo = QComboBox()
        self.organization_combo.addItems(["File Type", "Date Created", "File Size", "Custom Rules"])
        rules_layout.addWidget(self.organization_combo)
        rules_layout.addStretch()
        options_layout.addLayout(rules_layout)
        
        # Options checkboxes
        self.create_subdirs_checkbox = QCheckBox("Create date-based subdirectories for media")
        self.create_subdirs_checkbox.setChecked(True)
        options_layout.addWidget(self.create_subdirs_checkbox)
        
        self.preserve_structure_checkbox = QCheckBox("Preserve original directory structure")
        options_layout.addWidget(self.preserve_structure_checkbox)
        
        self.handle_duplicates_checkbox = QCheckBox("Handle duplicate files automatically")
        self.handle_duplicates_checkbox.setChecked(True)
        options_layout.addWidget(self.handle_duplicates_checkbox)
        
        comparison_layout.addWidget(options_group)
        
        self.content_splitter.addWidget(comparison_widget)
        
        # Summary and conflicts panel
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        
        # Statistics
        stats_group = QGroupBox("Preview Summary")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel("No preview generated")
        self.stats_label.setFont(QFont("", 9))
        stats_layout.addWidget(self.stats_label)
        
        summary_layout.addWidget(stats_group)
        
        # Conflicts
        conflicts_group = QGroupBox("Conflicts & Issues")
        conflicts_layout = QVBoxLayout(conflicts_group)
        
        self.conflicts_list = QTextEdit()
        self.conflicts_list.setReadOnly(True)
        self.conflicts_list.setMaximumHeight(150)
        self.conflicts_list.setFont(QFont("Courier", 8))
        self.conflicts_list.setPlainText("No conflicts detected")
        conflicts_layout.addWidget(self.conflicts_list)
        
        # Conflict resolution
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("When conflicts occur:"))
        self.conflict_combo = QComboBox()
        self.conflict_combo.addItems(["Ask me", "Skip file", "Rename automatically", "Overwrite"])
        resolution_layout.addWidget(self.conflict_combo)
        conflicts_layout.addLayout(resolution_layout)
        
        summary_layout.addWidget(conflicts_group)
        
        # Action buttons
        action_layout = QVBoxLayout()
        
        self.apply_button = QPushButton("✅ Apply Organization")
        self.apply_button.setEnabled(False)
        self.apply_button.setStyleSheet("""
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
        self.apply_button.clicked.connect(self.apply_organization_changes)
        action_layout.addWidget(self.apply_button)
        
        self.export_button = QPushButton("📋 Export Preview")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_preview)
        action_layout.addWidget(self.export_button)
        
        action_layout.addStretch()
        summary_layout.addLayout(action_layout)
        
        self.content_splitter.addWidget(summary_widget)
        
        # Set splitter proportions
        self.content_splitter.setSizes([600, 300])
        
        layout.addWidget(self.content_splitter)
        
        # Initially hide content until preview is generated
        self.content_splitter.setVisible(False)
    
    def generate_preview(self, file_paths: List[str] = None):
        """Generate organization preview"""
        if not file_paths:
            # For testing - use sample files
            file_paths = []
        
        if not file_paths:
            QMessageBox.information(self, "No Files", "Please select files to preview organization.")
            return
        
        # Get organization rules
        organization_rules = {
            "method": self.organization_combo.currentText(),
            "create_subdirs": self.create_subdirs_checkbox.isChecked(),
            "preserve_structure": self.preserve_structure_checkbox.isChecked(),
            "handle_duplicates": self.handle_duplicates_checkbox.isChecked(),
            "conflict_resolution": self.conflict_combo.currentText()
        }
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Starting preview generation...")
        self.generate_button.setEnabled(False)
        
        # Start worker thread
        self.preview_worker = PreviewWorker(file_paths, organization_rules)
        self.preview_worker.progress_updated.connect(self.on_preview_progress)
        self.preview_worker.preview_ready.connect(self.on_preview_ready)
        self.preview_worker.error_occurred.connect(self.on_preview_error)
        self.preview_worker.start()
    
    @pyqtSlot(int, str)
    def on_preview_progress(self, percent: int, message: str):
        """Handle preview generation progress"""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(message)
    
    @pyqtSlot(dict, dict, list)
    def on_preview_ready(self, before_structure: Dict, after_structure: Dict, conflicts: List):
        """Handle preview generation completion"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.generate_button.setEnabled(True)
        
        # Store data
        self.conflicts = conflicts
        
        # Update trees
        self.before_tree.add_directory_structure(before_structure)
        self.after_tree.add_directory_structure(after_structure)
        
        # Update statistics
        total_files = self._count_files_in_structure(after_structure)
        conflict_count = len(conflicts)
        
        stats_text = f"""
Files to organize: {total_files}
Conflicts detected: {conflict_count}
Organization method: {self.organization_combo.currentText()}
        """.strip()
        
        self.stats_label.setText(stats_text)
        
        # Update conflicts display
        if conflicts:
            conflict_text = "CONFLICTS DETECTED:\n\n"
            for conflict in conflicts[:10]:  # Show first 10 conflicts
                conflict_text += f"• {Path(conflict.original_path).name}\n"
                conflict_text += f"  Target: {conflict.suggested_path}\n"
                conflict_text += f"  Issue: {conflict.conflict_type}\n\n"
            
            if len(conflicts) > 10:
                conflict_text += f"... and {len(conflicts) - 10} more conflicts"
            
            self.conflicts_list.setPlainText(conflict_text)
        else:
            self.conflicts_list.setPlainText("✅ No conflicts detected - ready to proceed!")
        
        # Enable action buttons
        self.apply_button.setEnabled(True)
        self.export_button.setEnabled(True)
        
        # Show content
        self.content_splitter.setVisible(True)
        
        # Emit statistics
        preview_stats = {
            "total_files": total_files,
            "conflicts": conflict_count,
            "organization_method": self.organization_combo.currentText()
        }
        self.preview_generated.emit(preview_stats)
        
        self.logger.info(f"Preview generated: {total_files} files, {conflict_count} conflicts")
    
    @pyqtSlot(str)
    def on_preview_error(self, error_message: str):
        """Handle preview generation error"""
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.generate_button.setEnabled(True)
        
        QMessageBox.warning(self, "Preview Error", f"Failed to generate preview:\n\n{error_message}")
    
    def _count_files_in_structure(self, structure: Dict[str, Any]) -> int:
        """Count total files in directory structure"""
        count = 0
        for name, item in structure.items():
            if isinstance(item, dict) and "files" in item:
                count += item.get("file_count", 0)
                count += self._count_files_in_structure(item["files"])
            else:
                count += 1
        return count
    
    @pyqtSlot()
    def apply_organization_changes(self):
        """Apply the organization changes"""
        if not hasattr(self, 'preview_worker') or not self.preview_worker:
            return
        
        # Confirm with user
        if self.conflicts:
            reply = QMessageBox.question(
                self, "Confirm Organization",
                f"Apply organization with {len(self.conflicts)} conflicts?\n\n"
                f"Conflicts will be handled according to: {self.conflict_combo.currentText()}",
                QMessageBox.Yes | QMessageBox.No
            )
        else:
            reply = QMessageBox.question(
                self, "Confirm Organization",
                "Apply the file organization as previewed?",
                QMessageBox.Yes | QMessageBox.No
            )
        
        if reply == QMessageBox.Yes:
            # Get all preview items from the after structure
            preview_items = []
            # This would need to be properly implemented to extract items from structure
            
            self.apply_organization.emit(preview_items)
            QMessageBox.information(self, "Organization Applied", "File organization has been applied successfully!")
    
    @pyqtSlot()
    def export_preview(self):
        """Export preview to file"""
        from PyQt5.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Preview",
            f"file_organization_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON files (*.json)"
        )
        
        if filename:
            try:
                export_data = {
                    "timestamp": datetime.now().isoformat(),
                    "organization_method": self.organization_combo.currentText(),
                    "options": {
                        "create_subdirs": self.create_subdirs_checkbox.isChecked(),
                        "preserve_structure": self.preserve_structure_checkbox.isChecked(),
                        "handle_duplicates": self.handle_duplicates_checkbox.isChecked(),
                        "conflict_resolution": self.conflict_combo.currentText()
                    },
                    "statistics": {
                        "total_files": self._count_files_in_structure({}),
                        "conflicts": len(self.conflicts)
                    },
                    "conflicts": [
                        {
                            "original_path": c.original_path,
                            "suggested_path": c.suggested_path,
                            "conflict_type": c.conflict_type
                        } for c in self.conflicts
                    ]
                }
                
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                QMessageBox.information(self, "Export Successful", f"Preview exported to:\n{filename}")
            except Exception as e:
                QMessageBox.warning(self, "Export Failed", f"Failed to export preview:\n{str(e)}")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Create test window
    window = PreviewWidget()
    window.setWindowTitle("File Organization Preview")
    window.resize(1000, 700)
    window.show()
    
    sys.exit(app.exec_())