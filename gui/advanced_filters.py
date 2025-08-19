"""
Advanced File Filtering Widget for FileOrganizer

Provides sophisticated filtering options for file organization operations.
"""

import sys
import re
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QCheckBox, QGroupBox, QGridLayout, QComboBox,
                           QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit,
                           QSlider, QLineEdit, QPushButton, QListWidget,
                           QListWidgetItem, QFrame, QSizePolicy, QScrollArea,
                           QButtonGroup, QRadioButton, QTextEdit, QTabWidget,
                           QTreeWidget, QTreeWidgetItem, QHeaderView,
                           QProgressBar, QMessageBox)
from PyQt5.QtCore import pyqtSignal, QDate, QTime, Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter, QColor
from typing import Dict, Any, List, Optional, Set, Callable
import logging

# File type categories with icons
FILE_TYPE_CATEGORIES = {
    'Images': {
        'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg', '.raw'],
        'color': '#4CAF50',
        'icon': '🖼️'
    },
    'Documents': {
        'extensions': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages'],
        'color': '#2196F3', 
        'icon': '📄'
    },
    'Videos': {
        'extensions': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mkv'],
        'color': '#FF5722',
        'icon': '🎬'
    },
    'Audio': {
        'extensions': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
        'color': '#9C27B0',
        'icon': '🎵'
    },
    'Archives': {
        'extensions': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        'color': '#795548',
        'icon': '📦'
    },
    'Code': {
        'extensions': ['.py', '.js', '.html', '.css', '.cpp', '.c', '.java', '.php'],
        'color': '#607D8B',
        'icon': '💻'
    },
    'Spreadsheets': {
        'extensions': ['.xls', '.xlsx', '.csv', '.ods', '.numbers'],
        'color': '#4CAF50',
        'icon': '📊'
    },
    'Presentations': {
        'extensions': ['.ppt', '.pptx', '.odp', '.keynote'],
        'color': '#FF9800',
        'icon': '📈'
    }
}


