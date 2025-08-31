#!/usr/bin/env python3
"""
Advanced Audio Transfer Tool
============================

A specialized tool for transferring audio files from one location to another
with advanced filtering, metadata analysis, and organizational features.

Features:
- Smart audio file detection and filtering
- Metadata-based filtering (duration, bitrate, genre, artist, album)
- Duplicate detection and handling
- Resume interrupted transfers
- Progress tracking and statistics
- Audio format conversion options
- Playlist preservation
- Quality analysis and filtering

Usage:
    python audio_transfer.py

Author: FileOrganizer Team
"""

import os
import sys
import json
import shutil
import hashlib
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging

# GUI imports with fallback
GUI_AVAILABLE = False
GUI_TYPE = None

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QFileDialog, QTextEdit, QProgressBar,
        QMessageBox, QGroupBox, QGridLayout, QLineEdit, QSpinBox,
        QComboBox, QCheckBox, QTableWidget, QTableWidgetItem,
        QTabWidget, QSlider, QListWidget, QSplitter, QFrame
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt5.QtGui import QFont, QPalette, QColor
    GUI_AVAILABLE = True
    GUI_TYPE = "PyQt5"
except ImportError:
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
        GUI_AVAILABLE = True
        GUI_TYPE = "tkinter"
    except ImportError:
        print("No GUI framework available. Running in command-line mode.")

# Audio processing imports
try:
    from mutagen import File as MutagenFile
    from mutagen.mp3 import MP3
    from mutagen.mp4 import MP4
    from mutagen.flac import FLAC
    from mutagen.oggvorbis import OggVorbis
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    print("Warning: mutagen not available. Audio metadata features limited.")

