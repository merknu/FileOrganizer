#!/usr/bin/env python3
"""
Advanced Video Transfer Tool
============================

A specialized tool for transferring video files with transcoding capabilities,
format conversion, quality selection, and intelligent organization.

Features:
- Smart video file detection and filtering
- Video transcoding with ffmpeg support
- Resolution and quality-based filtering
- Format conversion (MP4, AVI, MKV, MOV, WebM, etc.)
- Metadata preservation and editing
- Subtitle handling
- Resume interrupted transfers
- Batch processing with queue management
- Hardware acceleration support (NVENC, VAAPI, etc.)

Usage:
    python video_transfer.py

Author: FileOrganizer Team
"""

import os
import sys
import json
import shutil
import hashlib
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging
import re

# GUI imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QTextEdit, QProgressBar,
    QMessageBox, QGroupBox, QGridLayout, QLineEdit, QSpinBox,
    QComboBox, QCheckBox, QTableWidget, QTableWidgetItem,
    QTabWidget, QSlider, QListWidget, QSplitter, QFrame,
    QHeaderView, QAbstractItemView, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Video file extensions
VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
    '.m4v', '.mpg', '.mpeg', '.3gp', '.3g2', '.mts', '.m2ts',
    '.vob', '.ogv', '.divx', '.xvid', '.asf', '.rm', '.rmvb',
    '.f4v', '.f4p', '.f4a', '.f4b', '.ts', '.mxf', '.h264',
    '.h265', '.hevc', '.av1'
}

# Transcoding presets
TRANSCODING_PRESETS = {
    "Copy (No Transcoding)": {
        "video_codec": "copy",
        "audio_codec": "copy",
        "container": None
    },
    "H.264 High Quality": {
        "video_codec": "libx264",
        "audio_codec": "aac",
        "preset": "slow",
        "crf": 18,
        "container": "mp4"
    },
    "H.264 Balanced": {
        "video_codec": "libx264",
        "audio_codec": "aac",
        "preset": "medium",
        "crf": 23,
        "container": "mp4"
    },
    "H.264 Fast (Lower Quality)": {
        "video_codec": "libx264",
        "audio_codec": "aac",
        "preset": "fast",
        "crf": 28,
        "container": "mp4"
    },
    "H.265/HEVC High Quality": {
        "video_codec": "libx265",
        "audio_codec": "aac",
        "preset": "slow",
        "crf": 22,
        "container": "mp4"
    },
    "H.265/HEVC Balanced": {
        "video_codec": "libx265",
        "audio_codec": "aac",
        "preset": "medium",
        "crf": 28,
        "container": "mp4"
    },
    "WebM (VP9)": {
        "video_codec": "libvpx-vp9",
        "audio_codec": "libopus",
        "crf": 30,
        "b:v": "0",
        "container": "webm"
    },
    "ProRes 422": {
        "video_codec": "prores_ks",
        "audio_codec": "pcm_s16le",
        "profile": 2,
        "container": "mov"
    },
    "DNxHD": {
        "video_codec": "dnxhd",
        "audio_codec": "pcm_s16le",
        "b:v": "185M",
        "container": "mov"
    }
}

# Resolution presets
RESOLUTION_PRESETS = {
    "Keep Original": None,
    "4K (3840x2160)": "3840:2160",
    "1080p (1920x1080)": "1920:1080",
    "720p (1280x720)": "1280:720",
    "480p (854x480)": "854:480",
    "360p (640x360)": "640:360"
}

