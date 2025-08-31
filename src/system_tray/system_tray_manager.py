#!/usr/bin/env python3
"""
System Tray Manager for FileOrganizer
Provides system tray functionality with scenario-based workflows
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable
from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QProgressBar, QTextEdit, QWidget, QCheckBox,
    QGroupBox, QGridLayout, QSpinBox, QLineEdit, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFont

class ScenarioManager:
    """Manages predefined and custom scenarios"""
    
    PREDEFINED_SCENARIOS = {
        "pc_migration": {
            "name": "Transfer All Files (Old PC → New PC)",
            "description": "Migrate all personal files from old computer to new computer",
            "icon": "💻",
            "category": "migration",
            "steps": [
                {"type": "scan", "source": "auto", "patterns": ["Documents", "Pictures", "Videos", "Music", "Desktop"]},
                {"type": "analyze", "duplicates": True, "organize": True},
                {"type": "transfer", "preserve_structure": True, "verify": True}
            ],
            "settings": {
                "auto_organize": True,
                "skip_system_files": True,
                "create_backup": True,
                "verify_checksums": True
            }
        },
        
        "video_space_saver": {
            "name": "Transcode Videos to Save Space",
            "description": "Convert large video files to smaller H.265 format",
            "icon": "🎬",
            "category": "optimization",
            "steps": [
                {"type": "scan", "extensions": [".avi", ".mkv", ".mov", ".mp4"], "min_size": "100MB"},
                {"type": "analyze", "codec": "detect", "estimate_savings": True},
                {"type": "transcode", "preset": "h265_balanced", "delete_original": False}
            ],
            "settings": {
                "target_codec": "h265",
                "quality": "balanced",
                "keep_original": True,
                "hardware_accel": True,
                "batch_size": 3
            }
        },
        
        "audio_library_organize": {
            "name": "Organize Music Library",
            "description": "Sort and organize music files by artist, album, and genre",
            "icon": "🎵",
            "category": "organization",
            "steps": [
                {"type": "scan", "extensions": [".mp3", ".flac", ".m4a", ".wav", ".ogg"]},
                {"type": "analyze", "metadata": True, "duplicates": True},
                {"type": "organize", "structure": "{Artist}/{Album}/{Track} - {Title}"}
            ],
            "settings": {
                "folder_structure": "artist_album",
                "fix_metadata": True,
                "remove_duplicates": True,
                "normalize_names": True
            }
        },
        
        "photo_date_sort": {
            "name": "Sort Photos by Date",
            "description": "Organize photos into folders by year and month",
            "icon": "📸",
            "category": "organization",
            "steps": [
                {"type": "scan", "extensions": [".jpg", ".jpeg", ".png", ".tiff", ".raw", ".cr2", ".nef"]},
                {"type": "analyze", "exif": True, "duplicates": True},
                {"type": "organize", "structure": "{Year}/{Month}/{Date}"}
            ],
            "settings": {
                "date_format": "YYYY/MM",
                "use_exif_date": True,
                "handle_duplicates": "rename",
                "preserve_originals": False
            }
        },
        
        "duplicate_cleanup": {
            "name": "Find and Remove Duplicates",
            "description": "Scan for duplicate files and safely remove them",
            "icon": "🔍",
            "category": "cleanup",
            "steps": [
                {"type": "scan", "source": "all", "recursive": True},
                {"type": "analyze", "hash_compare": True, "size_compare": True},
                {"type": "cleanup", "action": "move_to_duplicates_folder"}
            ],
            "settings": {
                "comparison_method": "hash",
                "min_file_size": "1KB",
                "safety_mode": True,
                "backup_before_delete": True
            }
        },
        
        "cloud_backup": {
            "name": "Backup to Cloud Storage",
            "description": "Backup important files to cloud storage with compression",
            "icon": "☁️",
            "category": "backup",
            "steps": [
                {"type": "scan", "patterns": ["Documents", "Pictures"], "exclude": ["temp", "cache"]},
                {"type": "compress", "format": "zip", "encryption": True},
                {"type": "upload", "destination": "cloud", "verify": True}
            ],
            "settings": {
                "cloud_provider": "auto_detect",
                "compression_level": 6,
                "encrypt_backups": True,
                "incremental": True
            }
        },
        
        "downloads_organizer": {
            "name": "Organize Downloads to System Folders",
            "description": "Move downloads to Documents, Pictures, Videos, Music based on file type",
            "icon": "📥",
            "category": "organization",
            "steps": [
                {"type": "scan", "source": "Downloads", "recursive": False},
                {"type": "analyze", "file_types": True, "categorize": True},
                {"type": "organize", "method": "system_folders", "create_subfolders": True}
            ],
            "settings": {
                "move_to_system_folders": True,
                "recent_only": False,  # Organize all files or recent only
                "dry_run": False,  # Preview mode
                "backup_before_move": False,
                "handle_duplicates": "rename",  # rename, skip, or replace
                "exclude_patterns": [".tmp", ".crdownload", ".part"],
                "categories": {
                    "documents": True,  # Move docs to Documents folder
                    "images": True,     # Move images to Pictures folder
                    "videos": True,     # Move videos to Videos folder
                    "music": True,      # Move music to Music folder
                    "archives": True,   # Move archives to Documents/Archives
                    "executables": False, # Keep software in Downloads/Software
                    "code": True,       # Move code to Documents/Code
                    "ebooks": True      # Move ebooks to Documents/eBooks
                }
            }
        },
        
        "disk_space_analyzer": {
            "name": "Find Space-Consuming Files",
            "description": "Identify large files and folders consuming disk space",
            "icon": "💾",
            "category": "analysis",
            "steps": [
                {"type": "scan", "source": "all_drives", "analyze_size": True},
                {"type": "analyze", "largest_files": 100, "largest_folders": 50},
                {"type": "report", "format": "interactive", "recommendations": True}
            ],
            "settings": {
                "min_file_size": "10MB",
                "scan_system_files": False,
                "include_hidden": False,
                "sort_by": "size"
            }
        }
    }
    
    def __init__(self):
        self.custom_scenarios = self.load_custom_scenarios()
    
    def load_custom_scenarios(self) -> Dict:
        """Load user-defined custom scenarios"""
        config_dir = self.get_config_dir()
        scenarios_file = config_dir / 'custom_scenarios.json'
        
        if scenarios_file.exists():
            try:
                with open(scenarios_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading custom scenarios: {e}")
        
        return {}
    
    def save_custom_scenarios(self):
        """Save custom scenarios to file"""
        config_dir = self.get_config_dir()
        scenarios_file = config_dir / 'custom_scenarios.json'
        
        try:
            with open(scenarios_file, 'w') as f:
                json.dump(self.custom_scenarios, f, indent=2)
        except Exception as e:
            print(f"Error saving custom scenarios: {e}")
    
    def get_config_dir(self) -> Path:
        """Get configuration directory"""
        if sys.platform == 'win32':
            config_dir = Path(os.environ['APPDATA']) / 'FileOrganizer'
        else:
            config_dir = Path.home() / '.config' / 'fileorganizer'
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def get_all_scenarios(self) -> Dict:
        """Get all scenarios (predefined + custom)"""
        scenarios = self.PREDEFINED_SCENARIOS.copy()
        scenarios.update(self.custom_scenarios)
        return scenarios
    
    def get_scenarios_by_category(self) -> Dict[str, List]:
        """Get scenarios grouped by category"""
        categories = {}
        all_scenarios = self.get_all_scenarios()
        
        for scenario_id, scenario in all_scenarios.items():
            category = scenario.get('category', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append({
                'id': scenario_id,
                'scenario': scenario
            })
        
        return categories

class ScenarioExecutor(QThread):
    """Executes scenario steps with progress reporting"""
    
    progress_update = pyqtSignal(int, str)
    step_completed = pyqtSignal(str, dict)
    scenario_completed = pyqtSignal(bool, str)
    
    def __init__(self, scenario_id: str, scenario: Dict, settings: Dict):
        super().__init__()
        self.scenario_id = scenario_id
        self.scenario = scenario
        self.settings = settings
        self.is_cancelled = False
    
    def run(self):
        """Execute scenario steps"""
        try:
            steps = self.scenario.get('steps', [])
            total_steps = len(steps)
            
            for i, step in enumerate(steps):
                if self.is_cancelled:
                    break
                
                step_name = step.get('type', f'Step {i+1}')
                self.progress_update.emit(
                    int((i / total_steps) * 100),
                    f"Executing: {step_name}"
                )
                
                # Execute step based on type
                result = self.execute_step(step)
                self.step_completed.emit(step_name, result)
            
            if not self.is_cancelled:
                self.progress_update.emit(100, "Scenario completed!")
                self.scenario_completed.emit(True, "Scenario executed successfully")
            else:
                self.scenario_completed.emit(False, "Scenario cancelled by user")
                
        except Exception as e:
            self.scenario_completed.emit(False, f"Error executing scenario: {e}")
    
    def execute_step(self, step: Dict) -> Dict:
        """Execute a single scenario step"""
        step_type = step.get('type')
        
        if step_type == 'scan':
            return self.execute_scan_step(step)
        elif step_type == 'analyze':
            return self.execute_analyze_step(step)
        elif step_type == 'transfer':
            return self.execute_transfer_step(step)
        elif step_type == 'transcode':
            return self.execute_transcode_step(step)
        elif step_type == 'organize':
            return self.execute_organize_step(step)
        elif step_type == 'cleanup':
            return self.execute_cleanup_step(step)
        else:
            return {'status': 'skipped', 'reason': f'Unknown step type: {step_type}'}
    
    def execute_scan_step(self, step: Dict) -> Dict:
        """Execute file scanning step"""
        # TODO: Implement actual file scanning
        import time
        time.sleep(2)  # Simulate work
        return {'status': 'completed', 'files_found': 1250}
    
    def execute_analyze_step(self, step: Dict) -> Dict:
        """Execute file analysis step"""
        # TODO: Implement actual analysis
        import time
        time.sleep(1.5)
        return {'status': 'completed', 'duplicates_found': 45, 'space_analysis': '2.3GB can be saved'}
    
    def execute_transfer_step(self, step: Dict) -> Dict:
        """Execute file transfer step"""
        # TODO: Implement actual transfer
        import time
        time.sleep(3)
        return {'status': 'completed', 'files_transferred': 1200, 'failed': 5}
    
    def execute_transcode_step(self, step: Dict) -> Dict:
        """Execute video transcoding step"""
        # TODO: Implement actual transcoding
        import time
        time.sleep(4)
        return {'status': 'completed', 'videos_transcoded': 25, 'space_saved': '1.8GB'}
    
    def execute_organize_step(self, step: Dict) -> Dict:
        """Execute file organization step"""
        method = step.get('method', 'generic')
        
        if method == 'system_folders':
            # Use the downloads organizer for system folder organization
            return self.execute_downloads_organization()
        else:
            # Generic organization
            import time
            time.sleep(2)
            return {'status': 'completed', 'files_organized': 1150, 'folders_created': 85}
    
    def execute_downloads_organization(self) -> Dict:
        """Execute downloads folder organization to system folders"""
        try:
            # Import and use the downloads organizer
            import sys
            import os
            from pathlib import Path
            
            # Add src directory to path to import downloads_organizer
            current_file = Path(__file__)
            src_root = current_file.parent.parent  # Go up from system_tray to src
            sys.path.insert(0, str(src_root))
            
            from transfers.downloads_organizer import DownloadsOrganizer
            
            organizer = DownloadsOrganizer()
            
            # Get settings from scenario (would be passed in real implementation)
            recent_only = self.settings.get('recent_only', False)
            dry_run = self.settings.get('dry_run', False)
            
            # Execute organization
            results = organizer.organize_downloads(
                recent_only=recent_only,
                dry_run=dry_run
            )
            
            # Convert results to scenario format
            return {
                'status': 'completed',
                'files_organized': len(results['moved_files']),
                'files_skipped': len(results['skipped_files']),
                'files_error': len(results['error_files']),
                'categories_used': list(results['categories_used']),
                'dry_run': results['dry_run'],
                'details': results
            }
            
        except ImportError as e:
            return {
                'status': 'error',
                'error': f'Downloads organizer module not found: {e}'
            }
        except Exception as e:
            return {
                'status': 'error', 
                'error': f'Downloads organization failed: {e}'
            }
    
    def execute_cleanup_step(self, step: Dict) -> Dict:
        """Execute cleanup step"""
        # TODO: Implement actual cleanup
        import time
        time.sleep(1)
        return {'status': 'completed', 'files_removed': 45, 'space_freed': '234MB'}
    
    def cancel(self):
        """Cancel scenario execution"""
        self.is_cancelled = True

class ScenarioDialog(QDialog):
    """Dialog for selecting and configuring scenarios"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scenario_manager = ScenarioManager()
        self.selected_scenario = None
        self.setup_ui()
        self.load_scenarios()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("FileOrganizer - Select Scenario")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Choose a file management scenario:")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Scenario selection
        self.scenario_combo = QComboBox()
        self.scenario_combo.currentTextChanged.connect(self.on_scenario_selected)
        layout.addWidget(self.scenario_combo)
        
        # Description
        self.description_text = QTextEdit()
        self.description_text.setMaximumHeight(100)
        self.description_text.setReadOnly(True)
        layout.addWidget(self.description_text)
        
        # Settings group
        self.settings_group = QGroupBox("Scenario Settings")
        self.settings_layout = QGridLayout(self.settings_group)
        layout.addWidget(self.settings_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.custom_button = QPushButton("Create Custom")
        self.custom_button.clicked.connect(self.create_custom_scenario)
        button_layout.addWidget(self.custom_button)
        
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.run_button = QPushButton("Run Scenario")
        self.run_button.clicked.connect(self.run_scenario)
        self.run_button.setDefault(True)
        button_layout.addWidget(self.run_button)
        
        layout.addLayout(button_layout)
    
    def load_scenarios(self):
        """Load scenarios into the combo box"""
        scenarios_by_category = self.scenario_manager.get_scenarios_by_category()
        
        for category, scenarios in scenarios_by_category.items():
            category_name = category.replace('_', ' ').title()
            self.scenario_combo.addItem(f"--- {category_name} ---", None)
            
            for scenario_data in scenarios:
                scenario_id = scenario_data['id']
                scenario = scenario_data['scenario']
                icon = scenario.get('icon', '📁')
                name = scenario.get('name', scenario_id)
                
                self.scenario_combo.addItem(f"{icon} {name}", scenario_id)
        
        if self.scenario_combo.count() > 1:
            self.scenario_combo.setCurrentIndex(1)  # Skip first category header
    
    def on_scenario_selected(self, text):
        """Handle scenario selection"""
        scenario_id = self.scenario_combo.currentData()
        
        if scenario_id:
            all_scenarios = self.scenario_manager.get_all_scenarios()
            scenario = all_scenarios.get(scenario_id)
            
            if scenario:
                self.selected_scenario = scenario_id
                self.description_text.setText(scenario.get('description', ''))
                self.setup_scenario_settings(scenario)
        else:
            self.selected_scenario = None
            self.description_text.clear()
            self.clear_settings()
    
    def setup_scenario_settings(self, scenario: Dict):
        """Setup settings UI for selected scenario"""
        self.clear_settings()
        
        settings = scenario.get('settings', {})
        row = 0
        
        for key, value in settings.items():
            label_text = key.replace('_', ' ').title()
            label = QLabel(f"{label_text}:")
            self.settings_layout.addWidget(label, row, 0)
            
            if isinstance(value, bool):
                widget = QCheckBox()
                widget.setChecked(value)
                widget.setObjectName(key)
            elif isinstance(value, int):
                widget = QSpinBox()
                widget.setValue(value)
                widget.setRange(0, 999999)
                widget.setObjectName(key)
            elif isinstance(value, str):
                widget = QLineEdit()
                widget.setText(value)
                widget.setObjectName(key)
            else:
                widget = QLineEdit()
                widget.setText(str(value))
                widget.setObjectName(key)
            
            self.settings_layout.addWidget(widget, row, 1)
            row += 1
    
    def clear_settings(self):
        """Clear settings UI"""
        while self.settings_layout.count():
            child = self.settings_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def get_scenario_settings(self) -> Dict:
        """Get current scenario settings from UI"""
        settings = {}
        
        for i in range(self.settings_layout.count()):
            widget = self.settings_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'objectName') and widget.objectName():
                key = widget.objectName()
                
                if isinstance(widget, QCheckBox):
                    settings[key] = widget.isChecked()
                elif isinstance(widget, QSpinBox):
                    settings[key] = widget.value()
                elif isinstance(widget, QLineEdit):
                    settings[key] = widget.text()
        
        return settings
    
    def create_custom_scenario(self):
        """Create a custom scenario"""
        # TODO: Implement custom scenario creator
        QMessageBox.information(self, "Custom Scenarios", 
                               "Custom scenario creator will be available in the next version.")
    
    def run_scenario(self):
        """Run the selected scenario"""
        if not self.selected_scenario:
            QMessageBox.warning(self, "No Selection", "Please select a scenario to run.")
            return
        
        settings = self.get_scenario_settings()
        self.accept()
        
        # Store selection for parent to access
        self.result_data = {
            'scenario_id': self.selected_scenario,
            'settings': settings
        }

