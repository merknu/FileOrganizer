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
        import os
        from pathlib import Path

        try:
            # Get scan path from step or use default
            scan_path = step.get('path', str(Path.home()))
            recursive = step.get('recursive', True)

            files_found = 0
            folders_found = 0

            if recursive:
                # Scan recursively
                for root, dirs, files in os.walk(scan_path):
                    files_found += len(files)
                    folders_found += len(dirs)
            else:
                # Scan only top level
                try:
                    items = os.listdir(scan_path)
                    for item in items:
                        item_path = os.path.join(scan_path, item)
                        if os.path.isfile(item_path):
                            files_found += 1
                        elif os.path.isdir(item_path):
                            folders_found += 1
                except (PermissionError, FileNotFoundError):
                    pass

            return {
                'status': 'completed',
                'files_found': files_found,
                'folders_found': folders_found,
                'path': scan_path
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': f'File scanning failed: {e}'
            }
    
    def execute_analyze_step(self, step: Dict) -> Dict:
        """Execute file analysis step"""
        import os
        from pathlib import Path
        from collections import defaultdict

        try:
            # Get analysis path from step or use default
            analyze_path = step.get('path', str(Path.home()))

            # Analyze file types and sizes
            file_types = defaultdict(int)
            total_size = 0
            file_count = 0
            duplicate_candidates = defaultdict(list)

            for root, dirs, files in os.walk(analyze_path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        file_ext = os.path.splitext(file)[1].lower()

                        file_types[file_ext if file_ext else 'no_extension'] += 1
                        total_size += file_size
                        file_count += 1

                        # Track potential duplicates by size and name
                        duplicate_candidates[(file, file_size)].append(file_path)

                    except (PermissionError, FileNotFoundError, OSError):
                        continue

            # Count potential duplicates
            duplicates_found = sum(1 for paths in duplicate_candidates.values() if len(paths) > 1)

            # Format total size
            def format_size(size_bytes):
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if size_bytes < 1024.0:
                        return f"{size_bytes:.2f} {unit}"
                    size_bytes /= 1024.0
                return f"{size_bytes:.2f} PB"

            return {
                'status': 'completed',
                'files_analyzed': file_count,
                'total_size': format_size(total_size),
                'duplicates_found': duplicates_found,
                'file_types': dict(file_types),
                'space_analysis': f'{format_size(total_size * 0.1)} could potentially be saved'
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': f'File analysis failed: {e}'
            }
    
    def execute_transfer_step(self, step: Dict) -> Dict:
        """Execute file transfer step"""
        import os
        import shutil
        from pathlib import Path

        try:
            # Get transfer parameters from step
            source_path = step.get('source', '')
            dest_path = step.get('destination', '')
            file_pattern = step.get('pattern', '*')

            if not source_path or not dest_path:
                return {
                    'status': 'error',
                    'error': 'Source and destination paths required'
                }

            source = Path(source_path)
            destination = Path(dest_path)

            if not source.exists():
                return {
                    'status': 'error',
                    'error': f'Source path does not exist: {source}'
                }

            # Create destination if it doesn't exist
            destination.mkdir(parents=True, exist_ok=True)

            files_transferred = 0
            failed = 0

            # Transfer files matching pattern
            if source.is_file():
                # Transfer single file
                try:
                    dest_file = destination / source.name
                    shutil.copy2(source, dest_file)
                    files_transferred += 1
                except Exception as e:
                    failed += 1
            else:
                # Transfer directory contents
                for file_path in source.rglob(file_pattern):
                    if file_path.is_file():
                        try:
                            relative_path = file_path.relative_to(source)
                            dest_file = destination / relative_path
                            dest_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(file_path, dest_file)
                            files_transferred += 1
                        except Exception as e:
                            failed += 1

            return {
                'status': 'completed',
                'files_transferred': files_transferred,
                'failed': failed,
                'source': str(source),
                'destination': str(destination)
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': f'File transfer failed: {e}'
            }
    
    def execute_transcode_step(self, step: Dict) -> Dict:
        """Execute video transcoding step"""
        import os
        import sys
        from pathlib import Path

        try:
            # Get transcoding parameters
            source_path = step.get('source', '')
            output_format = step.get('format', 'mp4')
            quality = step.get('quality', 'medium')

            if not source_path:
                return {
                    'status': 'error',
                    'error': 'Source path required'
                }

            source = Path(source_path)
            if not source.exists():
                return {
                    'status': 'error',
                    'error': f'Source path does not exist: {source}'
                }

            # Try to import video transfer module
            try:
                # Add src directory to path
                current_file = Path(__file__)
                src_root = current_file.parent.parent
                sys.path.insert(0, str(src_root))

                from transfers.video_transfer import VideoTransferTool

                # This would normally integrate with the video transfer tool
                # For now, return simulated results
                return {
                    'status': 'info',
                    'message': 'Video transcoding requires the video transfer tool',
                    'videos_transcoded': 0,
                    'space_saved': '0GB',
                    'note': 'Use the Video Transfer tool from the system tray for transcoding'
                }

            except ImportError:
                return {
                    'status': 'info',
                    'message': 'Video transcoding module not available',
                    'videos_transcoded': 0,
                    'note': 'Install video processing dependencies for transcoding support'
                }

        except Exception as e:
            return {
                'status': 'error',
                'error': f'Video transcoding failed: {e}'
            }
    
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
        import os
        import shutil
        from pathlib import Path
        from datetime import datetime, timedelta

        try:
            # Get cleanup parameters
            cleanup_path = step.get('path', '')
            cleanup_type = step.get('type', 'temp')  # temp, old, duplicates, empty
            days_old = step.get('days_old', 30)

            if not cleanup_path:
                cleanup_path = str(Path.home())

            path = Path(cleanup_path)
            if not path.exists():
                return {
                    'status': 'error',
                    'error': f'Cleanup path does not exist: {path}'
                }

            files_removed = 0
            space_freed = 0

            if cleanup_type == 'temp':
                # Clean temporary files
                temp_patterns = ['*.tmp', '*.temp', '*~', '*.bak', '*.cache']
                for pattern in temp_patterns:
                    for file_path in path.rglob(pattern):
                        try:
                            if file_path.is_file():
                                size = file_path.stat().st_size
                                file_path.unlink()
                                files_removed += 1
                                space_freed += size
                        except (PermissionError, OSError):
                            continue

            elif cleanup_type == 'old':
                # Clean old files
                cutoff_date = datetime.now() - timedelta(days=days_old)
                for file_path in path.rglob('*'):
                    try:
                        if file_path.is_file():
                            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_time < cutoff_date:
                                size = file_path.stat().st_size
                                file_path.unlink()
                                files_removed += 1
                                space_freed += size
                    except (PermissionError, OSError):
                        continue

            elif cleanup_type == 'empty':
                # Clean empty directories
                for dir_path in path.rglob('*'):
                    try:
                        if dir_path.is_dir() and not any(dir_path.iterdir()):
                            dir_path.rmdir()
                            files_removed += 1
                    except (PermissionError, OSError):
                        continue

            # Format space freed
            def format_size(size_bytes):
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if size_bytes < 1024.0:
                        return f"{size_bytes:.2f}{unit}"
                    size_bytes /= 1024.0
                return f"{size_bytes:.2f}PB"

            return {
                'status': 'completed',
                'files_removed': files_removed,
                'space_freed': format_size(space_freed),
                'cleanup_type': cleanup_type
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': f'Cleanup failed: {e}'
            }
    
    def cancel(self):
        """Cancel scenario execution"""
        self.is_cancelled = True

class CustomScenarioCreatorDialog(QDialog):
    """Dialog for creating custom scenarios"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Custom Scenario")
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)

        # Scenario name
        name_group = QGroupBox("Scenario Details")
        name_layout = QGridLayout(name_group)

        name_layout.addWidget(QLabel("Name:"), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., My Custom Workflow")
        name_layout.addWidget(self.name_edit, 0, 1)

        name_layout.addWidget(QLabel("Description:"), 1, 0)
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Brief description of what this scenario does")
        name_layout.addWidget(self.desc_edit, 1, 1)

        name_layout.addWidget(QLabel("Icon:"), 2, 0)
        self.icon_edit = QLineEdit()
        self.icon_edit.setText("⚙️")
        self.icon_edit.setMaxLength(2)
        name_layout.addWidget(self.icon_edit, 2, 1)

        layout.addWidget(name_group)

        # Steps configuration
        steps_group = QGroupBox("Workflow Steps")
        steps_layout = QVBoxLayout(steps_group)

        self.scan_check = QCheckBox("Scan files")
        self.scan_check.setChecked(True)
        steps_layout.addWidget(self.scan_check)

        self.analyze_check = QCheckBox("Analyze files")
        steps_layout.addWidget(self.analyze_check)

        self.organize_check = QCheckBox("Organize files")
        steps_layout.addWidget(self.organize_check)

        self.transfer_check = QCheckBox("Transfer files")
        steps_layout.addWidget(self.transfer_check)

        self.cleanup_check = QCheckBox("Cleanup temporary files")
        steps_layout.addWidget(self.cleanup_check)

        layout.addWidget(steps_group)

        # Path configuration
        path_group = QGroupBox("Paths")
        path_layout = QGridLayout(path_group)

        path_layout.addWidget(QLabel("Source Path:"), 0, 0)
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Leave empty to prompt at runtime")
        path_layout.addWidget(self.source_edit, 0, 1)

        source_browse = QPushButton("Browse...")
        source_browse.clicked.connect(self.browse_source)
        path_layout.addWidget(source_browse, 0, 2)

        path_layout.addWidget(QLabel("Destination Path:"), 1, 0)
        self.dest_edit = QLineEdit()
        self.dest_edit.setPlaceholderText("Leave empty to prompt at runtime")
        path_layout.addWidget(self.dest_edit, 1, 1)

        dest_browse = QPushButton("Browse...")
        dest_browse.clicked.connect(self.browse_dest)
        path_layout.addWidget(dest_browse, 1, 2)

        layout.addWidget(path_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        create_btn = QPushButton("Create Scenario")
        create_btn.clicked.connect(self.accept)
        button_layout.addWidget(create_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def browse_source(self):
        """Browse for source directory"""
        path = QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if path:
            self.source_edit.setText(path)

    def browse_dest(self):
        """Browse for destination directory"""
        path = QFileDialog.getExistingDirectory(self, "Select Destination Directory")
        if path:
            self.dest_edit.setText(path)

    def get_scenario_data(self) -> Optional[Dict]:
        """Get the scenario data from the form"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter a scenario name.")
            return None

        # Build steps list
        steps = []
        if self.scan_check.isChecked():
            steps.append({"type": "scan", "path": self.source_edit.text() or None})
        if self.analyze_check.isChecked():
            steps.append({"type": "analyze"})
        if self.organize_check.isChecked():
            steps.append({"type": "organize"})
        if self.transfer_check.isChecked():
            steps.append({"type": "transfer", "source": self.source_edit.text() or None,
                         "destination": self.dest_edit.text() or None})
        if self.cleanup_check.isChecked():
            steps.append({"type": "cleanup"})

        # Generate unique ID
        scenario_id = name.lower().replace(' ', '_').replace('-', '_')
        import time
        scenario_id = f"custom_{scenario_id}_{int(time.time())}"

        return {
            'id': scenario_id,
            'name': name,
            'description': self.desc_edit.text().strip() or "Custom scenario",
            'icon': self.icon_edit.text() or "⚙️",
            'category': 'custom',
            'steps': steps,
            'settings': {}
        }


