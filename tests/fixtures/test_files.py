"""
Test file fixtures and utilities for creating test data.

This module provides utilities for creating various types of test files
with specific content and metadata for comprehensive testing.
"""

import os
import struct
import json
from typing import Dict, List, Tuple
from pathlib import Path


class TestFileCreator:
    """Utility class for creating test files with specific properties."""
    
    @staticmethod
    def create_text_file(path: str, content: str = None, word_count: int = None) -> str:
        """Create a text file with specified content or word count."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        if content is None and word_count is not None:
            # Generate content with exact word count
            words = [f"word{i}" for i in range(word_count)]
            content = " ".join(words)
        elif content is None:
            content = "Default test content"
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return path
    
    @staticmethod
    def create_binary_file(path: str, size: int = 1024) -> str:
        """Create a binary file with specified size."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'wb') as f:
            # Create pattern-based binary content
            pattern = bytes(range(256))
            full_patterns = size // 256
            remainder = size % 256
            
            for _ in range(full_patterns):
                f.write(pattern)
            if remainder:
                f.write(pattern[:remainder])
        
        return path
    
    @staticmethod
    def create_fake_image(path: str, width: int = 100, height: int = 100) -> str:
        """Create a fake image file with minimal valid header."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        ext = os.path.splitext(path)[1].lower()
        
        if ext == '.jpg' or ext == '.jpeg':
            # Minimal JPEG header
            header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00'
            # Add fake dimensions in comment segment
            comment = f'Fake JPEG {width}x{height}'.encode('ascii')
            header += b'\xff\xfe' + struct.pack('>H', len(comment) + 2) + comment
            # End marker
            header += b'\xff\xd9'
            
        elif ext == '.png':
            # PNG signature
            header = b'\x89PNG\r\n\x1a\n'
            # IHDR chunk with dimensions
            ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
            ihdr_crc = 0x12345678  # Fake CRC
            header += b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
            
        elif ext == '.gif':
            # GIF header
            header = b'GIF89a'
            # Logical screen descriptor
            header += struct.pack('<HH', width, height)
            header += b'\x00\x00\x00'  # Global color table info
            
        elif ext == '.bmp':
            # BMP header (simplified)
            file_size = 54 + (width * height * 3)  # 24-bit
            header = b'BM' + struct.pack('<I', file_size) + b'\x00\x00\x00\x00\x36\x00\x00\x00'
            header += b'\x28\x00\x00\x00' + struct.pack('<II', width, height)
            header += b'\x01\x00\x18\x00' + b'\x00' * 24
            
        else:
            header = b'FAKE_IMAGE_DATA'
        
        with open(path, 'wb') as f:
            f.write(header)
            # Add some padding
            f.write(b'\x00' * 100)
        
        return path
    
    @staticmethod
    def create_fake_audio(path: str, duration_seconds: float = 10.0) -> str:
        """Create a fake audio file with minimal valid header."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        ext = os.path.splitext(path)[1].lower()
        
        if ext == '.mp3':
            # ID3v2 header
            header = b'ID3\x03\x00\x00\x00\x00\x00\x00'
            # Add fake MP3 frame header
            header += b'\xff\xfb\x90\x00'  # MP3 sync + info
            # Add duration info in a custom way (not standard but for testing)
            duration_bytes = struct.pack('<f', duration_seconds)
            header += b'DURATION' + duration_bytes
            
        elif ext == '.wav':
            # WAV header
            sample_rate = 44100
            num_samples = int(duration_seconds * sample_rate)
            data_size = num_samples * 2  # 16-bit mono
            
            header = b'RIFF' + struct.pack('<I', 36 + data_size) + b'WAVE'
            header += b'fmt ' + struct.pack('<IHHIIHH', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
            header += b'data' + struct.pack('<I', data_size)
            
        elif ext == '.flac':
            # FLAC header
            header = b'fLaC'  # FLAC signature
            # Streaminfo metadata block (simplified)
            header += b'\x00\x00\x00\x22'  # Last metadata block + length
            header += b'\x00\x00\x00\x00' + struct.pack('>I', int(duration_seconds * 44100))  # Total samples
            
        else:
            header = b'FAKE_AUDIO_DATA'
        
        with open(path, 'wb') as f:
            f.write(header)
            f.write(b'\x00' * 1000)  # Padding
        
        return path
    
    @staticmethod
    def create_fake_video(path: str, duration_seconds: float = 30.0) -> str:
        """Create a fake video file with minimal valid header."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        ext = os.path.splitext(path)[1].lower()
        
        if ext == '.mp4':
            # MP4 header (ftyp box)
            header = b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41'
            # Add fake duration in a custom way
            duration_bytes = struct.pack('>I', int(duration_seconds * 1000))  # milliseconds
            header += b'DURATION' + duration_bytes
            
        elif ext == '.avi':
            # AVI header
            header = b'RIFF\x00\x00\x00\x00AVI '
            header += b'LIST\x00\x00\x00\x00hdrlavih'
            # Add duration (microseconds per frame * total frames)
            frame_rate = 25
            total_frames = int(duration_seconds * frame_rate)
            microseconds_per_frame = int(1000000 / frame_rate)
            header += struct.pack('<I', microseconds_per_frame)
            header += struct.pack('<I', total_frames)
            
        elif ext == '.mov':
            # QuickTime header
            header = b'\x00\x00\x00\x14ftypqt  '
            # Add fake duration
            header += b'DURATION' + struct.pack('>f', duration_seconds)
            
        else:
            header = b'FAKE_VIDEO_DATA'
        
        with open(path, 'wb') as f:
            f.write(header)
            f.write(b'\x00' * 2000)  # Padding
        
        return path
    
    @staticmethod
    def create_fake_pdf(path: str, page_count: int = 1, words_per_page: int = 100) -> str:
        """Create a fake PDF file with specified content."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Minimal PDF structure
        content = "%PDF-1.4\n"
        content += "1 0 obj\n"
        content += "<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
        content += "2 0 obj\n"
        content += f"<<\n/Type /Pages\n/Kids [3 0 R]\n/Count {page_count}\n>>\nendobj\n"
        
        for page_num in range(page_count):
            obj_num = 3 + page_num
            # Page content with fake text
            page_text = " ".join([f"word{i}" for i in range(words_per_page)])
            content += f"{obj_num} 0 obj\n"
            content += "<<\n/Type /Page\n/Parent 2 0 R\n"
            content += f"/Contents [{obj_num + page_count} 0 R]\n>>\nendobj\n"
            
            # Content stream
            stream_obj = obj_num + page_count
            content += f"{stream_obj} 0 obj\n"
            content += f"<<\n/Length {len(page_text)}\n>>\nstream\n"
            content += f"BT\n/F1 12 Tf\n72 720 Td\n({page_text}) Tj\nET\n"
            content += "endstream\nendobj\n"
        
        content += "xref\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n%%EOF\n"
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return path
    
    @staticmethod
    def create_fake_docx(path: str, paragraph_count: int = 3, words_per_paragraph: int = 20) -> str:
        """Create a fake DOCX file (actually just a text file for testing)."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # For testing purposes, create a simple file that can be processed
        # In real implementation, this would be a proper DOCX structure
        content = "FAKE_DOCX_HEADER\n"
        
        for para_num in range(paragraph_count):
            paragraph_words = [f"paragraph{para_num}_word{i}" for i in range(words_per_paragraph)]
            content += " ".join(paragraph_words) + "\n"
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return path


class TestDataManager:
    """Manager for creating complex test data structures."""
    
    def __init__(self, base_dir: str):
        """Initialize with base directory for test data."""
        self.base_dir = Path(base_dir)
        self.creator = TestFileCreator()
    
    def create_sample_directory_structure(self) -> Dict[str, str]:
        """Create a comprehensive directory structure for testing."""
        structure = {}
        
        # Create main test directory
        test_dir = self.base_dir / "sample_files"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Images
        images_dir = test_dir / "images"
        structure.update({
            "small_image": self.creator.create_fake_image(
                str(images_dir / "small.jpg"), 640, 480
            ),
            "large_image": self.creator.create_fake_image(
                str(images_dir / "large.png"), 1920, 1080
            ),
            "gif_image": self.creator.create_fake_image(
                str(images_dir / "animated.gif"), 200, 200
            ),
        })
        
        # Audio files
        audio_dir = test_dir / "audio"
        structure.update({
            "short_audio": self.creator.create_fake_audio(
                str(audio_dir / "short.mp3"), 30.0
            ),
            "long_audio": self.creator.create_fake_audio(
                str(audio_dir / "long.wav"), 180.5
            ),
            "flac_audio": self.creator.create_fake_audio(
                str(audio_dir / "lossless.flac"), 120.0
            ),
        })
        
        # Video files
        video_dir = test_dir / "video"
        structure.update({
            "short_video": self.creator.create_fake_video(
                str(video_dir / "clip.mp4"), 60.0
            ),
            "long_video": self.creator.create_fake_video(
                str(video_dir / "movie.avi"), 3600.0
            ),
        })
        
        # Documents
        docs_dir = test_dir / "documents"
        structure.update({
            "text_doc": self.creator.create_text_file(
                str(docs_dir / "document.txt"), word_count=150
            ),
            "pdf_doc": self.creator.create_fake_pdf(
                str(docs_dir / "report.pdf"), page_count=3, words_per_page=200
            ),
            "word_doc": self.creator.create_fake_docx(
                str(docs_dir / "letter.docx"), paragraph_count=5, words_per_paragraph=30
            ),
        })
        
        # Mixed content with subdirectories
        mixed_dir = test_dir / "mixed"
        subdir = mixed_dir / "subfolder"
        structure.update({
            "mixed_image": self.creator.create_fake_image(
                str(mixed_dir / "photo.jpg"), 800, 600
            ),
            "mixed_audio": self.creator.create_fake_audio(
                str(mixed_dir / "sound.mp3"), 45.0
            ),
            "nested_doc": self.creator.create_text_file(
                str(subdir / "nested.txt"), word_count=75
            ),
            "no_extension": self.creator.create_text_file(
                str(mixed_dir / "no_extension"), "File without extension"
            ),
        })
        
        # Files for duplicate testing
        duplicates_dir = test_dir / "duplicates"
        original_content = "This is the original content for duplicate testing."
        structure.update({
            "original_file": self.creator.create_text_file(
                str(duplicates_dir / "original.txt"), original_content
            ),
            "duplicate_file": self.creator.create_text_file(
                str(duplicates_dir / "copy.txt"), original_content
            ),
            "similar_file": self.creator.create_text_file(
                str(duplicates_dir / "similar.txt"), "This is different content."
            ),
        })
        
        # Empty and special files
        special_dir = test_dir / "special"
        structure.update({
            "empty_file": self.creator.create_text_file(
                str(special_dir / "empty.txt"), ""
            ),
            "large_file": self.creator.create_binary_file(
                str(special_dir / "large.bin"), 1024 * 1024  # 1MB
            ),
            "unicode_file": self.creator.create_text_file(
                str(special_dir / "unicode.txt"), "Hello 世界 🌍 Тест"
            ),
        })
        
        return structure
    
    def create_error_condition_files(self) -> Dict[str, str]:
        """Create files that might cause processing errors."""
        structure = {}
        
        error_dir = self.base_dir / "error_conditions"
        error_dir.mkdir(parents=True, exist_ok=True)
        
        # Malformed files
        structure.update({
            "corrupt_image": self.creator.create_text_file(
                str(error_dir / "corrupt.jpg"), "This is not actually an image"
            ),
            "corrupt_audio": self.creator.create_text_file(
                str(error_dir / "corrupt.mp3"), "This is not actually audio"
            ),
            "corrupt_pdf": self.creator.create_text_file(
                str(error_dir / "corrupt.pdf"), "Not a real PDF"
            ),
        })
        
        # Very long filenames
        long_name = "very_long_filename_" + "a" * 200 + ".txt"
        structure["long_filename"] = self.creator.create_text_file(
            str(error_dir / long_name), "File with very long name"
        )
        
        # Special characters in filenames
        special_files = [
            "file with spaces.txt",
            "file-with-dashes.txt",
            "file_with_underscores.txt",
            "file.with.dots.txt",
            "file(with)parentheses.txt",
        ]
        
        for filename in special_files:
            key = filename.replace(" ", "_").replace("(", "").replace(")", "").replace(".", "_")
            structure[key] = self.creator.create_text_file(
                str(error_dir / filename), f"Content for {filename}"
            )
        
        return structure
    
    def create_performance_test_files(self, file_count: int = 100) -> List[str]:
        """Create many files for performance testing."""
        perf_dir = self.base_dir / "performance"
        perf_dir.mkdir(parents=True, exist_ok=True)
        
        files = []
        file_types = [
            ('.txt', lambda i: self.creator.create_text_file(
                str(perf_dir / f"text_{i:03d}.txt"), word_count=50
            )),
            ('.jpg', lambda i: self.creator.create_fake_image(
                str(perf_dir / f"image_{i:03d}.jpg"), 200, 200
            )),
            ('.mp3', lambda i: self.creator.create_fake_audio(
                str(perf_dir / f"audio_{i:03d}.mp3"), 30.0
            )),
            ('.pdf', lambda i: self.creator.create_fake_pdf(
                str(perf_dir / f"doc_{i:03d}.pdf"), 1, 100
            )),
        ]
        
        for i in range(file_count):
            file_type_index = i % len(file_types)
            ext, creator_func = file_types[file_type_index]
            file_path = creator_func(i)
            files.append(file_path)
        
        return files
    
    def cleanup(self):
        """Remove all created test files."""
        import shutil
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)


def create_test_config_variations() -> Dict[str, Dict]:
    """Create various configuration variations for testing."""
    
    base_config = {
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
    
    variations = {
        "minimal": {
            "default_duplicate_action": "k",
            "file_categories": {
                "Images": [".jpg"],
                "Documents": [".txt"]
            },
            "subfolders": {
                ".jpg": "Images",
                ".txt": "Documents"
            }
        },
        
        "comprehensive": {
            **base_config,
            "file_categories": {
                **base_config["file_categories"],
                "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
                "Code": [".py", ".js", ".html", ".css", ".cpp", ".java"],
            },
            "subfolders": {
                **base_config["subfolders"],
                ".zip": "Archives",
                ".rar": "Archives",
                ".py": "Code",
                ".js": "Code"
            }
        },
        
        "different_actions": {
            **base_config,
            "default_duplicate_action": "o"  # Overwrite instead of keep
        },
        
        "empty_categories": {
            "default_duplicate_action": "r",
            "file_categories": {},
            "subfolders": {}
        }
    }
    
    return variations