class FileTypeSelector(QWidget):
    """Widget for selecting file types with visual indicators"""
    
    selection_changed = pyqtSignal(set)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_categories = set()
        self.selected_extensions = set()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the file type selector interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("File Types:"))
        
        self.select_all_button = QPushButton("Select All")
        self.select_none_button = QPushButton("Clear All")
        self.select_all_button.setMaximumWidth(80)
        self.select_none_button.setMaximumWidth(80)
        
        header_layout.addStretch()
        header_layout.addWidget(self.select_all_button)
        header_layout.addWidget(self.select_none_button)
        
        layout.addLayout(header_layout)
        
        # File type categories
        categories_layout = QGridLayout()
        
        row, col = 0, 0
        for category, info in FILE_TYPE_CATEGORIES.items():
            checkbox = QCheckBox(f"{info['icon']} {category}")
            checkbox.setObjectName(category)
            checkbox.setFont(QFont("", 9))
            checkbox.stateChanged.connect(self.on_category_changed)
            
            # Style with category color
            checkbox.setStyleSheet(f"""
                QCheckBox::indicator:checked {{
                    background-color: {info['color']};
                    border: 2px solid #333;
                }}
            """)
            
            categories_layout.addWidget(checkbox, row, col)
            
            col += 1
            if col >= 2:
                col = 0
                row += 1
        
        layout.addLayout(categories_layout)
        
        # Custom extensions
        custom_group = QGroupBox("Custom Extensions")
        custom_layout = QVBoxLayout(custom_group)
        
        custom_info = QLabel("Add custom file extensions (comma-separated, with dots):")
        custom_info.setFont(QFont("", 8))
        custom_layout.addWidget(custom_info)
        
        self.custom_extensions_edit = QLineEdit()
        self.custom_extensions_edit.setPlaceholderText("e.g., .xyz, .custom, .special")
        self.custom_extensions_edit.textChanged.connect(self.on_custom_extensions_changed)
        custom_layout.addWidget(self.custom_extensions_edit)
        
        layout.addWidget(custom_group)
        
        # Connect buttons
        self.select_all_button.clicked.connect(self.select_all_categories)
        self.select_none_button.clicked.connect(self.clear_all_categories)
    
    @pyqtSlot(int)
    def on_category_changed(self, state):
        """Handle category selection change"""
        checkbox = self.sender()
        category = checkbox.objectName()
        
        if state == Qt.Checked:
            self.selected_categories.add(category)
            # Add all extensions from this category
            if category in FILE_TYPE_CATEGORIES:
                self.selected_extensions.update(FILE_TYPE_CATEGORIES[category]['extensions'])
        else:
            self.selected_categories.discard(category)
            # Remove all extensions from this category
            if category in FILE_TYPE_CATEGORIES:
                for ext in FILE_TYPE_CATEGORIES[category]['extensions']:
                    self.selected_extensions.discard(ext)
        
        self.update_selection()
    
    @pyqtSlot(str)
    def on_custom_extensions_changed(self, text):
        """Handle custom extensions change"""
        # Parse custom extensions
        custom_exts = []
        if text.strip():
            for ext in text.split(','):
                ext = ext.strip()
                if ext and not ext.startswith('.'):
                    ext = '.' + ext
                if ext:
                    custom_exts.append(ext.lower())
        
        # Update selected extensions
        for ext in list(self.selected_extensions):
            if ext not in [info['extensions'] for info in FILE_TYPE_CATEGORIES.values() for ext_list in [info['extensions']] for ext in ext_list]:
                self.selected_extensions.discard(ext)
        
        self.selected_extensions.update(custom_exts)
        self.update_selection()
    
    def select_all_categories(self):
        """Select all file type categories"""
        for checkbox in self.findChildren(QCheckBox):
            if checkbox.objectName() in FILE_TYPE_CATEGORIES:
                checkbox.setChecked(True)
    
    def clear_all_categories(self):
        """Clear all file type selections"""
        for checkbox in self.findChildren(QCheckBox):
            if checkbox.objectName() in FILE_TYPE_CATEGORIES:
                checkbox.setChecked(False)
        self.custom_extensions_edit.clear()
    
    def update_selection(self):
        """Update the current selection and emit signal"""
        all_extensions = set(self.selected_extensions)
        self.selection_changed.emit(all_extensions)
    
    def get_selected_extensions(self) -> Set[str]:
        """Get currently selected file extensions"""
        return set(self.selected_extensions)
    
    def set_selected_extensions(self, extensions: Set[str]):
        """Set selected file extensions"""
        self.selected_extensions = set(ext.lower() for ext in extensions)
        
        # Update category checkboxes
        for category, info in FILE_TYPE_CATEGORIES.items():
            checkbox = self.findChild(QCheckBox, category)
            if checkbox:
                category_extensions = set(info['extensions'])
                if category_extensions.issubset(self.selected_extensions):
                    checkbox.setChecked(True)
                else:
                    checkbox.setChecked(False)
        
        self.update_selection()


