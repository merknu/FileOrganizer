"""
Theme Manager for FileOrganizer

Provides dark/light theme switching capabilities with persistent settings.
"""

import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QButtonGroup, QRadioButton, QGroupBox,
                           QSlider, QComboBox, QColorDialog, QApplication,
                           QMessageBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QSettings, pyqtSlot
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon
from typing import Dict, Any, Optional
import json
import logging


class ThemeManager:
    """Manages application themes and styling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = QSettings("FileOrganizer", "Theme")
        self.current_theme = "light"
        self.custom_colors = {}
        
        # Built-in themes
        self.themes = {
            "light": {
                "name": "Light",
                "description": "Clean light theme",
                "colors": {
                    "background": "#ffffff",
                    "surface": "#f8f9fa",
                    "primary": "#007acc",
                    "primary_variant": "#005c99",
                    "secondary": "#6c757d",
                    "text_primary": "#212529",
                    "text_secondary": "#6c757d",
                    "border": "#dee2e6",
                    "success": "#28a745",
                    "warning": "#ffc107",
                    "error": "#dc3545",
                    "info": "#17a2b8"
                }
            },
            "dark": {
                "name": "Dark",
                "description": "Modern dark theme",
                "colors": {
                    "background": "#1a1a1a",
                    "surface": "#2d2d2d",
                    "primary": "#4CAF50",
                    "primary_variant": "#388e3c",
                    "secondary": "#b0b0b0",
                    "text_primary": "#ffffff",
                    "text_secondary": "#b0b0b0",
                    "border": "#404040",
                    "success": "#4caf50",
                    "warning": "#ff9800",
                    "error": "#f44336",
                    "info": "#2196f3"
                }
            },
            "blue": {
                "name": "Blue",
                "description": "Professional blue theme",
                "colors": {
                    "background": "#f0f4f8",
                    "surface": "#ffffff",
                    "primary": "#2196f3",
                    "primary_variant": "#1976d2",
                    "secondary": "#607d8b",
                    "text_primary": "#1a202c",
                    "text_secondary": "#4a5568",
                    "border": "#cbd5e0",
                    "success": "#48bb78",
                    "warning": "#ed8936",
                    "error": "#f56565",
                    "info": "#4299e1"
                }
            },
            "green": {
                "name": "Green",
                "description": "Nature-inspired green theme",
                "colors": {
                    "background": "#f0fff4",
                    "surface": "#ffffff",
                    "primary": "#38a169",
                    "primary_variant": "#2f855a",
                    "secondary": "#718096",
                    "text_primary": "#1a202c",
                    "text_secondary": "#4a5568",
                    "border": "#e2e8f0",
                    "success": "#48bb78",
                    "warning": "#ed8936",
                    "error": "#f56565",
                    "info": "#4299e1"
                }
            }
        }
        
        # Load saved theme
        self.load_theme_settings()
    
    def get_available_themes(self) -> Dict[str, Dict]:
        """Get all available themes"""
        return self.themes
    
    def get_current_theme(self) -> str:
        """Get current theme name"""
        return self.current_theme
    
    def get_theme_colors(self, theme_name: str = None) -> Dict[str, str]:
        """Get colors for specified theme or current theme"""
        if theme_name is None:
            theme_name = self.current_theme
        
        if theme_name in self.themes:
            colors = self.themes[theme_name]["colors"].copy()
            # Apply custom color overrides
            if theme_name in self.custom_colors:
                colors.update(self.custom_colors[theme_name])
            return colors
        
        return self.themes["light"]["colors"]
    
    def apply_theme(self, app: QApplication, theme_name: str):
        """Apply theme to application"""
        if theme_name not in self.themes:
            self.logger.warning(f"Unknown theme: {theme_name}")
            return False
        
        self.current_theme = theme_name
        colors = self.get_theme_colors(theme_name)
        
        # Create Qt palette
        palette = QPalette()
        
        # Set palette colors
        palette.setColor(QPalette.Window, QColor(colors["background"]))
        palette.setColor(QPalette.WindowText, QColor(colors["text_primary"]))
        palette.setColor(QPalette.Base, QColor(colors["surface"]))
        palette.setColor(QPalette.AlternateBase, QColor(colors["border"]))
        palette.setColor(QPalette.ToolTipBase, QColor(colors["surface"]))
        palette.setColor(QPalette.ToolTipText, QColor(colors["text_primary"]))
        palette.setColor(QPalette.Text, QColor(colors["text_primary"]))
        palette.setColor(QPalette.Button, QColor(colors["surface"]))
        palette.setColor(QPalette.ButtonText, QColor(colors["text_primary"]))
        palette.setColor(QPalette.BrightText, QColor(colors["text_primary"]))
        palette.setColor(QPalette.Link, QColor(colors["primary"]))
        palette.setColor(QPalette.Highlight, QColor(colors["primary"]))
        palette.setColor(QPalette.HighlightedText, QColor(colors["background"]))
        
        # Apply palette
        app.setPalette(palette)
        
        # Apply stylesheet
        stylesheet = self.generate_stylesheet(colors)
        app.setStyleSheet(stylesheet)
        
        # Save theme setting
        self.save_theme_settings()
        
        self.logger.info(f"Applied theme: {theme_name}")
        return True
    
    def generate_stylesheet(self, colors: Dict[str, str]) -> str:
        """Generate comprehensive stylesheet for the theme"""
        return f"""
        /* Main Window and Base Widgets */
        QMainWindow, QWidget {{
            background-color: {colors["background"]};
            color: {colors["text_primary"]};
        }}
        
        /* Group Boxes */
        QGroupBox {{
            font-weight: bold;
            border: 2px solid {colors["border"]};
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            background-color: {colors["surface"]};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: {colors["text_primary"]};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {colors["surface"]};
            border: 1px solid {colors["border"]};
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 500;
            color: {colors["text_primary"]};
            min-width: 60px;
        }}
        
        QPushButton:hover {{
            background-color: {colors["primary"]};
            color: {colors["background"]};
            border-color: {colors["primary"]};
        }}
        
        QPushButton:pressed {{
            background-color: {colors["primary_variant"]};
        }}
        
        QPushButton:disabled {{
            background-color: {colors["border"]};
            color: {colors["text_secondary"]};
            border-color: {colors["border"]};
        }}
        
        /* Primary Action Buttons */
        QPushButton[class="primary"] {{
            background-color: {colors["primary"]};
            color: {colors["background"]};
            border: none;
            font-weight: bold;
        }}
        
        QPushButton[class="primary"]:hover {{
            background-color: {colors["primary_variant"]};
        }}
        
        /* Input Fields */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {colors["surface"]};
            border: 1px solid {colors["border"]};
            border-radius: 3px;
            padding: 6px;
            color: {colors["text_primary"]};
            selection-background-color: {colors["primary"]};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {colors["primary"]};
        }}
        
        /* Combo Boxes */
        QComboBox {{
            background-color: {colors["surface"]};
            border: 1px solid {colors["border"]};
            border-radius: 3px;
            padding: 5px;
            min-width: 6em;
            color: {colors["text_primary"]};
        }}
        
        QComboBox:hover {{
            border-color: {colors["primary"]};
        }}
        
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 15px;
            border-left-width: 1px;
            border-left-color: {colors["border"]};
            border-left-style: solid;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors["surface"]};
            border: 1px solid {colors["border"]};
            selection-background-color: {colors["primary"]};
            color: {colors["text_primary"]};
        }}
        
        /* Spin Boxes */
        QSpinBox, QDoubleSpinBox {{
            background-color: {colors["surface"]};
            border: 1px solid {colors["border"]};
            border-radius: 3px;
            padding: 5px;
            color: {colors["text_primary"]};
        }}
        
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {colors["primary"]};
        }}
        
        /* Check Boxes and Radio Buttons */
        QCheckBox, QRadioButton {{
            color: {colors["text_primary"]};
            spacing: 8px;
        }}
        
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 16px;
            height: 16px;
        }}
        
        QCheckBox::indicator:unchecked {{
            border: 2px solid {colors["border"]};
            background-color: {colors["surface"]};
            border-radius: 2px;
        }}
        
        QCheckBox::indicator:checked {{
            border: 2px solid {colors["primary"]};
            background-color: {colors["primary"]};
            border-radius: 2px;
        }}
        
        QRadioButton::indicator:unchecked {{
            border: 2px solid {colors["border"]};
            background-color: {colors["surface"]};
            border-radius: 8px;
        }}
        
        QRadioButton::indicator:checked {{
            border: 2px solid {colors["primary"]};
            background-color: {colors["primary"]};
            border-radius: 8px;
        }}
        
        /* Progress Bars */
        QProgressBar {{
            border: 1px solid {colors["border"]};
            border-radius: 3px;
            text-align: center;
            background-color: {colors["surface"]};
            color: {colors["text_primary"]};
        }}
        
        QProgressBar::chunk {{
            background-color: {colors["primary"]};
            border-radius: 2px;
        }}
        
        /* Sliders */
        QSlider::groove:horizontal {{
            border: 1px solid {colors["border"]};
            height: 6px;
            background: {colors["surface"]};
            border-radius: 3px;
        }}
        
        QSlider::handle:horizontal {{
            background: {colors["primary"]};
            border: 1px solid {colors["primary_variant"]};
            width: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }}
        
        QSlider::handle:horizontal:hover {{
            background: {colors["primary_variant"]};
        }}
        
        /* Tab Widget */
        QTabWidget::pane {{
            border: 1px solid {colors["border"]};
            background-color: {colors["surface"]};
        }}
        
        QTabBar::tab {{
            background-color: {colors["background"]};
            border: 1px solid {colors["border"]};
            padding: 8px 16px;
            margin-right: 2px;
            color: {colors["text_primary"]};
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors["surface"]};
            border-bottom-color: {colors["surface"]};
            color: {colors["primary"]};
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors["primary"]};
            color: {colors["background"]};
        }}
        
        /* Tree and List Widgets */
        QTreeWidget, QListWidget, QTableWidget {{
            background-color: {colors["surface"]};
            alternate-background-color: {colors["background"]};
            border: 1px solid {colors["border"]};
            gridline-color: {colors["border"]};
            color: {colors["text_primary"]};
            selection-background-color: {colors["primary"]};
        }}
        
        QTreeWidget::item:hover, QListWidget::item:hover, QTableWidget::item:hover {{
            background-color: {colors["border"]};
        }}
        
        QTreeWidget::item:selected, QListWidget::item:selected, QTableWidget::item:selected {{
            background-color: {colors["primary"]};
            color: {colors["background"]};
        }}
        
        /* Headers */
        QHeaderView::section {{
            background-color: {colors["surface"]};
            color: {colors["text_primary"]};
            padding: 8px;
            border: 1px solid {colors["border"]};
            font-weight: bold;
        }}
        
        /* Scroll Bars */
        QScrollBar:vertical {{
            background-color: {colors["background"]};
            width: 12px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors["secondary"]};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors["primary"]};
        }}
        
        QScrollBar:horizontal {{
            background-color: {colors["background"]};
            height: 12px;
            border: none;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {colors["secondary"]};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {colors["primary"]};
        }}
        
        /* Tool Tips */
        QToolTip {{
            background-color: {colors["surface"]};
            color: {colors["text_primary"]};
            border: 1px solid {colors["border"]};
            padding: 5px;
            border-radius: 3px;
        }}
        
        /* Menu Bar and Menus */
        QMenuBar {{
            background-color: {colors["background"]};
            color: {colors["text_primary"]};
            border-bottom: 1px solid {colors["border"]};
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors["primary"]};
            color: {colors["background"]};
        }}
        
        QMenu {{
            background-color: {colors["surface"]};
            color: {colors["text_primary"]};
            border: 1px solid {colors["border"]};
        }}
        
        QMenu::item:selected {{
            background-color: {colors["primary"]};
            color: {colors["background"]};
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {colors["surface"]};
            color: {colors["text_primary"]};
            border-top: 1px solid {colors["border"]};
        }}
        
        /* Frames and Separators */
        QFrame[frameShape="4"] {{ /* HLine */
            color: {colors["border"]};
        }}
        
        QFrame[frameShape="5"] {{ /* VLine */
            color: {colors["border"]};
        }}
        
        /* Dock Widgets */
        QDockWidget {{
            titlebar-close-icon: none;
            titlebar-normal-icon: none;
            color: {colors["text_primary"]};
        }}
        
        QDockWidget::title {{
            background: {colors["surface"]};
            padding: 5px;
            border: 1px solid {colors["border"]};
        }}
        
        /* Special Status Colors */
        QLabel[status="success"] {{
            color: {colors["success"]};
            font-weight: bold;
        }}
        
        QLabel[status="warning"] {{
            color: {colors["warning"]};
            font-weight: bold;
        }}
        
        QLabel[status="error"] {{
            color: {colors["error"]};
            font-weight: bold;
        }}
        
        QLabel[status="info"] {{
            color: {colors["info"]};
            font-weight: bold;
        }}
        """
    
    def set_custom_color(self, theme_name: str, color_key: str, color_value: str):
        """Set custom color override for a theme"""
        if theme_name not in self.custom_colors:
            self.custom_colors[theme_name] = {}
        
        self.custom_colors[theme_name][color_key] = color_value
        self.save_theme_settings()
    
    def reset_custom_colors(self, theme_name: str):
        """Reset custom colors for a theme"""
        if theme_name in self.custom_colors:
            del self.custom_colors[theme_name]
            self.save_theme_settings()
    
    def save_theme_settings(self):
        """Save theme settings to persistent storage"""
        self.settings.setValue("current_theme", self.current_theme)
        self.settings.setValue("custom_colors", json.dumps(self.custom_colors))
    
    def load_theme_settings(self):
        """Load theme settings from persistent storage"""
        saved_theme = self.settings.value("current_theme", "light")
        if saved_theme in self.themes:
            self.current_theme = saved_theme
        
        try:
            custom_colors_json = self.settings.value("custom_colors", "{}")
            self.custom_colors = json.loads(custom_colors_json)
        except:
            self.custom_colors = {}


class ThemeToggleWidget(QWidget):
    """Widget for theme selection and customization"""
    
    theme_changed = pyqtSignal(str)  # Theme name
    
    def __init__(self, theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.setup_ui()
        self.update_current_theme()
    
    def setup_ui(self):
        """Setup the theme toggle interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("Theme Settings")
        header.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(header)
        
        # Theme selection
        theme_group = QGroupBox("Select Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        self.theme_buttons = QButtonGroup()
        
        for theme_id, theme_data in self.theme_manager.get_available_themes().items():
            radio = QRadioButton(f"{theme_data['name']} - {theme_data['description']}")
            radio.setObjectName(theme_id)
            self.theme_buttons.addButton(radio)
            theme_layout.addWidget(radio)
        
        self.theme_buttons.buttonClicked.connect(self.on_theme_selected)
        layout.addWidget(theme_group)
        
        # Quick toggle buttons
        quick_group = QGroupBox("Quick Toggle")
        quick_layout = QHBoxLayout(quick_group)
        
        self.light_button = QPushButton("☀️ Light")
        self.light_button.clicked.connect(lambda: self.set_theme("light"))
        quick_layout.addWidget(self.light_button)
        
        self.dark_button = QPushButton("🌙 Dark")
        self.dark_button.clicked.connect(lambda: self.set_theme("dark"))
        quick_layout.addWidget(self.dark_button)
        
        quick_layout.addStretch()
        layout.addWidget(quick_group)
        
        # Color customization (simplified)
        custom_group = QGroupBox("Color Customization")
        custom_layout = QVBoxLayout(custom_group)
        
        # Primary color picker
        primary_layout = QHBoxLayout()
        primary_layout.addWidget(QLabel("Primary Color:"))
        self.primary_color_button = QPushButton("Choose Color")
        self.primary_color_button.clicked.connect(self.choose_primary_color)
        primary_layout.addWidget(self.primary_color_button)
        primary_layout.addStretch()
        custom_layout.addLayout(primary_layout)
        
        # Reset button
        reset_button = QPushButton("Reset to Default Colors")
        reset_button.clicked.connect(self.reset_colors)
        custom_layout.addWidget(reset_button)
        
        layout.addWidget(custom_group)
        
        # Apply button
        apply_button = QPushButton("Apply Theme")
        apply_button.setStyleSheet("""
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
        """)
        apply_button.clicked.connect(self.apply_current_theme)
        layout.addWidget(apply_button)
        
        layout.addStretch()
    
    def update_current_theme(self):
        """Update UI to reflect current theme"""
        current_theme = self.theme_manager.get_current_theme()
        
        # Select appropriate radio button
        for button in self.theme_buttons.buttons():
            if button.objectName() == current_theme:
                button.setChecked(True)
                break
        
        # Update primary color button
        colors = self.theme_manager.get_theme_colors(current_theme)
        primary_color = colors.get("primary", "#007acc")
        self.primary_color_button.setStyleSheet(f"background-color: {primary_color};")
    
    @pyqtSlot()
    def on_theme_selected(self):
        """Handle theme selection"""
        checked_button = self.theme_buttons.checkedButton()
        if checked_button:
            theme_name = checked_button.objectName()
            self.set_theme(theme_name)
    
    def set_theme(self, theme_name: str):
        """Set and apply theme"""
        app = QApplication.instance()
        if self.theme_manager.apply_theme(app, theme_name):
            self.theme_changed.emit(theme_name)
            self.update_current_theme()
    
    @pyqtSlot()
    def choose_primary_color(self):
        """Open color picker for primary color"""
        current_theme = self.theme_manager.get_current_theme()
        colors = self.theme_manager.get_theme_colors(current_theme)
        current_color = QColor(colors.get("primary", "#007acc"))
        
        color = QColorDialog.getColor(current_color, self, "Choose Primary Color")
        if color.isValid():
            self.theme_manager.set_custom_color(current_theme, "primary", color.name())
            self.primary_color_button.setStyleSheet(f"background-color: {color.name()};")
            
            # Auto-apply theme with new color
            app = QApplication.instance()
            self.theme_manager.apply_theme(app, current_theme)
    
    @pyqtSlot()
    def reset_colors(self):
        """Reset colors to theme defaults"""
        current_theme = self.theme_manager.get_current_theme()
        self.theme_manager.reset_custom_colors(current_theme)
        
        # Re-apply theme
        app = QApplication.instance()
        self.theme_manager.apply_theme(app, current_theme)
        self.update_current_theme()
        
        QMessageBox.information(self, "Colors Reset", "Theme colors have been reset to defaults.")
    
    @pyqtSlot()
    def apply_current_theme(self):
        """Apply the currently selected theme"""
        checked_button = self.theme_buttons.checkedButton()
        if checked_button:
            theme_name = checked_button.objectName()
            app = QApplication.instance()
            if self.theme_manager.apply_theme(app, theme_name):
                QMessageBox.information(self, "Theme Applied", f"'{theme_name}' theme has been applied successfully!")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
    import sys
    
    app = QApplication(sys.argv)
    
    # Create theme manager
    theme_manager = ThemeManager()
    
    # Create test window
    window = QMainWindow()
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # Add theme toggle widget
    theme_widget = ThemeToggleWidget(theme_manager)
    layout.addWidget(theme_widget)
    
    # Add some test widgets
    test_button = QPushButton("Test Button")
    layout.addWidget(test_button)
    
    window.setCentralWidget(central_widget)
    window.setWindowTitle("Theme Manager Test")
    window.resize(400, 600)
    
    # Apply initial theme
    theme_manager.apply_theme(app, "light")
    
    window.show()
    sys.exit(app.exec_())