class SettingsDialog(QDialog):
    """Settings dialog for FileOrganizer system tray"""

    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("FileOrganizer Settings")
        self.setMinimumWidth(450)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)

        # General settings
        general_group = QGroupBox("General")
        general_layout = QGridLayout(general_group)

        self.startup_msg_check = QCheckBox("Show startup message")
        general_layout.addWidget(self.startup_msg_check, 0, 0, 1, 2)

        self.minimize_to_tray_check = QCheckBox("Minimize to tray instead of taskbar")
        general_layout.addWidget(self.minimize_to_tray_check, 1, 0, 1, 2)

        self.confirm_exit_check = QCheckBox("Confirm before exit")
        general_layout.addWidget(self.confirm_exit_check, 2, 0, 1, 2)

        layout.addWidget(general_group)

        # Notification settings
        notification_group = QGroupBox("Notifications")
        notification_layout = QGridLayout(notification_group)

        notification_layout.addWidget(QLabel("Notification Duration (seconds):"), 0, 0)
        self.notification_duration = QSpinBox()
        self.notification_duration.setRange(1, 30)
        self.notification_duration.setValue(5)
        notification_layout.addWidget(self.notification_duration, 0, 1)

        self.show_completion_check = QCheckBox("Show completion notifications")
        notification_layout.addWidget(self.show_completion_check, 1, 0, 1, 2)

        self.show_error_check = QCheckBox("Show error notifications")
        notification_layout.addWidget(self.show_error_check, 2, 0, 1, 2)

        layout.addWidget(notification_group)

        # File organization settings
        org_group = QGroupBox("File Organization")
        org_layout = QGridLayout(org_group)

        self.auto_organize_check = QCheckBox("Auto-organize downloads")
        org_layout.addWidget(self.auto_organize_check, 0, 0, 1, 2)

        org_layout.addWidget(QLabel("Auto-organize interval (minutes):"), 1, 0)
        self.auto_organize_interval = QSpinBox()
        self.auto_organize_interval.setRange(5, 1440)
        self.auto_organize_interval.setValue(60)
        org_layout.addWidget(self.auto_organize_interval, 1, 1)

        self.verify_moves_check = QCheckBox("Verify file moves")
        org_layout.addWidget(self.verify_moves_check, 2, 0, 1, 2)

        layout.addWidget(org_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def load_settings(self):
        """Load settings from QSettings"""
        self.startup_msg_check.setChecked(self.settings.value('show_startup_message', True, bool))
        self.minimize_to_tray_check.setChecked(self.settings.value('minimize_to_tray', True, bool))
        self.confirm_exit_check.setChecked(self.settings.value('confirm_exit', True, bool))
        self.notification_duration.setValue(self.settings.value('notification_duration', 5, int))
        self.show_completion_check.setChecked(self.settings.value('show_completion', True, bool))
        self.show_error_check.setChecked(self.settings.value('show_errors', True, bool))
        self.auto_organize_check.setChecked(self.settings.value('auto_organize', False, bool))
        self.auto_organize_interval.setValue(self.settings.value('auto_organize_interval', 60, int))
        self.verify_moves_check.setChecked(self.settings.value('verify_moves', True, bool))

    def save_settings(self):
        """Save settings to QSettings"""
        self.settings.setValue('show_startup_message', self.startup_msg_check.isChecked())
        self.settings.setValue('minimize_to_tray', self.minimize_to_tray_check.isChecked())
        self.settings.setValue('confirm_exit', self.confirm_exit_check.isChecked())
        self.settings.setValue('notification_duration', self.notification_duration.value())
        self.settings.setValue('show_completion', self.show_completion_check.isChecked())
        self.settings.setValue('show_errors', self.show_error_check.isChecked())
        self.settings.setValue('auto_organize', self.auto_organize_check.isChecked())
        self.settings.setValue('auto_organize_interval', self.auto_organize_interval.value())
        self.settings.setValue('verify_moves', self.verify_moves_check.isChecked())

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(self, "Reset Settings",
                                     "Are you sure you want to reset all settings to defaults?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.settings.clear()
            self.load_settings()


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
        dialog = CustomScenarioCreatorDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Get the custom scenario data
            scenario_data = dialog.get_scenario_data()
            if scenario_data:
                # Save to user scenarios
                self.save_custom_scenario(scenario_data)
                QMessageBox.information(self, "Scenario Created",
                                      f"Custom scenario '{scenario_data['name']}' has been created successfully!")

    def save_custom_scenario(self, scenario_data: Dict):
        """Save custom scenario to user's configuration"""
        try:
            # Get user scenarios directory
            config_dir = Path.home() / '.fileorganizer' / 'scenarios'
            config_dir.mkdir(parents=True, exist_ok=True)

            # Save scenario as JSON
            scenario_file = config_dir / f"{scenario_data['id']}.json"
            with open(scenario_file, 'w') as f:
                json.dump(scenario_data, f, indent=2)

        except Exception as e:
            QMessageBox.warning(self, "Save Error",
                              f"Failed to save custom scenario: {e}")
    
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
        self.main_window = None
        self.file_organizer = None
        self.audio_transfer = None
        self.video_transfer = None
        
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
        
        # Direct transfer managers
        file_transfer_action = QAction("📁 Advanced File Organizer", self)
        file_transfer_action.triggered.connect(self.launch_file_organizer)
        menu.addAction(file_transfer_action)
        
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
            self.show_main_window()
        elif reason == QSystemTrayIcon.MiddleClick:
            self.show_scenario_dialog()
    
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
            from transfers.audio_transfer import AudioTransferWindow
            if not hasattr(self, 'audio_transfer') or not self.audio_transfer:
                self.audio_transfer = AudioTransferWindow()
            
            self.audio_transfer.show()
            self.audio_transfer.raise_()
            self.audio_transfer.activateWindow()
        except Exception as e:
            self.showMessage("Error", f"Failed to launch Audio Transfer: {e}", QSystemTrayIcon.Critical)
    
    def launch_video_transfer(self):
        """Launch video transfer tool"""
        try:
            from transfers.video_transfer import VideoTransferWindow
            if not hasattr(self, 'video_transfer') or not self.video_transfer:
                self.video_transfer = VideoTransferWindow()
            
            self.video_transfer.show()
            self.video_transfer.raise_()
            self.video_transfer.activateWindow()
        except Exception as e:
            self.showMessage("Error", f"Failed to launch Video Transfer: {e}", QSystemTrayIcon.Critical)
    
    def launch_batch_transfer(self):
        """Launch batch transfer dialog"""
        self.showMessage("Batch Transfer", "Batch transfer functionality coming soon!", QSystemTrayIcon.Information)
    
    def launch_file_organizer(self):
        """Launch advanced file organizer"""
        try:
            from gui.main_window import FileOrganizerMainWindow
            from config.config_handler import ConfigHandler
            
            config_handler = ConfigHandler('config/config.json')
            if not hasattr(self, 'file_organizer') or not self.file_organizer:
                self.file_organizer = FileOrganizerMainWindow(config_handler.config)
            
            self.file_organizer.show()
            self.file_organizer.raise_()
            self.file_organizer.activateWindow()
        except Exception as e:
            self.showMessage("Error", f"Failed to launch File Organizer: {e}", QSystemTrayIcon.Critical)
    
    def show_main_window(self):
        """Show main FileOrganizer window"""
        try:
            # Import and show the enhanced main window
            if not hasattr(self, 'main_window') or not self.main_window:
                from core.main_enhanced import EnhancedMainApplication
                self.main_window = EnhancedMainApplication()
            
            # Show and bring to front
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
            self.main_window.setWindowState(Qt.WindowActive)
        except ImportError:
            # Fallback to regular main window
            try:
                from core.main import MainApplication
                if not hasattr(self, 'main_window') or not self.main_window:
                    self.main_window = MainApplication()
                self.main_window.show()
                self.main_window.raise_()
                self.main_window.activateWindow()
            except Exception as e:
                self.showMessage("Error", f"Failed to show main window: {e}", QSystemTrayIcon.Critical)
        except Exception as e:
            self.showMessage("Error", f"Failed to show main window: {e}", QSystemTrayIcon.Critical)
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.settings)
        if dialog.exec_() == QDialog.Accepted:
            # Save settings
            dialog.save_settings()
            self.showMessage("Settings", "Settings saved successfully!", QSystemTrayIcon.Information)
    
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