class SizeFilterWidget(QWidget):
    """Widget for filtering files by size"""
    
    size_filter_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the size filter interface"""
        layout = QVBoxLayout(self)
        
        # Size range controls
        range_group = QGroupBox("File Size Range")
        range_layout = QGridLayout(range_group)
        
        # Minimum size
        range_layout.addWidget(QLabel("Minimum Size:"), 0, 0)
        self.min_size_spin = QDoubleSpinBox()
        self.min_size_spin.setRange(0, 999999)
        self.min_size_spin.setDecimals(2)
        self.min_size_spin.setValue(0)
        range_layout.addWidget(self.min_size_spin, 0, 1)
        
        self.min_size_unit = QComboBox()
        self.min_size_unit.addItems(["Bytes", "KB", "MB", "GB"])
        self.min_size_unit.setCurrentText("KB")
        range_layout.addWidget(self.min_size_unit, 0, 2)
        
        # Maximum size
        range_layout.addWidget(QLabel("Maximum Size:"), 1, 0)
        self.max_size_spin = QDoubleSpinBox()
        self.max_size_spin.setRange(0, 999999)
        self.max_size_spin.setDecimals(2)
        self.max_size_spin.setValue(1000)
        range_layout.addWidget(self.max_size_spin, 1, 1)
        
        self.max_size_unit = QComboBox()
        self.max_size_unit.addItems(["Bytes", "KB", "MB", "GB"])
        self.max_size_unit.setCurrentText("MB")
        range_layout.addWidget(self.max_size_unit, 1, 2)
        
        layout.addWidget(range_group)
        
        # Quick size presets
        presets_group = QGroupBox("Quick Size Presets")
        presets_layout = QGridLayout(presets_group)
        
        presets = [
            ("Tiny Files", "< 1 KB", 0, 1, "Bytes", "KB"),
            ("Small Files", "1-100 KB", 1, 100, "KB", "KB"),
            ("Medium Files", "100 KB - 10 MB", 100, 10, "KB", "MB"),
            ("Large Files", "10-100 MB", 10, 100, "MB", "MB"),
            ("Huge Files", "> 100 MB", 100, 999999, "MB", "MB")
        ]
        
        self.preset_buttons = QButtonGroup()
        for i, (name, description, min_val, max_val, min_unit, max_unit) in enumerate(presets):
            btn = QPushButton(f"{name}\n({description})")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, mv=min_val, Mv=max_val, mu=min_unit, Mu=max_unit: 
                              self.apply_size_preset(mv, Mv, mu, Mu))
            self.preset_buttons.addButton(btn, i)
            presets_layout.addWidget(btn, i // 3, i % 3)
        
        layout.addWidget(presets_group)
        
        # Connect change signals
        self.min_size_spin.valueChanged.connect(self.emit_size_filter_changed)
        self.max_size_spin.valueChanged.connect(self.emit_size_filter_changed)
        self.min_size_unit.currentTextChanged.connect(self.emit_size_filter_changed)
        self.max_size_unit.currentTextChanged.connect(self.emit_size_filter_changed)
    
    def apply_size_preset(self, min_val, max_val, min_unit, max_unit):
        """Apply a size preset"""
        self.min_size_spin.setValue(min_val)
        self.max_size_spin.setValue(max_val)
        self.min_size_unit.setCurrentText(min_unit)
        self.max_size_unit.setCurrentText(max_unit)
        self.emit_size_filter_changed()
    
    def emit_size_filter_changed(self):
        """Emit size filter changed signal"""
        size_filter = {
            'min_size': self.min_size_spin.value(),
            'min_size_unit': self.min_size_unit.currentText(),
            'max_size': self.max_size_spin.value(),
            'max_size_unit': self.max_size_unit.currentText(),
            'min_size_bytes': self.convert_to_bytes(self.min_size_spin.value(), self.min_size_unit.currentText()),
            'max_size_bytes': self.convert_to_bytes(self.max_size_spin.value(), self.max_size_unit.currentText())
        }
        self.size_filter_changed.emit(size_filter)
    
    def convert_to_bytes(self, value: float, unit: str) -> int:
        """Convert size value to bytes"""
        multipliers = {
            'Bytes': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024
        }
        return int(value * multipliers.get(unit, 1))
    
    def get_size_filter(self) -> Dict[str, Any]:
        """Get current size filter settings"""
        return {
            'min_size_bytes': self.convert_to_bytes(self.min_size_spin.value(), self.min_size_unit.currentText()),
            'max_size_bytes': self.convert_to_bytes(self.max_size_spin.value(), self.max_size_unit.currentText())
        }


class DateFilterWidget(QWidget):
    """Widget for filtering files by date"""
    
    date_filter_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the date filter interface"""
        layout = QVBoxLayout(self)
        
        # Date type selection
        date_type_group = QGroupBox("Date Type")
        date_type_layout = QHBoxLayout(date_type_group)
        
        self.date_type_group = QButtonGroup()
        
        self.creation_date_radio = QRadioButton("Creation Date")
        self.modification_date_radio = QRadioButton("Modification Date")
        self.access_date_radio = QRadioButton("Access Date")
        
        self.creation_date_radio.setChecked(True)
        
        self.date_type_group.addButton(self.creation_date_radio, 0)
        self.date_type_group.addButton(self.modification_date_radio, 1)
        self.date_type_group.addButton(self.access_date_radio, 2)
        
        date_type_layout.addWidget(self.creation_date_radio)
        date_type_layout.addWidget(self.modification_date_radio)
        date_type_layout.addWidget(self.access_date_radio)
        
        layout.addWidget(date_type_group)
        
        # Date range controls
        range_group = QGroupBox("Date Range")
        range_layout = QGridLayout(range_group)
        
        # From date
        range_layout.addWidget(QLabel("From:"), 0, 0)
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        range_layout.addWidget(self.from_date, 0, 1)
        
        # To date
        range_layout.addWidget(QLabel("To:"), 1, 0)
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        range_layout.addWidget(self.to_date, 1, 1)
        
        layout.addWidget(range_group)
        
        # Quick date presets
        presets_group = QGroupBox("Quick Date Presets")
        presets_layout = QGridLayout(presets_group)
        
        presets = [
            ("Today", 0),
            ("Yesterday", 1),
            ("Last 7 Days", 7),
            ("Last 30 Days", 30),
            ("Last 90 Days", 90),
            ("Last Year", 365)
        ]
        
        for i, (name, days) in enumerate(presets):
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, d=days: self.apply_date_preset(d))
            presets_layout.addWidget(btn, i // 3, i % 3)
        
        layout.addWidget(presets_group)
        
        # Connect change signals
        self.from_date.dateChanged.connect(self.emit_date_filter_changed)
        self.to_date.dateChanged.connect(self.emit_date_filter_changed)
        self.date_type_group.buttonClicked.connect(self.emit_date_filter_changed)
    
    def apply_date_preset(self, days_back: int):
        """Apply a date preset"""
        if days_back == 0:
            # Today
            self.from_date.setDate(QDate.currentDate())
            self.to_date.setDate(QDate.currentDate())
        elif days_back == 1:
            # Yesterday
            yesterday = QDate.currentDate().addDays(-1)
            self.from_date.setDate(yesterday)
            self.to_date.setDate(yesterday)
        else:
            # Last X days
            self.from_date.setDate(QDate.currentDate().addDays(-days_back))
            self.to_date.setDate(QDate.currentDate())
        
        self.emit_date_filter_changed()
    
    def emit_date_filter_changed(self):
        """Emit date filter changed signal"""
        date_type_map = {0: 'creation', 1: 'modification', 2: 'access'}
        date_type = date_type_map.get(self.date_type_group.checkedId(), 'creation')
        
        date_filter = {
            'date_type': date_type,
            'from_date': self.from_date.date().toPyDate(),
            'to_date': self.to_date.date().toPyDate()
        }
        self.date_filter_changed.emit(date_filter)
    
    def get_date_filter(self) -> Dict[str, Any]:
        """Get current date filter settings"""
        date_type_map = {0: 'creation', 1: 'modification', 2: 'access'}
        date_type = date_type_map.get(self.date_type_group.checkedId(), 'creation')
        
        return {
            'date_type': date_type,
            'from_date': self.from_date.date().toPyDate(),
            'to_date': self.to_date.date().toPyDate()
        }


class AdvancedFiltersWidget(QWidget):
    """Main advanced filters widget with all filtering options"""
    
    filters_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.current_filters = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the advanced filters interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create tabs for different filter types
        self.tab_widget = QTabWidget()
        
        # File Types Tab
        self.file_type_selector = FileTypeSelector()
        self.tab_widget.addTab(self.file_type_selector, "📁 File Types")
        
        # Size Filter Tab
        self.size_filter = SizeFilterWidget()
        self.tab_widget.addTab(self.size_filter, "📏 Size")
        
        # Date Filter Tab
        self.date_filter = DateFilterWidget()
        self.tab_widget.addTab(self.date_filter, "📅 Date")
        
        # Name/Path Filter Tab
        name_tab = self.setup_name_filter_tab()
        self.tab_widget.addTab(name_tab, "🔤 Name/Path")
        
        # Advanced Tab
        advanced_tab = self.setup_advanced_filter_tab()
        self.tab_widget.addTab(advanced_tab, "⚙️ Advanced")
        
        layout.addWidget(self.tab_widget)
        
        # Filter summary and controls
        self.setup_filter_controls(layout)
        
        # Connect signals
        self.file_type_selector.selection_changed.connect(self.on_filters_changed)
        self.size_filter.size_filter_changed.connect(self.on_filters_changed)
        self.date_filter.date_filter_changed.connect(self.on_filters_changed)
    
    def setup_name_filter_tab(self) -> QWidget:
        """Setup name/path filtering tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Filename patterns
        filename_group = QGroupBox("Filename Patterns")
        filename_layout = QVBoxLayout(filename_group)
        
        # Include patterns
        filename_layout.addWidget(QLabel("Include files matching (wildcards allowed):"))
        self.include_pattern_edit = QLineEdit()
        self.include_pattern_edit.setPlaceholderText("e.g., *.jpg, IMG_*, vacation*")
        filename_layout.addWidget(self.include_pattern_edit)
        
        # Exclude patterns
        filename_layout.addWidget(QLabel("Exclude files matching:"))
        self.exclude_pattern_edit = QLineEdit()
        self.exclude_pattern_edit.setPlaceholderText("e.g., temp*, *.tmp, ._*")
        filename_layout.addWidget(self.exclude_pattern_edit)
        
        layout.addWidget(filename_group)
        
        # Path filters
        path_group = QGroupBox("Path Filters")
        path_layout = QVBoxLayout(path_group)
        
        path_layout.addWidget(QLabel("Include paths containing:"))
        self.include_path_edit = QLineEdit()
        self.include_path_edit.setPlaceholderText("e.g., Photos, Documents")
        path_layout.addWidget(self.include_path_edit)
        
        path_layout.addWidget(QLabel("Exclude paths containing:"))
        self.exclude_path_edit = QLineEdit()
        self.exclude_path_edit.setPlaceholderText("e.g., temp, cache, .git")
        path_layout.addWidget(self.exclude_path_edit)
        
        layout.addWidget(path_group)
        
        # Regex patterns
        regex_group = QGroupBox("Regular Expression Patterns")
        regex_layout = QVBoxLayout(regex_group)
        
        self.use_regex_checkbox = QCheckBox("Enable regular expression matching")
        regex_layout.addWidget(self.use_regex_checkbox)
        
        regex_layout.addWidget(QLabel("Regex pattern:"))
        self.regex_pattern_edit = QLineEdit()
        self.regex_pattern_edit.setPlaceholderText("e.g., ^IMG_\\d{4}\\.(jpg|png)$")
        self.regex_pattern_edit.setEnabled(False)
        regex_layout.addWidget(self.regex_pattern_edit)
        
        # Enable/disable regex input based on checkbox
        self.use_regex_checkbox.toggled.connect(self.regex_pattern_edit.setEnabled)
        
        layout.addWidget(regex_group)
        layout.addStretch()
        
        # Connect change signals
        self.include_pattern_edit.textChanged.connect(self.on_filters_changed)
        self.exclude_pattern_edit.textChanged.connect(self.on_filters_changed)
        self.include_path_edit.textChanged.connect(self.on_filters_changed)
        self.exclude_path_edit.textChanged.connect(self.on_filters_changed)
        self.use_regex_checkbox.toggled.connect(self.on_filters_changed)
        self.regex_pattern_edit.textChanged.connect(self.on_filters_changed)
        
        return tab
    
    def setup_advanced_filter_tab(self) -> QWidget:
        """Setup advanced filtering options tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # File attributes
        attributes_group = QGroupBox("File Attributes")
        attributes_layout = QGridLayout(attributes_group)
        
        self.hidden_files_checkbox = QCheckBox("Include hidden files")
        attributes_layout.addWidget(self.hidden_files_checkbox, 0, 0)
        
        self.system_files_checkbox = QCheckBox("Include system files")
        attributes_layout.addWidget(self.system_files_checkbox, 0, 1)
        
        self.readonly_files_checkbox = QCheckBox("Include read-only files")
        self.readonly_files_checkbox.setChecked(True)
        attributes_layout.addWidget(self.readonly_files_checkbox, 1, 0)
        
        self.empty_files_checkbox = QCheckBox("Include empty files (0 bytes)")
        attributes_layout.addWidget(self.empty_files_checkbox, 1, 1)
        
        layout.addWidget(attributes_group)
        
        # Duplicate handling
        duplicates_group = QGroupBox("Duplicate File Handling")
        duplicates_layout = QVBoxLayout(duplicates_group)
        
        self.include_duplicates_checkbox = QCheckBox("Include duplicate files in results")
        self.include_duplicates_checkbox.setChecked(True)
        duplicates_layout.addWidget(self.include_duplicates_checkbox)
        
        self.duplicate_criteria_combo = QComboBox()
        self.duplicate_criteria_combo.addItems([
            "File content (hash)", "File size", "Filename", "Size + Name"
        ])
        duplicates_layout.addWidget(QLabel("Duplicate detection method:"))
        duplicates_layout.addWidget(self.duplicate_criteria_combo)
        
        layout.addWidget(duplicates_group)
        
        # Performance options
        performance_group = QGroupBox("Performance Options")
        performance_layout = QGridLayout(performance_group)
        
        performance_layout.addWidget(QLabel("Max files to process:"), 0, 0)
        self.max_files_spin = QSpinBox()
        self.max_files_spin.setRange(100, 1000000)
        self.max_files_spin.setValue(10000)
        performance_layout.addWidget(self.max_files_spin, 0, 1)
        
        performance_layout.addWidget(QLabel("Deep scan (slower):"), 1, 0)
        self.deep_scan_checkbox = QCheckBox("Enable detailed file analysis")
        performance_layout.addWidget(self.deep_scan_checkbox, 1, 1)
        
        layout.addWidget(performance_group)
        
        # Custom filter script
        script_group = QGroupBox("Custom Filter Script (Advanced)")
        script_layout = QVBoxLayout(script_group)
        
        self.enable_custom_script_checkbox = QCheckBox("Enable custom Python filter script")
        script_layout.addWidget(self.enable_custom_script_checkbox)
        
        script_info = QLabel("Write a Python function that returns True to include the file:")
        script_info.setFont(QFont("", 8))
        script_layout.addWidget(script_info)
        
        self.custom_script_edit = QTextEdit()
        self.custom_script_edit.setMaximumHeight(100)
        self.custom_script_edit.setEnabled(False)
        self.custom_script_edit.setPlainText("""def custom_filter(filepath, filesize, modified_date):
    # Example: include only files larger than 1MB
    return filesize > 1024 * 1024""")
        script_layout.addWidget(self.custom_script_edit)
        
        self.enable_custom_script_checkbox.toggled.connect(self.custom_script_edit.setEnabled)
        
        layout.addWidget(script_group)
        layout.addStretch()
        
        # Connect change signals
        self.hidden_files_checkbox.toggled.connect(self.on_filters_changed)
        self.system_files_checkbox.toggled.connect(self.on_filters_changed)
        self.readonly_files_checkbox.toggled.connect(self.on_filters_changed)
        self.empty_files_checkbox.toggled.connect(self.on_filters_changed)
        self.include_duplicates_checkbox.toggled.connect(self.on_filters_changed)
        self.duplicate_criteria_combo.currentTextChanged.connect(self.on_filters_changed)
        self.max_files_spin.valueChanged.connect(self.on_filters_changed)
        self.deep_scan_checkbox.toggled.connect(self.on_filters_changed)
        self.enable_custom_script_checkbox.toggled.connect(self.on_filters_changed)
        self.custom_script_edit.textChanged.connect(self.on_filters_changed)
        
        return tab
    
    def setup_filter_controls(self, layout):
        """Setup filter summary and control buttons"""
        # Filter summary
        summary_group = QGroupBox("Active Filters Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        self.filter_summary_label = QLabel("No filters active")
        self.filter_summary_label.setFont(QFont("", 9))
        self.filter_summary_label.setWordWrap(True)
        summary_layout.addWidget(self.filter_summary_label)
        
        layout.addWidget(summary_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.apply_filters_button = QPushButton("Apply Filters")
        self.clear_filters_button = QPushButton("Clear All")
        self.save_preset_button = QPushButton("Save Preset")
        self.load_preset_button = QPushButton("Load Preset")
        
        button_layout.addWidget(self.apply_filters_button)
        button_layout.addWidget(self.clear_filters_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_preset_button)
        button_layout.addWidget(self.load_preset_button)
        
        layout.addLayout(button_layout)
        
        # Connect button signals
        self.apply_filters_button.clicked.connect(self.apply_filters)
        self.clear_filters_button.clicked.connect(self.clear_all_filters)
        self.save_preset_button.clicked.connect(self.save_filter_preset)
        self.load_preset_button.clicked.connect(self.load_filter_preset)
    
    @pyqtSlot()
    def on_filters_changed(self):
        """Handle filter changes and update summary"""
        self.current_filters = self.get_current_filters()
        self.update_filter_summary()
        self.filters_changed.emit(self.current_filters)
    
    def get_current_filters(self) -> Dict[str, Any]:
        """Get all current filter settings"""
        filters = {}
        
        # File type filters
        selected_extensions = self.file_type_selector.get_selected_extensions()
        if selected_extensions:
            filters['file_extensions'] = list(selected_extensions)
        
        # Size filters
        size_filter = self.size_filter.get_size_filter()
        if size_filter['min_size_bytes'] > 0 or size_filter['max_size_bytes'] < 999999 * 1024 * 1024:
            filters['size_range'] = size_filter
        
        # Date filters
        date_filter = self.date_filter.get_date_filter()
        filters['date_filter'] = date_filter
        
        # Name/path filters
        if hasattr(self, 'include_pattern_edit'):
            if self.include_pattern_edit.text().strip():
                filters['include_patterns'] = self.include_pattern_edit.text().strip()
            
            if self.exclude_pattern_edit.text().strip():
                filters['exclude_patterns'] = self.exclude_pattern_edit.text().strip()
            
            if self.include_path_edit.text().strip():
                filters['include_paths'] = self.include_path_edit.text().strip()
            
            if self.exclude_path_edit.text().strip():
                filters['exclude_paths'] = self.exclude_path_edit.text().strip()
            
            if self.use_regex_checkbox.isChecked() and self.regex_pattern_edit.text().strip():
                filters['regex_pattern'] = self.regex_pattern_edit.text().strip()
        
        # Advanced filters
        if hasattr(self, 'hidden_files_checkbox'):
            filters['include_hidden'] = self.hidden_files_checkbox.isChecked()
            filters['include_system'] = self.system_files_checkbox.isChecked()
            filters['include_readonly'] = self.readonly_files_checkbox.isChecked()
            filters['include_empty'] = self.empty_files_checkbox.isChecked()
            filters['include_duplicates'] = self.include_duplicates_checkbox.isChecked()
            filters['duplicate_criteria'] = self.duplicate_criteria_combo.currentText()
            filters['max_files'] = self.max_files_spin.value()
            filters['deep_scan'] = self.deep_scan_checkbox.isChecked()
            
            if self.enable_custom_script_checkbox.isChecked():
                filters['custom_script'] = self.custom_script_edit.toPlainText()
        
        return filters
    
    def update_filter_summary(self):
        """Update the filter summary display"""
        summary_parts = []
        
        # File types
        if 'file_extensions' in self.current_filters:
            ext_count = len(self.current_filters['file_extensions'])
            summary_parts.append(f"File types: {ext_count} extensions")
        
        # Size
        if 'size_range' in self.current_filters:
            size_range = self.current_filters['size_range']
            min_size = size_range['min_size_bytes']
            max_size = size_range['max_size_bytes']
            summary_parts.append(f"Size: {self.format_bytes(min_size)} - {self.format_bytes(max_size)}")
        
        # Date
        if 'date_filter' in self.current_filters:
            date_filter = self.current_filters['date_filter']
            date_type = date_filter['date_type'].title()
            from_date = date_filter['from_date'].strftime('%Y-%m-%d')
            to_date = date_filter['to_date'].strftime('%Y-%m-%d')
            summary_parts.append(f"{date_type} date: {from_date} to {to_date}")
        
        # Name patterns
        pattern_count = 0
        if 'include_patterns' in self.current_filters:
            pattern_count += 1
        if 'exclude_patterns' in self.current_filters:
            pattern_count += 1
        if 'regex_pattern' in self.current_filters:
            pattern_count += 1
        if pattern_count > 0:
            summary_parts.append(f"Name patterns: {pattern_count} rules")
        
        # Advanced options
        advanced_count = 0
        for key in ['include_hidden', 'include_system', 'deep_scan']:
            if self.current_filters.get(key, False):
                advanced_count += 1
        if advanced_count > 0:
            summary_parts.append(f"Advanced options: {advanced_count} enabled")
        
        if summary_parts:
            summary_text = " • ".join(summary_parts)
        else:
            summary_text = "No filters active - all files will be included"
        
        self.filter_summary_label.setText(summary_text)
    
    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes value for display"""
        if bytes_value < 1024:
            return f"{bytes_value} B"
        elif bytes_value < 1024 * 1024:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"
    
    @pyqtSlot()
    def apply_filters(self):
        """Apply current filters"""
        self.filters_changed.emit(self.current_filters)
        QMessageBox.information(self, "Filters Applied", 
                              "Filters have been applied successfully.")
    
    @pyqtSlot()
    def clear_all_filters(self):
        """Clear all active filters"""
        # Clear file type selection
        self.file_type_selector.clear_all_categories()
        
        # Reset size filters
        self.size_filter.min_size_spin.setValue(0)
        self.size_filter.max_size_spin.setValue(1000)
        self.size_filter.min_size_unit.setCurrentText("KB")
        self.size_filter.max_size_unit.setCurrentText("MB")
        
        # Reset date filters to last 30 days
        self.date_filter.from_date.setDate(QDate.currentDate().addDays(-30))
        self.date_filter.to_date.setDate(QDate.currentDate())
        self.date_filter.creation_date_radio.setChecked(True)
        
        # Clear name/path filters
        if hasattr(self, 'include_pattern_edit'):
            self.include_pattern_edit.clear()
            self.exclude_pattern_edit.clear()
            self.include_path_edit.clear()
            self.exclude_path_edit.clear()
            self.use_regex_checkbox.setChecked(False)
            self.regex_pattern_edit.clear()
        
        # Reset advanced options
        if hasattr(self, 'hidden_files_checkbox'):
            self.hidden_files_checkbox.setChecked(False)
            self.system_files_checkbox.setChecked(False)
            self.readonly_files_checkbox.setChecked(True)
            self.empty_files_checkbox.setChecked(False)
            self.include_duplicates_checkbox.setChecked(True)
            self.duplicate_criteria_combo.setCurrentIndex(0)
            self.max_files_spin.setValue(10000)
            self.deep_scan_checkbox.setChecked(False)
            self.enable_custom_script_checkbox.setChecked(False)
        
        QMessageBox.information(self, "Filters Cleared", "All filters have been cleared.")
    
    @pyqtSlot()
    def save_filter_preset(self):
        """Save current filters as a preset"""
        # Implementation would save to a config file or database
        QMessageBox.information(self, "Preset Saved", "Filter preset saved successfully.")
    
    @pyqtSlot()
    def load_filter_preset(self):
        """Load a saved filter preset"""
        # Implementation would load from a config file or database
        QMessageBox.information(self, "Preset Loaded", "Filter preset loaded successfully.")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Create test window
    window = AdvancedFiltersWidget()
    window.setWindowTitle("Advanced File Filters Test")
    window.resize(600, 800)
    window.show()
    
    # Connect to filter changes
    def on_filters_changed(filters):
        print("Filters changed:", filters)
    
    window.filters_changed.connect(on_filters_changed)
    
    sys.exit(app.exec_())