class SystemTrayManager(QSystemTrayIcon):
    """System tray manager with scenario-based functionality"""
    
    def __init__(self, app: QApplication):
        # Create tray icon
        icon = self.create_tray_icon()
        super().__init__(icon, app)
        
        self.app = app
        self.scenario_manager = ScenarioManager()
        self.current_executor = None
        
        # Settings
        self.settings = QSettings('FileOrganizer', 'SystemTray')
        
        # Setup tray
        self.setup_context_menu()
        self.setToolTip("FileOrganizer - System Tray")
        
        # Connect signals
        self.activated.connect(self.on_tray_activated)
        self.messageClicked.connect(self.on_message_clicked)
        
        # Show tray icon
        self.show()
        
        # Show startup message
        if self.settings.value('show_startup_message', True, bool):
            self.showMessage(
                "FileOrganizer",
                "FileOrganizer is running in the system tray.\nRight-click for options.",
                QSystemTrayIcon.Information,
                3000
            )
    
    def create_tray_icon(self) -> QIcon:
        """Create system tray icon"""
        # Create a simple icon (in real implementation, use proper icon file)
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setPen(Qt.blue)
        painter.setBrush(Qt.lightGray)
        painter.drawEllipse(2, 2, 12, 12)
        painter.setPen(Qt.darkBlue)
        painter.drawText(6, 11, "F")
        painter.end()
        
        return QIcon(pixmap)
    
    def setup_context_menu(self):
        """Setup system tray context menu"""
        menu = QMenu()
        
        # Quick scenarios
        scenarios_menu = menu.addMenu("🎯 Quick Scenarios")
        self.add_quick_scenarios(scenarios_menu)
        
        menu.addSeparator()
        
        # Tools submenu
        tools_menu = menu.addMenu("🔧 Tools")
        
        photo_action = QAction("📸 Photo Transfer", self)
        photo_action.triggered.connect(self.launch_photo_transfer)
        tools_menu.addAction(photo_action)
        
        audio_action = QAction("🎵 Audio Transfer", self)
        audio_action.triggered.connect(self.launch_audio_transfer)
        tools_menu.addAction(audio_action)
        
        video_action = QAction("🎬 Video Transfer", self)
        video_action.triggered.connect(self.launch_video_transfer)
        tools_menu.addAction(video_action)
        
        tools_menu.addSeparator()
        
        batch_action = QAction("📦 Batch Transfer", self)
        batch_action.triggered.connect(self.launch_batch_transfer)
        tools_menu.addAction(batch_action)
        
        menu.addSeparator()
        
        # Main window
        main_action = QAction("🏠 Open Main Window", self)
        main_action.triggered.connect(self.show_main_window)
        menu.addAction(main_action)
        
        # Custom scenarios
        custom_action = QAction("⚙️ Custom Scenario...", self)
        custom_action.triggered.connect(self.show_scenario_dialog)
        menu.addAction(custom_action)
        
        menu.addSeparator()
        
        # Settings
        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        # About
        about_action = QAction("ℹ️ About", self)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)
        
        menu.addSeparator()
        
        # Exit
        exit_action = QAction("❌ Exit", self)
        exit_action.triggered.connect(self.exit_application)
        menu.addAction(exit_action)
        
        self.setContextMenu(menu)
    
    def add_quick_scenarios(self, menu: QMenu):
        """Add quick scenario actions to menu"""
        # Add most common scenarios to quick menu
        quick_scenarios = [
            'pc_migration',
            'video_space_saver',
            'downloads_organizer',
            'photo_date_sort',
            'duplicate_cleanup'
        ]
        
        all_scenarios = self.scenario_manager.get_all_scenarios()
        
        for scenario_id in quick_scenarios:
            if scenario_id in all_scenarios:
                scenario = all_scenarios[scenario_id]
                icon = scenario.get('icon', '📁')
                name = scenario.get('name', scenario_id)
                
                action = QAction(f"{icon} {name}", self)
                action.triggered.connect(lambda checked, sid=scenario_id: self.run_quick_scenario(sid))
                menu.addAction(action)
        
        menu.addSeparator()
        menu.addAction("📋 More Scenarios...", self.show_scenario_dialog)
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_scenario_dialog()
        elif reason == QSystemTrayIcon.MiddleClick:
            self.show_main_window()
    
    def on_message_clicked(self):
        """Handle tray message click"""
        self.show_main_window()
    
    def run_quick_scenario(self, scenario_id: str):
        """Run a quick scenario with default settings"""
        all_scenarios = self.scenario_manager.get_all_scenarios()
        scenario = all_scenarios.get(scenario_id)
        
        if scenario:
            # Use default settings
            settings = scenario.get('settings', {})
            self.execute_scenario(scenario_id, scenario, settings)
        else:
            self.showMessage(
                "Error",
                f"Scenario '{scenario_id}' not found.",
                QSystemTrayIcon.Critical,
                3000
            )
    
    def show_scenario_dialog(self):
        """Show scenario selection dialog"""
        dialog = ScenarioDialog()
        
        if dialog.exec_() == QDialog.Accepted and hasattr(dialog, 'result_data'):
            data = dialog.result_data
            scenario_id = data['scenario_id']
            settings = data['settings']
            
            all_scenarios = self.scenario_manager.get_all_scenarios()
            scenario = all_scenarios.get(scenario_id)
            
            if scenario:
                self.execute_scenario(scenario_id, scenario, settings)
    
    def execute_scenario(self, scenario_id: str, scenario: Dict, settings: Dict):
        """Execute a scenario"""
        if self.current_executor and self.current_executor.isRunning():
            reply = QMessageBox.question(
                None,
                "Scenario Running",
                "Another scenario is currently running. Stop it and start new one?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.current_executor.cancel()
                self.current_executor.wait()
            else:
                return
        
        # Show starting message
        scenario_name = scenario.get('name', scenario_id)
        self.showMessage(
            "Scenario Started",
            f"Running: {scenario_name}",
            QSystemTrayIcon.Information,
            2000
        )
        
        # Start executor
        self.current_executor = ScenarioExecutor(scenario_id, scenario, settings)
        self.current_executor.progress_update.connect(self.on_scenario_progress)
        self.current_executor.scenario_completed.connect(self.on_scenario_completed)
        self.current_executor.start()
    
    def on_scenario_progress(self, progress: int, status: str):
        """Handle scenario progress updates"""
        # Update tray tooltip with progress
        self.setToolTip(f"FileOrganizer - {status} ({progress}%)")
        
        # You could also show progress in a small window if needed
    
    def on_scenario_completed(self, success: bool, message: str):
        """Handle scenario completion"""
        self.setToolTip("FileOrganizer - System Tray")
        
        if success:
            self.showMessage(
                "Scenario Complete",
                message,
                QSystemTrayIcon.Information,
                5000
            )
        else:
            self.showMessage(
                "Scenario Failed",
                message,
                QSystemTrayIcon.Critical,
                5000
            )
        
        self.current_executor = None
    
    def launch_photo_transfer(self):
        """Launch photo transfer tool"""
        try:
            import subprocess
            import sys
            subprocess.Popen([sys.executable, "photo_transfer.py"])
        except Exception as e:
            self.showMessage("Error", f"Failed to launch Photo Transfer: {e}", QSystemTrayIcon.Critical)
    
    def launch_audio_transfer(self):
        """Launch audio transfer tool"""
        try:
            import subprocess
            import sys
            subprocess.Popen([sys.executable, "audio_transfer.py"])
        except Exception as e:
            self.showMessage("Error", f"Failed to launch Audio Transfer: {e}", QSystemTrayIcon.Critical)
    
    def launch_video_transfer(self):
        """Launch video transfer tool"""
        try:
            import subprocess
            import sys
            subprocess.Popen([sys.executable, "video_transfer.py"])
        except Exception as e:
            self.showMessage("Error", f"Failed to launch Video Transfer: {e}", QSystemTrayIcon.Critical)
    
    def launch_batch_transfer(self):
        """Launch batch transfer dialog"""
        self.showMessage("Batch Transfer", "Batch transfer functionality coming soon!", QSystemTrayIcon.Information)
    
    def show_main_window(self):
        """Show main FileOrganizer window"""
        try:
            import subprocess
            import sys
            subprocess.Popen([sys.executable, "main.py"])
        except Exception as e:
            self.showMessage("Error", f"Failed to launch main window: {e}", QSystemTrayIcon.Critical)
    
    def show_settings(self):
        """Show settings dialog"""
        # TODO: Implement settings dialog
        self.showMessage("Settings", "Settings dialog coming soon!", QSystemTrayIcon.Information)
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            None,
            "About FileOrganizer",
            "FileOrganizer v3.0\n\n"
            "Advanced file organization tool with scenario-based workflows.\n\n"
            "Features:\n"
            "• System tray operation\n"
            "• Predefined scenarios for common tasks\n"
            "• Media transfer tools with transcoding\n"
            "• Intelligent file organization\n\n"
            "© 2024 FileOrganizer Team"
        )
    
    def exit_application(self):
        """Exit the application"""
        if self.current_executor and self.current_executor.isRunning():
            reply = QMessageBox.question(
                None,
                "Scenario Running",
                "A scenario is currently running. Exit anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            self.current_executor.cancel()
        
        self.hide()
        QApplication.quit()

def main():
    """Main entry point for system tray application"""
    import sys
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray
    
    # Check if system tray is available
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None,
            "System Tray",
            "System tray is not available on this system."
        )
        sys.exit(1)
    
    # Create system tray manager
    tray = SystemTrayManager(app)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()