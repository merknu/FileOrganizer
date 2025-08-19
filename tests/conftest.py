"""
Pytest configuration and shared fixtures for FileOrganizer tests.
"""

import os
import tempfile
import shutil
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock

import pytest

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Provide a test configuration dictionary."""
    return {
        "default_duplicate_action": "k",
        "file_categories": {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
            "Documents": [".pdf", ".docx", ".doc", ".txt"],
            "Audio": [".mp3", ".wav", ".flac"],
            "Video": [".mp4", ".avi", ".mov"]
        },
        "subfolders": {
            ".jpg": "Images",
            ".jpeg": "Images", 
            ".png": "Images",
            ".gif": "Images",
            ".bmp": "Images",
            ".pdf": "Documents",
            ".docx": "Documents",
            ".doc": "Documents",
            ".txt": "Documents",
            ".mp3": "Audio",
            ".wav": "Audio",
            ".flac": "Audio",
            ".mp4": "Video",
            ".avi": "Video",
            ".mov": "Video"
        }
    }


@pytest.fixture
def test_config_file(temp_dir, test_config):
    """Create a temporary configuration file."""
    config_path = os.path.join(temp_dir, "test_config.json")
    with open(config_path, 'w') as f:
        json.dump(test_config, f, indent=2)
    return config_path


@pytest.fixture
def sample_files_structure(temp_dir):
    """Create a sample directory structure with test files."""
    structure = {
        "test_folder": {
            "files": [
                ("image1.jpg", b"fake jpeg data"),
                ("document1.pdf", b"fake pdf data"),
                ("audio1.mp3", b"fake mp3 data"),
                ("video1.mp4", b"fake mp4 data"),
                ("text1.txt", b"fake text content"),
                ("no_extension", b"file without extension")
            ],
            "subdirs": {
                "nested": {
                    "files": [
                        ("nested_image.png", b"fake png data"),
                        ("nested_doc.docx", b"fake docx data")
                    ]
                }
            }
        }
    }
    
    def create_structure(base_path, struct):
        for name, content in struct.items():
            if name == "files":
                for filename, data in content:
                    file_path = os.path.join(base_path, filename)
                    with open(file_path, 'wb') as f:
                        f.write(data)
            elif name == "subdirs":
                for subdir_name, subdir_content in content.items():
                    subdir_path = os.path.join(base_path, subdir_name)
                    os.makedirs(subdir_path, exist_ok=True)
                    create_structure(subdir_path, subdir_content)
    
    test_folder = os.path.join(temp_dir, "test_folder")
    os.makedirs(test_folder)
    create_structure(test_folder, structure["test_folder"])
    
    return test_folder


@pytest.fixture
def mock_image_file(temp_dir):
    """Create a mock image file for testing."""
    image_path = os.path.join(temp_dir, "test_image.jpg")
    # Create a minimal JPEG-like file
    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01'
    with open(image_path, 'wb') as f:
        f.write(jpeg_header + b'\x00' * 100)  # Minimal content
    return image_path


@pytest.fixture
def mock_audio_file(temp_dir):
    """Create a mock audio file for testing."""
    audio_path = os.path.join(temp_dir, "test_audio.mp3")
    # Create a minimal MP3-like file
    mp3_header = b'ID3\x03\x00\x00\x00'
    with open(audio_path, 'wb') as f:
        f.write(mp3_header + b'\x00' * 100)
    return audio_path


@pytest.fixture
def mock_document_file(temp_dir):
    """Create a mock document file for testing."""
    doc_path = os.path.join(temp_dir, "test_document.pdf")
    # Create a minimal PDF-like file
    pdf_header = b'%PDF-1.4\n'
    with open(doc_path, 'wb') as f:
        f.write(pdf_header + b'fake pdf content')
    return doc_path


@pytest.fixture
def duplicate_files_setup(temp_dir):
    """Create a setup with duplicate files for testing."""
    # Original file
    original_path = os.path.join(temp_dir, "original.txt")
    content = b"This is test content for duplicate testing"
    with open(original_path, 'wb') as f:
        f.write(content)
    
    # Create target directory
    target_dir = os.path.join(temp_dir, "target")
    os.makedirs(target_dir)
    
    # Duplicate file in target
    duplicate_path = os.path.join(target_dir, "original.txt")
    with open(duplicate_path, 'wb') as f:
        f.write(content)  # Same content
    
    # Different file with same name
    different_path = os.path.join(temp_dir, "different.txt") 
    with open(different_path, 'wb') as f:
        f.write(b"Different content")
    
    return {
        "original": original_path,
        "duplicate": duplicate_path,
        "different": different_path,
        "target_dir": target_dir
    }


@pytest.fixture
def mock_pyqt_app():
    """Mock PyQt5 application for GUI tests."""
    try:
        from PyQt5.QtWidgets import QApplication
        import sys
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        yield app
    except ImportError:
        # If PyQt5 not available, provide mock
        mock_app = Mock()
        mock_app.processEvents = Mock()
        yield mock_app


@pytest.fixture
def mock_processing_thread():
    """Mock processing thread for testing."""
    mock_thread = Mock()
    mock_thread.start = Mock()
    mock_thread.stop = Mock()
    mock_thread.wait = Mock()
    mock_thread.isRunning = Mock(return_value=False)
    mock_thread.processing_finished = Mock()
    mock_thread.error_occurred = Mock()
    mock_thread.file_processed = Mock()
    mock_thread.status_changed = Mock()
    mock_thread.progress_changed = Mock()
    return mock_thread


@pytest.fixture
def mock_file_operations(monkeypatch):
    """Mock file operations to prevent actual file system changes during tests."""
    move_mock = Mock()
    hash_mock = Mock(return_value="mock_hash_123")
    
    monkeypatch.setattr("file_handler.file_operations.move_file", move_mock)
    monkeypatch.setattr("file_handler.file_operations.calculate_file_hash", hash_mock)
    
    return {
        "move_file": move_mock,
        "calculate_file_hash": hash_mock
    }


@pytest.fixture(autouse=True)
def suppress_gui_output(monkeypatch):
    """Suppress GUI-related output during tests."""
    # Mock logging to reduce noise during tests
    mock_logger = Mock()
    mock_logger.info = Mock()
    mock_logger.warning = Mock()
    mock_logger.error = Mock()
    mock_logger.debug = Mock()
    
    # Don't actually apply this automatically - let individual tests decide
    return mock_logger


@pytest.fixture
def test_files_with_metadata(temp_dir):
    """Create test files with different properties for metadata testing."""
    files = {}
    
    # Text file with known content
    text_file = os.path.join(temp_dir, "sample.txt")
    text_content = "Hello world this is a test document with exactly ten words."
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text_content)
    files['text'] = text_file
    
    # Binary file
    binary_file = os.path.join(temp_dir, "sample.bin")
    with open(binary_file, 'wb') as f:
        f.write(b'\x00\x01\x02\x03' * 100)
    files['binary'] = binary_file
    
    return files


@pytest.fixture
def error_conditions_setup(temp_dir):
    """Setup various error conditions for testing."""
    conditions = {}
    
    # Non-existent file
    conditions['non_existent'] = os.path.join(temp_dir, "does_not_exist.txt")
    
    # Read-only directory (if supported)
    readonly_dir = os.path.join(temp_dir, "readonly")
    os.makedirs(readonly_dir)
    try:
        os.chmod(readonly_dir, 0o444)  # Read-only
        conditions['readonly_dir'] = readonly_dir
    except (OSError, AttributeError):
        conditions['readonly_dir'] = None
    
    # Empty file
    empty_file = os.path.join(temp_dir, "empty.txt")
    Path(empty_file).touch()
    conditions['empty_file'] = empty_file
    
    return conditions


# Helper functions for tests
def create_test_file(path: str, content: bytes = b"test content", size: int = None) -> str:
    """Create a test file with specified content or size."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    if size is not None:
        content = b'\x00' * size
    
    with open(path, 'wb') as f:
        f.write(content)
    
    return path


def count_files_in_directory(directory: str, recursive: bool = True) -> int:
    """Count files in a directory."""
    count = 0
    if recursive:
        for root, dirs, files in os.walk(directory):
            count += len(files)
    else:
        try:
            items = os.listdir(directory)
            count = sum(1 for item in items 
                       if os.path.isfile(os.path.join(directory, item)))
        except (OSError, FileNotFoundError):
            count = 0
    return count


def get_directory_structure(directory: str) -> Dict:
    """Get directory structure as a dictionary for comparison."""
    structure = {}
    try:
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                structure[item] = get_directory_structure(item_path)
            else:
                structure[item] = "file"
    except (OSError, FileNotFoundError):
        pass
    return structure