class VideoMetadata:
    """Extracts and stores video metadata using ffprobe"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.metadata = self._extract_metadata()
    
    def _extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', self.file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
            return {}
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}
    
    def get_duration(self) -> float:
        """Get video duration in seconds"""
        try:
            return float(self.metadata.get('format', {}).get('duration', 0))
        except:
            return 0
    
    def get_resolution(self) -> Tuple[int, int]:
        """Get video resolution (width, height)"""
        for stream in self.metadata.get('streams', []):
            if stream.get('codec_type') == 'video':
                width = stream.get('width', 0)
                height = stream.get('height', 0)
                return (width, height)
        return (0, 0)
    
    def get_bitrate(self) -> int:
        """Get video bitrate in bits per second"""
        try:
            return int(self.metadata.get('format', {}).get('bit_rate', 0))
        except:
            return 0
    
    def get_codec(self) -> str:
        """Get video codec name"""
        for stream in self.metadata.get('streams', []):
            if stream.get('codec_type') == 'video':
                return stream.get('codec_name', 'unknown')
        return 'unknown'
    
    def get_fps(self) -> float:
        """Get frames per second"""
        for stream in self.metadata.get('streams', []):
            if stream.get('codec_type') == 'video':
                fps_str = stream.get('r_frame_rate', '0/1')
                try:
                    num, den = map(int, fps_str.split('/'))
                    return num / den if den != 0 else 0
                except:
                    return 0
        return 0

class VideoTranscoder(QThread):
    """Handles video transcoding operations"""
    
    progress = pyqtSignal(int)
    status_update = pyqtSignal(str)
    file_completed = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.queue = []
        self.current_file = None
        self.stop_requested = False
        self.preset = "Copy (No Transcoding)"
        self.resolution = None
        self.hardware_accel = None
    
    def add_to_queue(self, source: str, destination: str):
        """Add file to transcoding queue"""
        self.queue.append((source, destination))
    
    def set_preset(self, preset_name: str):
        """Set transcoding preset"""
        self.preset = preset_name
    
    def set_resolution(self, resolution: str):
        """Set target resolution"""
        self.resolution = resolution
    
    def set_hardware_acceleration(self, accel_type: str):
        """Set hardware acceleration type"""
        self.hardware_accel = accel_type
    
    def build_ffmpeg_command(self, source: str, destination: str) -> List[str]:
        """Build ffmpeg command based on preset and settings"""
        preset = TRANSCODING_PRESETS[self.preset]
        
        # Base command
        cmd = ['ffmpeg', '-i', source]
        
        # Hardware acceleration
        if self.hardware_accel == "NVIDIA NVENC":
            cmd.extend(['-hwaccel', 'cuda'])
        elif self.hardware_accel == "Intel Quick Sync":
            cmd.extend(['-hwaccel', 'qsv'])
        elif self.hardware_accel == "AMD AMF":
            cmd.extend(['-hwaccel', 'd3d11va'])
        
        # Video codec
        if preset['video_codec'] != 'copy':
            cmd.extend(['-c:v', preset['video_codec']])
            
            # Codec-specific settings
            if 'crf' in preset:
                cmd.extend(['-crf', str(preset['crf'])])
            if 'preset' in preset:
                cmd.extend(['-preset', preset['preset']])
            if 'b:v' in preset:
                cmd.extend(['-b:v', preset['b:v']])
            if 'profile' in preset:
                cmd.extend(['-profile:v', str(preset['profile'])])
                
            # Resolution scaling
            if self.resolution and self.resolution != "Keep Original":
                scale = RESOLUTION_PRESETS[self.resolution]
                cmd.extend(['-vf', f'scale={scale}'])
        else:
            cmd.extend(['-c:v', 'copy'])
        
        # Audio codec
        if preset['audio_codec'] != 'copy':
            cmd.extend(['-c:a', preset['audio_codec']])
        else:
            cmd.extend(['-c:a', 'copy'])
        
        # Output file
        if preset.get('container'):
            # Change extension if container is specified
            dest_path = Path(destination)
            destination = str(dest_path.with_suffix(f".{preset['container']}"))
        
        cmd.extend(['-y', destination])
        return cmd
    
    def run(self):
        """Process transcoding queue"""
        total_files = len(self.queue)
        completed = 0
        
        for source, destination in self.queue:
            if self.stop_requested:
                break
                
            self.current_file = Path(source).name
            self.status_update.emit(f"Processing: {self.current_file}")
            
            try:
                # Create destination directory if needed
                Path(destination).parent.mkdir(parents=True, exist_ok=True)
                
                if self.preset == "Copy (No Transcoding)":
                    # Simple copy
                    shutil.copy2(source, destination)
                else:
                    # Transcode with ffmpeg
                    cmd = self.build_ffmpeg_command(source, destination)
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    
                    # Monitor progress
                    for line in process.stderr:
                        if 'time=' in line:
                            # Parse progress from ffmpeg output
                            pass
                    
                    process.wait()
                    
                    if process.returncode != 0:
                        raise Exception("FFmpeg transcoding failed")
                
                completed += 1
                progress = int((completed / total_files) * 100)
                self.progress.emit(progress)
                self.file_completed.emit(source, destination)
                
            except Exception as e:
                self.error_occurred.emit(source, str(e))
                logger.error(f"Error processing {source}: {e}")
        
        self.status_update.emit("Transfer complete!" if not self.stop_requested else "Transfer stopped")
    
    def stop(self):
        """Request stop of transcoding"""
        self.stop_requested = True

class VideoTransferWindow(QMainWindow):
    """Main window for video transfer application"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.transcoder = VideoTranscoder()
        self.transcoder.progress.connect(self.update_progress)
        self.transcoder.status_update.connect(self.update_status)
        self.transcoder.file_completed.connect(self.on_file_completed)
        self.transcoder.error_occurred.connect(self.on_error)
        
        self.source_videos = []
        self.selected_videos = []
        
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Advanced Video Transfer Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tabs
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        
        # Transfer tab
        transfer_tab = QWidget()
        tabs.addTab(transfer_tab, "Transfer")
        self.setup_transfer_tab(transfer_tab)
        
        # Settings tab
        settings_tab = QWidget()
        tabs.addTab(settings_tab, "Transcoding Settings")
        self.setup_settings_tab(settings_tab)
        
        # Progress tab
        progress_tab = QWidget()
        tabs.addTab(progress_tab, "Progress")
        self.setup_progress_tab(progress_tab)
        
        # Apply dark theme
        self.apply_dark_theme()
    
    def setup_transfer_tab(self, parent):
        """Setup transfer tab UI"""
        layout = QVBoxLayout(parent)
        
        # Source and destination selection
        paths_group = QGroupBox("Paths")
        paths_layout = QGridLayout()
        paths_group.setLayout(paths_layout)
        
        # Source folder
        paths_layout.addWidget(QLabel("Source:"), 0, 0)
        self.source_edit = QLineEdit()
        paths_layout.addWidget(self.source_edit, 0, 1)
        self.source_button = QPushButton("Browse")
        self.source_button.clicked.connect(self.browse_source)
        paths_layout.addWidget(self.source_button, 0, 2)
        
        # Destination folder
        paths_layout.addWidget(QLabel("Destination:"), 1, 0)
        self.dest_edit = QLineEdit()
        paths_layout.addWidget(self.dest_edit, 1, 1)
        self.dest_button = QPushButton("Browse")
        self.dest_button.clicked.connect(self.browse_destination)
        paths_layout.addWidget(self.dest_button, 1, 2)
        
        layout.addWidget(paths_group)
        
        # Filter options
        filter_group = QGroupBox("Filters")
        filter_layout = QGridLayout()
        filter_group.setLayout(filter_layout)
        
        # Resolution filter
        filter_layout.addWidget(QLabel("Min Resolution:"), 0, 0)
        self.min_resolution = QComboBox()
        self.min_resolution.addItems(["Any", "360p", "480p", "720p", "1080p", "4K"])
        filter_layout.addWidget(self.min_resolution, 0, 1)
        
        # Duration filter
        filter_layout.addWidget(QLabel("Min Duration (seconds):"), 0, 2)
        self.min_duration = QSpinBox()
        self.min_duration.setRange(0, 3600)
        filter_layout.addWidget(self.min_duration, 0, 3)
        
        # Format filter
        filter_layout.addWidget(QLabel("Formats:"), 1, 0)
        self.format_filter = QLineEdit()
        self.format_filter.setPlaceholderText("e.g., mp4,mkv,avi (leave empty for all)")
        filter_layout.addWidget(self.format_filter, 1, 1, 1, 3)
        
        # Codec filter
        filter_layout.addWidget(QLabel("Codec:"), 2, 0)
        self.codec_filter = QComboBox()
        self.codec_filter.addItems(["Any", "h264", "h265", "vp9", "av1", "mpeg4"])
        filter_layout.addWidget(self.codec_filter, 2, 1)
        
        # File size filter
        filter_layout.addWidget(QLabel("Max Size (MB):"), 2, 2)
        self.max_size = QSpinBox()
        self.max_size.setRange(0, 100000)
        self.max_size.setValue(0)
        self.max_size.setSpecialValueText("No Limit")
        filter_layout.addWidget(self.max_size, 2, 3)
        
        layout.addWidget(filter_group)
        
        # File list
        list_group = QGroupBox("Video Files")
        list_layout = QVBoxLayout()
        list_group.setLayout(list_layout)
        
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(6)
        self.file_table.setHorizontalHeaderLabels([
            "Select", "Filename", "Resolution", "Duration", "Codec", "Size (MB)"
        ])
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_table.horizontalHeader().setStretchLastSection(True)
        list_layout.addWidget(self.file_table)
        
        # List controls
        list_controls = QHBoxLayout()
        self.scan_button = QPushButton("Scan Source")
        self.scan_button.clicked.connect(self.scan_source)
        list_controls.addWidget(self.scan_button)
        
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all)
        list_controls.addWidget(self.select_all_button)
        
        self.deselect_all_button = QPushButton("Deselect All")
        self.deselect_all_button.clicked.connect(self.deselect_all)
        list_controls.addWidget(self.deselect_all_button)
        
        list_controls.addStretch()
        
        self.transfer_button = QPushButton("Start Transfer")
        self.transfer_button.clicked.connect(self.start_transfer)
        self.transfer_button.setStyleSheet("background-color: #4CAF50;")
        list_controls.addWidget(self.transfer_button)
        
        list_layout.addLayout(list_controls)
        layout.addWidget(list_group)
    
    def setup_settings_tab(self, parent):
        """Setup transcoding settings tab"""
        layout = QVBoxLayout(parent)
        
        # Transcoding preset
        preset_group = QGroupBox("Transcoding Preset")
        preset_layout = QVBoxLayout()
        preset_group.setLayout(preset_layout)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(list(TRANSCODING_PRESETS.keys()))
        preset_layout.addWidget(self.preset_combo)
        
        self.preset_description = QTextEdit()
        self.preset_description.setReadOnly(True)
        self.preset_description.setMaximumHeight(100)
        preset_layout.addWidget(self.preset_description)
        
        self.preset_combo.currentTextChanged.connect(self.update_preset_description)
        layout.addWidget(preset_group)
        
        # Output settings
        output_group = QGroupBox("Output Settings")
        output_layout = QGridLayout()
        output_group.setLayout(output_layout)
        
        # Resolution
        output_layout.addWidget(QLabel("Resolution:"), 0, 0)
        self.output_resolution = QComboBox()
        self.output_resolution.addItems(list(RESOLUTION_PRESETS.keys()))
        output_layout.addWidget(self.output_resolution, 0, 1)
        
        # Frame rate
        output_layout.addWidget(QLabel("Frame Rate:"), 1, 0)
        self.output_fps = QComboBox()
        self.output_fps.addItems(["Keep Original", "24", "25", "30", "48", "50", "60"])
        output_layout.addWidget(self.output_fps, 1, 1)
        
        # Bitrate
        output_layout.addWidget(QLabel("Bitrate (Mbps):"), 2, 0)
        self.output_bitrate = QDoubleSpinBox()
        self.output_bitrate.setRange(0.1, 100)
        self.output_bitrate.setValue(5.0)
        self.output_bitrate.setSingleStep(0.5)
        output_layout.addWidget(self.output_bitrate, 2, 1)
        
        layout.addWidget(output_group)
        
        # Hardware acceleration
        hw_group = QGroupBox("Hardware Acceleration")
        hw_layout = QVBoxLayout()
        hw_group.setLayout(hw_layout)
        
        self.hw_accel = QComboBox()
        self.hw_accel.addItems([
            "None", "Auto-detect", "NVIDIA NVENC", "Intel Quick Sync", 
            "AMD AMF", "Apple VideoToolbox"
        ])
        hw_layout.addWidget(self.hw_accel)
        
        layout.addWidget(hw_group)
        
        # Advanced options
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QVBoxLayout()
        advanced_group.setLayout(advanced_layout)
        
        self.preserve_metadata = QCheckBox("Preserve metadata")
        self.preserve_metadata.setChecked(True)
        advanced_layout.addWidget(self.preserve_metadata)
        
        self.copy_subtitles = QCheckBox("Copy subtitles")
        self.copy_subtitles.setChecked(True)
        advanced_layout.addWidget(self.copy_subtitles)
        
        self.two_pass = QCheckBox("Two-pass encoding (better quality, slower)")
        advanced_layout.addWidget(self.two_pass)
        
        self.delete_source = QCheckBox("Delete source files after successful transfer")
        advanced_layout.addWidget(self.delete_source)
        
        layout.addWidget(advanced_group)
        layout.addStretch()
    
    def setup_progress_tab(self, parent):
        """Setup progress tab"""
        layout = QVBoxLayout(parent)
        
        # Overall progress
        progress_group = QGroupBox("Overall Progress")
        progress_layout = QVBoxLayout()
        progress_group.setLayout(progress_layout)
        
        self.overall_progress = QProgressBar()
        progress_layout.addWidget(self.overall_progress)
        
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        # Transfer log
        log_group = QGroupBox("Transfer Log")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setEnabled(False)
        control_layout.addWidget(self.pause_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_transfer)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)
        
        control_layout.addStretch()
        
        self.clear_log_button = QPushButton("Clear Log")
        self.clear_log_button.clicked.connect(self.log_text.clear)
        control_layout.addWidget(self.clear_log_button)
        
        layout.addLayout(control_layout)
    
    def apply_dark_theme(self):
        """Apply dark theme to the application"""
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        self.setPalette(dark_palette)
    
    def browse_source(self):
        """Browse for source folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.source_edit.setText(folder)
    
    def browse_destination(self):
        """Browse for destination folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_edit.setText(folder)
    
    def scan_source(self):
        """Scan source folder for video files"""
        source_path = self.source_edit.text()
        if not source_path or not os.path.exists(source_path):
            QMessageBox.warning(self, "Warning", "Please select a valid source folder")
            return
        
        self.source_videos.clear()
        self.file_table.setRowCount(0)
        
        # Get filter criteria
        min_res = self.min_resolution.currentText()
        min_dur = self.min_duration.value()
        formats = self.format_filter.text().split(',') if self.format_filter.text() else []
        codec_filter = self.codec_filter.currentText()
        max_size_mb = self.max_size.value() if self.max_size.value() > 0 else None
        
        # Scan for video files
        for root, dirs, files in os.walk(source_path):
            for file in files:
                if Path(file).suffix.lower() in VIDEO_EXTENSIONS:
                    file_path = os.path.join(root, file)
                    
                    # Apply format filter
                    if formats and Path(file).suffix.lower()[1:] not in formats:
                        continue
                    
                    # Check file size
                    if max_size_mb:
                        size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        if size_mb > max_size_mb:
                            continue
                    
                    # Get metadata
                    try:
                        meta = VideoMetadata(file_path)
                        
                        # Apply filters
                        if min_dur > 0 and meta.get_duration() < min_dur:
                            continue
                        
                        if codec_filter != "Any" and meta.get_codec() != codec_filter:
                            continue
                        
                        # Add to list
                        self.add_video_to_table(file_path, meta)
                        self.source_videos.append(file_path)
                        
                    except Exception as e:
                        logger.error(f"Error processing {file}: {e}")
        
        self.log_text.append(f"Found {len(self.source_videos)} video files")
    
    def add_video_to_table(self, file_path: str, metadata: VideoMetadata):
        """Add video to the file table"""
        row = self.file_table.rowCount()
        self.file_table.insertRow(row)
        
        # Checkbox
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        self.file_table.setCellWidget(row, 0, checkbox)
        
        # Filename
        self.file_table.setItem(row, 1, QTableWidgetItem(Path(file_path).name))
        
        # Resolution
        width, height = metadata.get_resolution()
        resolution = f"{width}x{height}" if width > 0 else "Unknown"
        self.file_table.setItem(row, 2, QTableWidgetItem(resolution))
        
        # Duration
        duration = metadata.get_duration()
        duration_str = str(timedelta(seconds=int(duration))) if duration > 0 else "Unknown"
        self.file_table.setItem(row, 3, QTableWidgetItem(duration_str))
        
        # Codec
        self.file_table.setItem(row, 4, QTableWidgetItem(metadata.get_codec()))
        
        # Size
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        self.file_table.setItem(row, 5, QTableWidgetItem(f"{size_mb:.2f}"))
    
    def select_all(self):
        """Select all files in the table"""
        for row in range(self.file_table.rowCount()):
            checkbox = self.file_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def deselect_all(self):
        """Deselect all files in the table"""
        for row in range(self.file_table.rowCount()):
            checkbox = self.file_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
    
    def get_selected_videos(self) -> List[str]:
        """Get list of selected video files"""
        selected = []
        for row in range(self.file_table.rowCount()):
            checkbox = self.file_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                if row < len(self.source_videos):
                    selected.append(self.source_videos[row])
        return selected
    
    def start_transfer(self):
        """Start the video transfer process"""
        # Validate inputs
        if not self.source_edit.text() or not self.dest_edit.text():
            QMessageBox.warning(self, "Warning", "Please select source and destination folders")
            return
        
        selected = self.get_selected_videos()
        if not selected:
            QMessageBox.warning(self, "Warning", "No videos selected for transfer")
            return
        
        # Setup transcoder
        self.transcoder.set_preset(self.preset_combo.currentText())
        self.transcoder.set_resolution(self.output_resolution.currentText())
        self.transcoder.set_hardware_acceleration(self.hw_accel.currentText())
        
        # Add files to queue
        dest_base = self.dest_edit.text()
        source_base = self.source_edit.text()
        
        for video_path in selected:
            # Maintain folder structure
            rel_path = os.path.relpath(video_path, source_base)
            dest_path = os.path.join(dest_base, rel_path)
            self.transcoder.add_to_queue(video_path, dest_path)
        
        # Update UI
        self.transfer_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.log_text.append(f"Starting transfer of {len(selected)} videos...")
        
        # Start transfer
        self.transcoder.start()
    
    def stop_transfer(self):
        """Stop the transfer process"""
        self.transcoder.stop()
        self.transfer_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def update_progress(self, value: int):
        """Update progress bar"""
        self.overall_progress.setValue(value)
    
    def update_status(self, status: str):
        """Update status label"""
        self.status_label.setText(status)
        self.log_text.append(status)
    
    def on_file_completed(self, source: str, destination: str):
        """Handle file completion"""
        self.log_text.append(f"✓ Completed: {Path(source).name}")
    
    def on_error(self, file_path: str, error: str):
        """Handle transfer error"""
        self.log_text.append(f"✗ Error with {Path(file_path).name}: {error}")
    
    def update_preset_description(self, preset_name: str):
        """Update preset description"""
        preset = TRANSCODING_PRESETS.get(preset_name, {})
        desc = f"Video Codec: {preset.get('video_codec', 'N/A')}\n"
        desc += f"Audio Codec: {preset.get('audio_codec', 'N/A')}\n"
        if 'crf' in preset:
            desc += f"Quality (CRF): {preset['crf']}\n"
        if 'preset' in preset:
            desc += f"Encoding Speed: {preset['preset']}\n"
        if 'container' in preset:
            desc += f"Container: {preset['container']}"
        self.preset_description.setText(desc)

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Video Transfer Tool")
    app.setStyle("Fusion")
    
    window = VideoTransferWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()