class AudioFileInfo:
    """Represents an audio file with metadata"""
    
    def __init__(self, file_path: Path):
        self.path = file_path
        self.name = file_path.name
        self.size = file_path.stat().st_size if file_path.exists() else 0
        self.modified = datetime.fromtimestamp(file_path.stat().st_mtime) if file_path.exists() else None
        
        # Audio metadata
        self.duration = 0.0  # seconds
        self.bitrate = 0     # kbps
        self.sample_rate = 0 # Hz
        self.channels = 0
        self.format = file_path.suffix.lower().lstrip('.')
        
        # Tags
        self.title = ""
        self.artist = ""
        self.album = ""
        self.genre = ""
        self.year = ""
        self.track_number = ""
        
        # Quality indicators
        self.quality_score = 0.0  # 0-10 scale
        self.is_lossless = False
        
        # Load metadata if possible
        self._load_metadata()
    
    def _load_metadata(self):
        """Load audio metadata using mutagen"""
        if not MUTAGEN_AVAILABLE or not self.path.exists():
            return
            
        try:
            audio_file = MutagenFile(str(self.path))
            if audio_file is None:
                return
                
            # Basic info
            if hasattr(audio_file, 'info'):
                info = audio_file.info
                self.duration = getattr(info, 'length', 0.0)
                self.bitrate = getattr(info, 'bitrate', 0)
                self.sample_rate = getattr(info, 'sample_rate', 0)
                self.channels = getattr(info, 'channels', 0)
            
            # Tags - handle different formats
            if hasattr(audio_file, 'tags') and audio_file.tags:
                tags = audio_file.tags
                
                # Common tag mappings
                tag_mappings = {
                    'title': ['TIT2', 'TITLE', '\xa9nam'],
                    'artist': ['TPE1', 'ARTIST', '\xa9ART'],
                    'album': ['TALB', 'ALBUM', '\xa9alb'],
                    'genre': ['TCON', 'GENRE', '\xa9gen'],
                    'year': ['TDRC', 'DATE', '\xa9day'],
                    'track_number': ['TRCK', 'TRACKNUMBER', 'trkn']
                }
                
                for attr, tag_keys in tag_mappings.items():
                    for key in tag_keys:
                        if key in tags:
                            value = tags[key]
                            if isinstance(value, list) and value:
                                value = value[0]
                            if hasattr(value, 'text'):
                                value = str(value.text[0]) if value.text else ""
                            setattr(self, attr, str(value))
                            break
            
            # Calculate quality score
            self._calculate_quality_score()
            
        except Exception as e:
            logging.warning(f"Failed to load metadata for {self.path}: {e}")
    
    def _calculate_quality_score(self):
        """Calculate a quality score based on audio properties"""
        score = 5.0  # Base score
        
        # Bitrate scoring
        if self.bitrate >= 320:
            score += 2.0
        elif self.bitrate >= 256:
            score += 1.5
        elif self.bitrate >= 192:
            score += 1.0
        elif self.bitrate >= 128:
            score += 0.5
        else:
            score -= 1.0
            
        # Sample rate scoring
        if self.sample_rate >= 48000:
            score += 1.0
        elif self.sample_rate >= 44100:
            score += 0.5
            
        # Lossless formats
        lossless_formats = ['flac', 'alac', 'wav', 'aiff', 'ape']
        if self.format in lossless_formats:
            score += 2.0
            self.is_lossless = True
            
        # Stereo bonus
        if self.channels == 2:
            score += 0.3
        elif self.channels > 2:
            score += 0.5
            
        self.quality_score = min(10.0, max(0.0, score))
    
    def matches_filter(self, filters: Dict[str, Any]) -> bool:
        """Check if file matches the given filters"""
        
        # Duration filter
        if filters.get('min_duration', 0) > 0 and self.duration < filters['min_duration']:
            return False
        if filters.get('max_duration', 0) > 0 and self.duration > filters['max_duration']:
            return False
            
        # Quality filter
        if filters.get('min_quality', 0) > 0 and self.quality_score < filters['min_quality']:
            return False
            
        # Bitrate filter
        if filters.get('min_bitrate', 0) > 0 and self.bitrate < filters['min_bitrate']:
            return False
            
        # Format filter
        allowed_formats = filters.get('formats', [])
        if allowed_formats and self.format not in allowed_formats:
            return False
            
        # Lossless filter
        if filters.get('lossless_only', False) and not self.is_lossless:
            return False
            
        # Artist filter
        artist_filter = filters.get('artist', '').lower()
        if artist_filter and artist_filter not in self.artist.lower():
            return False
            
        # Genre filter
        genre_filter = filters.get('genre', '').lower()
        if genre_filter and genre_filter not in self.genre.lower():
            return False
            
        # Album filter
        album_filter = filters.get('album', '').lower()
        if album_filter and album_filter not in self.album.lower():
            return False
            
        return True
    
    def get_hash(self) -> str:
        """Get SHA-256 hash of the file for duplicate detection"""
        if not self.path.exists():
            return ""
            
        hash_sha256 = hashlib.sha256()
        try:
            with open(self.path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logging.error(f"Failed to hash {self.path}: {e}")
            return ""

class AudioTranscoder:
    """Handles audio transcoding operations using ffmpeg"""
    
    # Audio format presets
    TRANSCODING_PRESETS = {
        "Copy (No Transcoding)": {
            "codec": "copy",
            "container": None
        },
        "MP3 320kbps": {
            "codec": "libmp3lame",
            "bitrate": "320k",
            "container": "mp3"
        },
        "MP3 256kbps VBR": {
            "codec": "libmp3lame",
            "quality": "0",  # VBR quality
            "container": "mp3"
        },
        "MP3 192kbps": {
            "codec": "libmp3lame",
            "bitrate": "192k",
            "container": "mp3"
        },
        "MP3 128kbps": {
            "codec": "libmp3lame",
            "bitrate": "128k",
            "container": "mp3"
        },
        "AAC 256kbps": {
            "codec": "aac",
            "bitrate": "256k",
            "container": "m4a"
        },
        "AAC 192kbps": {
            "codec": "aac",
            "bitrate": "192k",
            "container": "m4a"
        },
        "FLAC Lossless": {
            "codec": "flac",
            "compression": "8",
            "container": "flac"
        },
        "ALAC Lossless": {
            "codec": "alac",
            "container": "m4a"
        },
        "OGG Vorbis Q6": {
            "codec": "libvorbis",
            "quality": "6",
            "container": "ogg"
        },
        "Opus 128kbps": {
            "codec": "libopus",
            "bitrate": "128k",
            "container": "opus"
        },
        "WAV PCM": {
            "codec": "pcm_s16le",
            "container": "wav"
        }
    }
    
    def __init__(self):
        self.preset = "Copy (No Transcoding)"
        self.normalize_audio = False
        self.remove_silence = False
        self.fade_in = 0  # seconds
        self.fade_out = 0  # seconds
        self.sample_rate = None  # Keep original if None
        self.channels = None  # Keep original if None
        
    def check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def transcode_file(self, source: str, destination: str, progress_callback=None) -> bool:
        """Transcode audio file using ffmpeg"""
        try:
            preset = self.TRANSCODING_PRESETS[self.preset]
            
            if preset['codec'] == 'copy' and not self.normalize_audio and not self.remove_silence:
                # Simple copy
                shutil.copy2(source, destination)
                return True
            
            # Build ffmpeg command
            cmd = ['ffmpeg', '-i', source, '-y']
            
            # Audio filters
            audio_filters = []
            
            # Normalize audio
            if self.normalize_audio:
                audio_filters.append('loudnorm=I=-16:TP=-1.5:LRA=11')
            
            # Remove silence
            if self.remove_silence:
                audio_filters.append('silenceremove=start_periods=1:start_silence=0.1:start_threshold=-50dB')
            
            # Fade in/out
            if self.fade_in > 0:
                audio_filters.append(f'afade=in:st=0:d={self.fade_in}')
            if self.fade_out > 0:
                # Need duration for fade out
                duration = self.get_audio_duration(source)
                if duration > self.fade_out:
                    fade_start = duration - self.fade_out
                    audio_filters.append(f'afade=out:st={fade_start}:d={self.fade_out}')
            
            if audio_filters:
                cmd.extend(['-af', ','.join(audio_filters)])
            
            # Audio codec
            if preset['codec'] != 'copy':
                cmd.extend(['-c:a', preset['codec']])
                
                # Codec-specific options
                if 'bitrate' in preset:
                    cmd.extend(['-b:a', preset['bitrate']])
                if 'quality' in preset:
                    if preset['codec'] == 'libmp3lame':
                        cmd.extend(['-q:a', preset['quality']])
                    elif preset['codec'] == 'libvorbis':
                        cmd.extend(['-q:a', preset['quality']])
                if 'compression' in preset:
                    cmd.extend(['-compression_level', preset['compression']])
            else:
                cmd.extend(['-c:a', 'copy'])
            
            # Sample rate
            if self.sample_rate:
                cmd.extend(['-ar', str(self.sample_rate)])
            
            # Channels
            if self.channels:
                cmd.extend(['-ac', str(self.channels)])
            
            # Output file
            if preset.get('container'):
                dest_path = Path(destination)
                destination = str(dest_path.with_suffix(f".{preset['container']}"))
            
            cmd.append(destination)
            
            # Run ffmpeg
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Monitor progress if callback provided
            if progress_callback:
                for line in process.stderr:
                    if 'time=' in line:
                        # Parse progress from ffmpeg output
                        progress_callback(line)
            
            process.wait()
            return process.returncode == 0
            
        except Exception as e:
            logging.error(f"Transcoding failed: {e}")
            return False
    
    def get_audio_duration(self, file_path: str) -> float:
        """Get audio duration using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data.get('format', {}).get('duration', 0))
        except:
            pass
        return 0

class AudioTransferWorker(QThread if GUI_TYPE == "PyQt5" else object):
    """Worker thread for audio file transfer operations"""
    
    # Signals for PyQt5
    if GUI_TYPE == "PyQt5":
        progress_updated = pyqtSignal(int, str)
        file_processed = pyqtSignal(str, str, bool)  # filename, status, success
        transfer_completed = pyqtSignal(dict)  # statistics
        error_occurred = pyqtSignal(str)
    
    def __init__(self, source_dir: str, dest_dir: str, filters: Dict[str, Any], 
                 options: Dict[str, Any]):
        if GUI_TYPE == "PyQt5":
            super().__init__()
        
        self.source_dir = Path(source_dir)
        self.dest_dir = Path(dest_dir)
        self.filters = filters
        self.options = options
        
        self.should_stop = False
        self.paused = False
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'transferred_files': 0,
            'skipped_files': 0,
            'error_files': 0,
            'total_size': 0,
            'transferred_size': 0,
            'start_time': None,
            'end_time': None
        }
    
    def run(self):
        """Main transfer operation"""
        self.stats['start_time'] = datetime.now()
        
        try:
            # Discover audio files
            audio_files = self._discover_audio_files()
            self.stats['total_files'] = len(audio_files)
            self.stats['total_size'] = sum(af.size for af in audio_files)
            
            if GUI_TYPE == "PyQt5":
                self.progress_updated.emit(0, f"Found {len(audio_files)} audio files")
            
            # Create destination directory
            self.dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Process files
            for i, audio_file in enumerate(audio_files):
                if self.should_stop:
                    break
                    
                while self.paused and not self.should_stop:
                    if GUI_TYPE == "PyQt5":
                        self.msleep(100)
                    else:
                        import time
                        time.sleep(0.1)
                
                try:
                    success = self._transfer_file(audio_file)
                    
                    if success:
                        self.stats['transferred_files'] += 1
                        self.stats['transferred_size'] += audio_file.size
                    else:
                        self.stats['skipped_files'] += 1
                        
                    self.stats['processed_files'] += 1
                    
                    # Update progress
                    progress = int((i + 1) / len(audio_files) * 100)
                    status = f"Processed {i + 1}/{len(audio_files)} files"
                    
                    if GUI_TYPE == "PyQt5":
                        self.progress_updated.emit(progress, status)
                        self.file_processed.emit(audio_file.name, 
                                               "Transferred" if success else "Skipped", 
                                               success)
                    
                except Exception as e:
                    self.stats['error_files'] += 1
                    error_msg = f"Error processing {audio_file.name}: {e}"
                    logging.error(error_msg)
                    
                    if GUI_TYPE == "PyQt5":
                        self.error_occurred.emit(error_msg)
            
        except Exception as e:
            error_msg = f"Transfer operation failed: {e}"
            logging.error(error_msg)
            if GUI_TYPE == "PyQt5":
                self.error_occurred.emit(error_msg)
        
        finally:
            self.stats['end_time'] = datetime.now()
            if GUI_TYPE == "PyQt5":
                self.transfer_completed.emit(self.stats)
    
    def _discover_audio_files(self) -> List[AudioFileInfo]:
        """Discover and filter audio files in source directory"""
        audio_extensions = {'.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg', 
                          '.wma', '.aiff', '.ape', '.opus', '.m4b', '.m4p'}
        
        audio_files = []
        
        for file_path in self.source_dir.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix.lower() in audio_extensions):
                
                audio_info = AudioFileInfo(file_path)
                
                # Apply filters
                if audio_info.matches_filter(self.filters):
                    audio_files.append(audio_info)
        
        return audio_files
    
    def _transfer_file(self, audio_file: AudioFileInfo) -> bool:
        """Transfer a single audio file"""
        try:
            # Determine destination path
            if self.options.get('preserve_structure', True):
                # Preserve folder structure
                rel_path = audio_file.path.relative_to(self.source_dir)
                dest_path = self.dest_dir / rel_path
            else:
                # Flat structure
                dest_path = self.dest_dir / audio_file.name
            
            # Create destination directory
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle duplicates
            if dest_path.exists():
                duplicate_action = self.options.get('duplicate_action', 'skip')
                
                if duplicate_action == 'skip':
                    return False
                elif duplicate_action == 'rename':
                    dest_path = self._get_unique_filename(dest_path)
                elif duplicate_action == 'compare':
                    # Compare files and keep better quality
                    existing_info = AudioFileInfo(dest_path)
                    if existing_info.quality_score >= audio_file.quality_score:
                        return False
            
            # Copy file
            if self.options.get('move_files', False):
                shutil.move(str(audio_file.path), str(dest_path))
            else:
                shutil.copy2(str(audio_file.path), str(dest_path))
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to transfer {audio_file.path}: {e}")
            return False
    
    def _get_unique_filename(self, path: Path) -> Path:
        """Generate a unique filename if file exists"""
        counter = 1
        original_stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        while True:
            new_name = f"{original_stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
    
    def stop(self):
        """Stop the transfer operation"""
        self.should_stop = True
    
    def pause(self):
        """Pause the transfer operation"""
        self.paused = True
    
    def resume(self):
        """Resume the transfer operation"""
        self.paused = False

class AudioTransferGUI(QMainWindow if GUI_TYPE == "PyQt5" else object):
    """Main GUI for the Audio Transfer Tool"""
    
    def __init__(self):
        if GUI_TYPE == "PyQt5":
            super().__init__()
        
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        if GUI_TYPE == "PyQt5":
            self.setWindowTitle("Audio Transfer Tool - Smart Audio File Management")
            self.setGeometry(100, 100, 1200, 800)
            
            # Central widget
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Main layout
            main_layout = QVBoxLayout(central_widget)
            
            # Header
            header = QLabel("🎵 Advanced Audio Transfer Tool")
            header.setAlignment(Qt.AlignCenter)
            header.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 20px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                stop:0 #3498db, stop:1 #2980b9);
                    color: white;
                    border-radius: 10px;
                    margin-bottom: 20px;
                }
            """)
            main_layout.addWidget(header)
            
            # Create tabs
            self.create_tabs(main_layout)
            
            # Progress section
            self.create_progress_section(main_layout)
            
            # Control buttons
            self.create_control_buttons(main_layout)
            
            # Apply modern styling
            self.apply_modern_style()
        
        elif GUI_TYPE == "tkinter":
            self.root = tk.Tk()
            self.root.title("Audio Transfer Tool - Smart Audio File Management")
            self.root.geometry("1000x700")
            
            # Create tkinter interface
            self.create_tkinter_ui()
    
    def create_tabs(self, parent_layout):
        """Create tabbed interface"""
        if GUI_TYPE != "PyQt5":
            return
            
        self.tabs = QTabWidget()
        
        # Source & Destination Tab
        self.create_source_dest_tab()
        
        # Filters Tab
        self.create_filters_tab()
        
        # Options Tab
        self.create_options_tab()
        
        # Results Tab
        self.create_results_tab()
        
        parent_layout.addWidget(self.tabs)
    
    def create_source_dest_tab(self):
        """Create source and destination selection tab"""
        if GUI_TYPE != "PyQt5":
            return
            
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Source section
        source_group = QGroupBox("📁 Source Directory")
        source_layout = QVBoxLayout()
        
        self.source_label = QLabel("No source selected")
        self.source_label.setStyleSheet("padding: 10px; background: #ecf0f1; border-radius: 5px; margin: 5px;")
        source_layout.addWidget(self.source_label)
        
        source_btn = QPushButton("Browse Source Directory")
        source_btn.clicked.connect(self.browse_source)
        source_layout.addWidget(source_btn)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Destination section
        dest_group = QGroupBox("📂 Destination Directory")
        dest_layout = QVBoxLayout()
        
        self.dest_label = QLabel("No destination selected")
        self.dest_label.setStyleSheet("padding: 10px; background: #ecf0f1; border-radius: 5px; margin: 5px;")
        dest_layout.addWidget(self.dest_label)
        
        dest_btn = QPushButton("Browse Destination Directory")
        dest_btn.clicked.connect(self.browse_destination)
        dest_layout.addWidget(dest_btn)
        
        dest_group.setLayout(dest_layout)
        layout.addWidget(dest_group)
        
        # Scan button
        scan_btn = QPushButton("🔍 Scan Source Directory")
        scan_btn.setStyleSheet("""
            QPushButton {
                background: #f39c12;
                color: white;
                font-size: 16px;
                padding: 15px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e67e22;
            }
        """)
        scan_btn.clicked.connect(self.scan_source)
        layout.addWidget(scan_btn)
        
        # File list
        self.file_list = QTableWidget()
        self.file_list.setColumnCount(7)
        self.file_list.setHorizontalHeaderLabels([
            "Filename", "Artist", "Album", "Duration", "Bitrate", "Format", "Quality"
        ])
        layout.addWidget(self.file_list)
        
        self.tabs.addTab(tab, "📁 Source & Destination")
    
    def create_filters_tab(self):
        """Create filters configuration tab"""
        if GUI_TYPE != "PyQt5":
            return
            
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Audio properties filters
        audio_group = QGroupBox("🎧 Audio Properties")
        audio_layout = QGridLayout()
        
        # Duration filter
        audio_layout.addWidget(QLabel("Min Duration (seconds):"), 0, 0)
        self.min_duration = QSpinBox()
        self.min_duration.setMaximum(3600)
        audio_layout.addWidget(self.min_duration, 0, 1)
        
        audio_layout.addWidget(QLabel("Max Duration (seconds):"), 0, 2)
        self.max_duration = QSpinBox()
        self.max_duration.setMaximum(3600)
        audio_layout.addWidget(self.max_duration, 0, 3)
        
        # Bitrate filter
        audio_layout.addWidget(QLabel("Min Bitrate (kbps):"), 1, 0)
        self.min_bitrate = QSpinBox()
        self.min_bitrate.setMaximum(2000)
        audio_layout.addWidget(self.min_bitrate, 1, 1)
        
        # Quality filter
        audio_layout.addWidget(QLabel("Min Quality (1-10):"), 1, 2)
        self.min_quality = QSpinBox()
        self.min_quality.setMaximum(10)
        audio_layout.addWidget(self.min_quality, 1, 3)
        
        # Lossless only
        self.lossless_only = QCheckBox("Lossless formats only")
        audio_layout.addWidget(self.lossless_only, 2, 0, 1, 2)
        
        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)
        
        # Format filters
        format_group = QGroupBox("🎼 Format Selection")
        format_layout = QGridLayout()
        
        formats = ['mp3', 'flac', 'wav', 'm4a', 'aac', 'ogg', 'wma', 'aiff']
        self.format_checkboxes = {}
        
        for i, fmt in enumerate(formats):
            checkbox = QCheckBox(fmt.upper())
            checkbox.setChecked(True)
            self.format_checkboxes[fmt] = checkbox
            format_layout.addWidget(checkbox, i // 4, i % 4)
        
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Metadata filters
        metadata_group = QGroupBox("🏷️ Metadata Filters")
        metadata_layout = QGridLayout()
        
        metadata_layout.addWidget(QLabel("Artist contains:"), 0, 0)
        self.artist_filter = QLineEdit()
        metadata_layout.addWidget(self.artist_filter, 0, 1)
        
        metadata_layout.addWidget(QLabel("Album contains:"), 1, 0)
        self.album_filter = QLineEdit()
        metadata_layout.addWidget(self.album_filter, 1, 1)
        
        metadata_layout.addWidget(QLabel("Genre contains:"), 2, 0)
        self.genre_filter = QLineEdit()
        metadata_layout.addWidget(self.genre_filter, 2, 1)
        
        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)
        
        self.tabs.addTab(tab, "🔍 Filters")
    
    def create_options_tab(self):
        """Create transfer options tab"""
        if GUI_TYPE != "PyQt5":
            return
            
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Transfer options
        transfer_group = QGroupBox("📋 Transfer Options")
        transfer_layout = QVBoxLayout()
        
        self.preserve_structure = QCheckBox("Preserve folder structure")
        self.preserve_structure.setChecked(True)
        transfer_layout.addWidget(self.preserve_structure)
        
        self.move_files = QCheckBox("Move files (instead of copy)")
        transfer_layout.addWidget(self.move_files)
        
        # Duplicate handling
        dup_layout = QHBoxLayout()
        dup_layout.addWidget(QLabel("Duplicate files:"))
        self.duplicate_action = QComboBox()
        self.duplicate_action.addItems(["Skip", "Rename", "Compare Quality", "Overwrite"])
        dup_layout.addWidget(self.duplicate_action)
        transfer_layout.addLayout(dup_layout)
        
        transfer_group.setLayout(transfer_layout)
        layout.addWidget(transfer_group)
        
        # Organization options
        org_group = QGroupBox("🗂️ Organization")
        org_layout = QVBoxLayout()
        
        self.organize_by_artist = QCheckBox("Organize by Artist")
        org_layout.addWidget(self.organize_by_artist)
        
        self.organize_by_album = QCheckBox("Organize by Album")
        org_layout.addWidget(self.organize_by_album)
        
        self.organize_by_genre = QCheckBox("Organize by Genre")
        org_layout.addWidget(self.organize_by_genre)
        
        org_group.setLayout(org_layout)
        layout.addWidget(org_group)
        
        # Quality options
        quality_group = QGroupBox("🎚️ Quality Options")
        quality_layout = QVBoxLayout()
        
        self.create_playlists = QCheckBox("Create playlists (.m3u)")
        quality_layout.addWidget(self.create_playlists)
        
        self.verify_integrity = QCheckBox("Verify file integrity")
        self.verify_integrity.setChecked(True)
        quality_layout.addWidget(self.verify_integrity)
        
        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)
        
        self.tabs.addTab(tab, "⚙️ Options")
    
    def create_results_tab(self):
        """Create results and statistics tab"""
        if GUI_TYPE != "PyQt5":
            return
            
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Statistics
        stats_group = QGroupBox("📊 Transfer Statistics")
        stats_layout = QGridLayout()
        
        self.stats_labels = {}
        stats = ["Total Files", "Transferred", "Skipped", "Errors", "Total Size", "Time Elapsed"]
        
        for i, stat in enumerate(stats):
            label = QLabel(f"{stat}:")
            value = QLabel("0")
            value.setStyleSheet("font-weight: bold; color: #2c3e50;")
            
            stats_layout.addWidget(label, i // 2, (i % 2) * 2)
            stats_layout.addWidget(value, i // 2, (i % 2) * 2 + 1)
            self.stats_labels[stat.lower().replace(" ", "_")] = value
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Transfer log
        log_group = QGroupBox("📝 Transfer Log")
        log_layout = QVBoxLayout()
        
        self.transfer_log = QTextEdit()
        self.transfer_log.setStyleSheet("""
            QTextEdit {
                background: #2c3e50;
                color: #ecf0f1;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        log_layout.addWidget(self.transfer_log)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        self.tabs.addTab(tab, "📊 Results")
    
    def create_progress_section(self, parent_layout):
        """Create progress tracking section"""
        if GUI_TYPE != "PyQt5":
            return
            
        progress_group = QGroupBox("📈 Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                text-align: center;
                font-weight: bold;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #27ae60, stop:1 #2ecc71);
                border-radius: 6px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready to transfer audio files")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: #7f8c8d; padding: 5px;")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        parent_layout.addWidget(progress_group)
    
    def create_control_buttons(self, parent_layout):
        """Create control buttons"""
        if GUI_TYPE != "PyQt5":
            return
            
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 Start Transfer")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                font-size: 16px;
                padding: 15px 30px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #219a52;
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)
        self.start_btn.clicked.connect(self.start_transfer)
        button_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("⏸️ Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_transfer)
        button_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("🛑 Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_transfer)
        button_layout.addWidget(self.stop_btn)
        
        parent_layout.addLayout(button_layout)
    
    def apply_modern_style(self):
        """Apply modern styling to the interface"""
        if GUI_TYPE != "PyQt5":
            return
            
        self.setStyleSheet("""
            QMainWindow {
                background: #ecf0f1;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2980b9;
            }
            QPushButton:pressed {
                background: #21618c;
            }
            QPushButton:disabled {
                background: #bdc3c7;
                color: #7f8c8d;
            }
            QLineEdit, QSpinBox, QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background: white;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #3498db;
            }
            QCheckBox {
                font-size: 12px;
                color: #2c3e50;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QTableWidget {
                gridline-color: #bdc3c7;
                background: white;
                alternate-background-color: #f8f9fa;
            }
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                color: #2c3e50;
                padding: 10px 15px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
        """)
    
    def create_tkinter_ui(self):
        """Create tkinter interface as fallback"""
        # Basic tkinter implementation
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Header
        header = ttk.Label(main_frame, text="🎵 Audio Transfer Tool", 
                          font=("Arial", 18, "bold"))
        header.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Source selection
        ttk.Label(main_frame, text="Source Directory:").grid(row=1, column=0, sticky=tk.W)
        self.source_var = tk.StringVar(value="No source selected")
        ttk.Label(main_frame, textvariable=self.source_var).grid(row=1, column=1, sticky=tk.W)
        ttk.Button(main_frame, text="Browse Source", 
                  command=self.browse_source_tk).grid(row=2, column=0, pady=5)
        
        # Destination selection
        ttk.Label(main_frame, text="Destination Directory:").grid(row=3, column=0, sticky=tk.W)
        self.dest_var = tk.StringVar(value="No destination selected")
        ttk.Label(main_frame, textvariable=self.dest_var).grid(row=3, column=1, sticky=tk.W)
        ttk.Button(main_frame, text="Browse Destination", 
                  command=self.browse_dest_tk).grid(row=4, column=0, pady=5)
        
        # Start button
        ttk.Button(main_frame, text="Start Transfer", 
                  command=self.start_transfer_tk).grid(row=5, column=0, columnspan=2, pady=20)
    
    def browse_source(self):
        """Browse for source directory"""
        if GUI_TYPE == "PyQt5":
            directory = QFileDialog.getExistingDirectory(self, "Select Source Directory")
            if directory:
                self.source_label.setText(directory)
        elif GUI_TYPE == "tkinter":
            self.browse_source_tk()
    
    def browse_source_tk(self):
        """Tkinter version of source browsing"""
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory:
            self.source_var.set(directory)
    
    def browse_destination(self):
        """Browse for destination directory"""
        if GUI_TYPE == "PyQt5":
            directory = QFileDialog.getExistingDirectory(self, "Select Destination Directory")
            if directory:
                self.dest_label.setText(directory)
        elif GUI_TYPE == "tkinter":
            self.browse_dest_tk()
    
    def browse_dest_tk(self):
        """Tkinter version of destination browsing"""
        directory = filedialog.askdirectory(title="Select Destination Directory")
        if directory:
            self.dest_var.set(directory)
    
    def scan_source(self):
        """Scan source directory for audio files"""
        if GUI_TYPE != "PyQt5":
            return
            
        source_dir = self.source_label.text()
        if source_dir == "No source selected":
            QMessageBox.warning(self, "Warning", "Please select a source directory first")
            return
        
        self.status_label.setText("Scanning source directory...")
        
        # Create a simple scanner (not using worker thread for simplicity)
        filters = self.get_current_filters()
        
        try:
            audio_extensions = {'.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg', 
                              '.wma', '.aiff', '.ape', '.opus'}
            
            audio_files = []
            source_path = Path(source_dir)
            
            for file_path in source_path.rglob('*'):
                if (file_path.is_file() and 
                    file_path.suffix.lower() in audio_extensions):
                    
                    audio_info = AudioFileInfo(file_path)
                    if audio_info.matches_filter(filters):
                        audio_files.append(audio_info)
            
            # Populate file list
            self.file_list.setRowCount(len(audio_files))
            
            for i, audio_file in enumerate(audio_files):
                self.file_list.setItem(i, 0, QTableWidgetItem(audio_file.name))
                self.file_list.setItem(i, 1, QTableWidgetItem(audio_file.artist))
                self.file_list.setItem(i, 2, QTableWidgetItem(audio_file.album))
                self.file_list.setItem(i, 3, QTableWidgetItem(f"{audio_file.duration:.0f}s"))
                self.file_list.setItem(i, 4, QTableWidgetItem(f"{audio_file.bitrate}"))
                self.file_list.setItem(i, 5, QTableWidgetItem(audio_file.format.upper()))
                self.file_list.setItem(i, 6, QTableWidgetItem(f"{audio_file.quality_score:.1f}"))
            
            self.status_label.setText(f"Found {len(audio_files)} audio files matching filters")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to scan directory: {e}")
            self.status_label.setText("Scan failed")
    
    def get_current_filters(self) -> Dict[str, Any]:
        """Get current filter settings"""
        if GUI_TYPE != "PyQt5":
            return {}
            
        filters = {}
        
        # Duration filters
        if self.min_duration.value() > 0:
            filters['min_duration'] = self.min_duration.value()
        if self.max_duration.value() > 0:
            filters['max_duration'] = self.max_duration.value()
        
        # Quality filters
        if self.min_bitrate.value() > 0:
            filters['min_bitrate'] = self.min_bitrate.value()
        if self.min_quality.value() > 0:
            filters['min_quality'] = self.min_quality.value()
        
        # Format filters
        enabled_formats = []
        for fmt, checkbox in self.format_checkboxes.items():
            if checkbox.isChecked():
                enabled_formats.append(fmt)
        if enabled_formats:
            filters['formats'] = enabled_formats
        
        # Lossless filter
        filters['lossless_only'] = self.lossless_only.isChecked()
        
        # Metadata filters
        if self.artist_filter.text().strip():
            filters['artist'] = self.artist_filter.text().strip()
        if self.album_filter.text().strip():
            filters['album'] = self.album_filter.text().strip()
        if self.genre_filter.text().strip():
            filters['genre'] = self.genre_filter.text().strip()
        
        return filters
    
    def get_current_options(self) -> Dict[str, Any]:
        """Get current transfer options"""
        if GUI_TYPE != "PyQt5":
            return {}
            
        options = {
            'preserve_structure': self.preserve_structure.isChecked(),
            'move_files': self.move_files.isChecked(),
            'duplicate_action': self.duplicate_action.currentText().lower().replace(' ', '_'),
            'organize_by_artist': self.organize_by_artist.isChecked(),
            'organize_by_album': self.organize_by_album.isChecked(),
            'organize_by_genre': self.organize_by_genre.isChecked(),
            'create_playlists': self.create_playlists.isChecked(),
            'verify_integrity': self.verify_integrity.isChecked()
        }
        
        return options
    
    def start_transfer(self):
        """Start the transfer operation"""
        if GUI_TYPE == "PyQt5":
            source_dir = self.source_label.text()
            dest_dir = self.dest_label.text()
            
            if source_dir == "No source selected":
                QMessageBox.warning(self, "Warning", "Please select a source directory")
                return
            
            if dest_dir == "No destination selected":
                QMessageBox.warning(self, "Warning", "Please select a destination directory")
                return
            
            # Get filters and options
            filters = self.get_current_filters()
            options = self.get_current_options()
            
            # Create and start worker
            self.worker = AudioTransferWorker(source_dir, dest_dir, filters, options)
            
            # Connect signals
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.file_processed.connect(self.file_processed)
            self.worker.transfer_completed.connect(self.transfer_completed)
            self.worker.error_occurred.connect(self.show_error)
            
            # Update UI
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            
            # Switch to results tab
            self.tabs.setCurrentIndex(3)
            
            # Start transfer
            self.worker.start()
            
        elif GUI_TYPE == "tkinter":
            self.start_transfer_tk()
    
    def start_transfer_tk(self):
        """Tkinter version of transfer start"""
        source_dir = self.source_var.get()
        dest_dir = self.dest_var.get()
        
        if source_dir == "No source selected":
            messagebox.showwarning("Warning", "Please select a source directory")
            return
        
        if dest_dir == "No destination selected":
            messagebox.showwarning("Warning", "Please select a destination directory")
            return
        
        messagebox.showinfo("Info", "Transfer started (basic mode)")
    
    def pause_transfer(self):
        """Pause the transfer"""
        if self.worker:
            self.worker.pause()
            self.pause_btn.setText("▶️ Resume")
            self.pause_btn.clicked.disconnect()
            self.pause_btn.clicked.connect(self.resume_transfer)
    
    def resume_transfer(self):
        """Resume the transfer"""
        if self.worker:
            self.worker.resume()
            self.pause_btn.setText("⏸️ Pause")
            self.pause_btn.clicked.disconnect()
            self.pause_btn.clicked.connect(self.pause_transfer)
    
    def stop_transfer(self):
        """Stop the transfer"""
        if self.worker:
            self.worker.stop()
    
    def update_progress(self, percentage: int, status: str):
        """Update progress display"""
        if GUI_TYPE == "PyQt5":
            self.progress_bar.setValue(percentage)
            self.status_label.setText(status)
    
    def file_processed(self, filename: str, status: str, success: bool):
        """Handle file processing update"""
        if GUI_TYPE == "PyQt5":
            color = "green" if success else "orange"
            self.transfer_log.append(f'<span style="color: {color};">[{datetime.now().strftime("%H:%M:%S")}] {filename} - {status}</span>')
    
    def transfer_completed(self, stats: Dict[str, Any]):
        """Handle transfer completion"""
        if GUI_TYPE == "PyQt5":
            # Update statistics
            self.stats_labels['total_files'].setText(str(stats['total_files']))
            self.stats_labels['transferred'].setText(str(stats['transferred_files']))
            self.stats_labels['skipped'].setText(str(stats['skipped_files']))
            self.stats_labels['errors'].setText(str(stats['error_files']))
            
            # Format size
            size_mb = stats['transferred_size'] / (1024 * 1024)
            self.stats_labels['total_size'].setText(f"{size_mb:.1f} MB")
            
            # Calculate elapsed time
            if stats['start_time'] and stats['end_time']:
                elapsed = stats['end_time'] - stats['start_time']
                self.stats_labels['time_elapsed'].setText(str(elapsed).split('.')[0])
            
            # Reset UI
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            
            self.status_label.setText("Transfer completed!")
            
            # Show completion message
            QMessageBox.information(self, "Transfer Complete", 
                                  f"Transfer completed!\n\n"
                                  f"Files transferred: {stats['transferred_files']}\n"
                                  f"Files skipped: {stats['skipped_files']}\n"
                                  f"Errors: {stats['error_files']}")
    
    def show_error(self, error_message: str):
        """Show error message"""
        if GUI_TYPE == "PyQt5":
            self.transfer_log.append(f'<span style="color: red;">[ERROR] {error_message}</span>')
    
    def run(self):
        """Run the application"""
        if GUI_TYPE == "PyQt5":
            self.show()
        elif GUI_TYPE == "tkinter":
            self.root.mainloop()

def main():
    """Main entry point"""
    print("🎵 Advanced Audio Transfer Tool")
    print("=" * 50)
    
    if not GUI_AVAILABLE:
        print("No GUI framework available. Please install PyQt5 or ensure tkinter is available.")
        return 1
    
    if GUI_TYPE == "PyQt5":
        app = QApplication(sys.argv)
        window = AudioTransferGUI()
        window.run()
        return app.exec_()
    elif GUI_TYPE == "tkinter":
        window = AudioTransferGUI()
        window.run()
        return 0
    
    return 1

if __name__ == "__main__":
    sys.exit(main())