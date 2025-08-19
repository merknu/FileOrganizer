"""
Unit tests for file_handler.file_operations module.

Tests cover:
- File moving operations
- File hash calculations
- Timestamp preservation
- Error handling for file operations
- Edge cases with different file types and sizes
"""

import os
import shutil
import hashlib
import tempfile
import time
from unittest.mock import Mock, patch, call

import pytest

from file_handler.file_operations import (
    move_file,
    preserve_timestamps,
    calculate_file_hash
)


class TestMoveFile:
    """Test file moving functionality."""
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_move_file_success(self, temp_dir):
        """Test successful file moving."""
        # Create source file
        src_file = os.path.join(temp_dir, "source.txt")
        with open(src_file, 'w') as f:
            f.write("test content")
        
        # Create destination directory
        dest_dir = os.path.join(temp_dir, "dest")
        os.makedirs(dest_dir)
        dest_file = os.path.join(dest_dir, "moved.txt")
        
        # Mock preserve_timestamps to avoid timestamp issues in tests
        with patch('file_handler.file_operations.preserve_timestamps') as mock_preserve:
            move_file(src_file, dest_file)
            
            # Verify file was moved
            assert not os.path.exists(src_file)
            assert os.path.exists(dest_file)
            
            # Verify content
            with open(dest_file, 'r') as f:
                content = f.read()
            assert content == "test content"
            
            # Verify preserve_timestamps was called
            mock_preserve.assert_called_once_with(src_file, dest_file)
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_move_file_overwrite_existing(self, temp_dir):
        """Test moving file to location with existing file."""
        # Create source file
        src_file = os.path.join(temp_dir, "source.txt")
        with open(src_file, 'w') as f:
            f.write("new content")
        
        # Create existing destination file
        dest_file = os.path.join(temp_dir, "existing.txt")
        with open(dest_file, 'w') as f:
            f.write("old content")
        
        with patch('file_handler.file_operations.preserve_timestamps'):
            move_file(src_file, dest_file)
            
            # Verify source is gone and destination has new content
            assert not os.path.exists(src_file)
            assert os.path.exists(dest_file)
            
            with open(dest_file, 'r') as f:
                content = f.read()
            assert content == "new content"
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_move_file_create_destination_directory(self, temp_dir):
        """Test moving file to non-existent destination directory."""
        # Create source file
        src_file = os.path.join(temp_dir, "source.txt")
        with open(src_file, 'w') as f:
            f.write("test content")
        
        # Destination in non-existent directory
        dest_file = os.path.join(temp_dir, "nonexistent", "moved.txt")
        
        with patch('file_handler.file_operations.preserve_timestamps'):
            # shutil.move should create the directory automatically
            move_file(src_file, dest_file)
            
            assert not os.path.exists(src_file)
            assert os.path.exists(dest_file)
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_move_file_same_location(self, temp_dir):
        """Test moving file to same location."""
        src_file = os.path.join(temp_dir, "same.txt")
        with open(src_file, 'w') as f:
            f.write("content")
        
        with patch('file_handler.file_operations.preserve_timestamps'):
            # Moving to same location should work without issues
            move_file(src_file, src_file)
            
            # File should still exist
            assert os.path.exists(src_file)
    
    @pytest.mark.unit
    def test_move_file_source_not_found(self, temp_dir):
        """Test moving non-existent source file."""
        src_file = os.path.join(temp_dir, "nonexistent.txt")
        dest_file = os.path.join(temp_dir, "dest.txt")
        
        with pytest.raises(FileNotFoundError):
            move_file(src_file, dest_file)
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_move_file_permission_denied(self, temp_dir):
        """Test moving file when permission is denied."""
        src_file = os.path.join(temp_dir, "source.txt")
        with open(src_file, 'w') as f:
            f.write("content")
        
        dest_file = os.path.join(temp_dir, "dest.txt")
        
        # Mock shutil.move to raise PermissionError
        with patch('shutil.move', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                move_file(src_file, dest_file)
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_move_file_with_binary_content(self, temp_dir):
        """Test moving file with binary content."""
        src_file = os.path.join(temp_dir, "binary.bin")
        binary_content = b'\x00\x01\x02\x03\xff\xfe\xfd\xfc'
        
        with open(src_file, 'wb') as f:
            f.write(binary_content)
        
        dest_file = os.path.join(temp_dir, "moved_binary.bin")
        
        with patch('file_handler.file_operations.preserve_timestamps'):
            move_file(src_file, dest_file)
            
            assert not os.path.exists(src_file)
            assert os.path.exists(dest_file)
            
            with open(dest_file, 'rb') as f:
                moved_content = f.read()
            assert moved_content == binary_content
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_move_large_file(self, temp_dir):
        """Test moving a large file."""
        src_file = os.path.join(temp_dir, "large.txt")
        
        # Create a reasonably large file (1MB)
        large_content = "a" * (1024 * 1024)
        with open(src_file, 'w') as f:
            f.write(large_content)
        
        dest_file = os.path.join(temp_dir, "large_moved.txt")
        
        with patch('file_handler.file_operations.preserve_timestamps'):
            move_file(src_file, dest_file)
            
            assert not os.path.exists(src_file)
            assert os.path.exists(dest_file)
            
            # Verify file size
            assert os.path.getsize(dest_file) == len(large_content)


class TestPreserveTimestamps:
    """Test timestamp preservation functionality."""
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_preserve_timestamps_success(self, temp_dir):
        """Test successful timestamp preservation."""
        src_file = os.path.join(temp_dir, "source.txt")
        dest_file = os.path.join(temp_dir, "dest.txt")
        
        # Create source file and get its timestamps
        with open(src_file, 'w') as f:
            f.write("content")
        
        # Create dest file
        with open(dest_file, 'w') as f:
            f.write("content")
        
        # Get original timestamps
        src_stat = os.stat(src_file)
        original_atime = src_stat.st_atime
        original_mtime = src_stat.st_mtime
        
        # Wait a bit to ensure different timestamps
        time.sleep(0.1)
        
        # Modify dest file timestamp
        current_time = time.time()
        os.utime(dest_file, (current_time, current_time))
        
        # Preserve timestamps
        preserve_timestamps(src_file, dest_file)
        
        # Check that timestamps were preserved
        dest_stat = os.stat(dest_file)
        assert abs(dest_stat.st_atime - original_atime) < 1.0  # Allow small difference due to precision
        assert abs(dest_stat.st_mtime - original_mtime) < 1.0
    
    @pytest.mark.unit
    def test_preserve_timestamps_source_not_found(self, temp_dir):
        """Test timestamp preservation with non-existent source file."""
        src_file = os.path.join(temp_dir, "nonexistent.txt")
        dest_file = os.path.join(temp_dir, "dest.txt")
        
        with open(dest_file, 'w') as f:
            f.write("content")
        
        with pytest.raises(FileNotFoundError):
            preserve_timestamps(src_file, dest_file)
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_preserve_timestamps_dest_not_found(self, temp_dir):
        """Test timestamp preservation with non-existent destination file."""
        src_file = os.path.join(temp_dir, "source.txt")
        dest_file = os.path.join(temp_dir, "nonexistent.txt")
        
        with open(src_file, 'w') as f:
            f.write("content")
        
        with pytest.raises(FileNotFoundError):
            preserve_timestamps(src_file, dest_file)
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_preserve_timestamps_permission_error(self, temp_dir):
        """Test timestamp preservation with permission error."""
        src_file = os.path.join(temp_dir, "source.txt")
        dest_file = os.path.join(temp_dir, "dest.txt")
        
        with open(src_file, 'w') as f:
            f.write("content")
        with open(dest_file, 'w') as f:
            f.write("content")
        
        # Mock os.utime to raise PermissionError
        with patch('os.utime', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                preserve_timestamps(src_file, dest_file)


class TestCalculateFileHash:
    """Test file hash calculation functionality."""
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_calculate_file_hash_success(self, temp_dir):
        """Test successful file hash calculation."""
        test_file = os.path.join(temp_dir, "test.txt")
        test_content = b"Hello, World!"
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        result = calculate_file_hash(test_file)
        
        # Calculate expected hash
        expected_hash = hashlib.sha256(test_content).hexdigest()
        assert result == expected_hash
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_calculate_file_hash_empty_file(self, temp_dir):
        """Test hash calculation for empty file."""
        test_file = os.path.join(temp_dir, "empty.txt")
        
        # Create empty file
        with open(test_file, 'wb') as f:
            pass
        
        result = calculate_file_hash(test_file)
        
        # Hash of empty content
        expected_hash = hashlib.sha256(b"").hexdigest()
        assert result == expected_hash
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_calculate_file_hash_binary_content(self, temp_dir):
        """Test hash calculation for binary file."""
        test_file = os.path.join(temp_dir, "binary.bin")
        binary_content = bytes(range(256))  # All byte values 0-255
        
        with open(test_file, 'wb') as f:
            f.write(binary_content)
        
        result = calculate_file_hash(test_file)
        
        expected_hash = hashlib.sha256(binary_content).hexdigest()
        assert result == expected_hash
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_calculate_file_hash_large_file(self, temp_dir):
        """Test hash calculation for large file."""
        test_file = os.path.join(temp_dir, "large.txt")
        
        # Create a 1MB file with repeated pattern
        pattern = b"0123456789" * 1024  # 10KB pattern
        large_content = pattern * 100  # 1MB total
        
        with open(test_file, 'wb') as f:
            f.write(large_content)
        
        result = calculate_file_hash(test_file)
        
        expected_hash = hashlib.sha256(large_content).hexdigest()
        assert result == expected_hash
    
    @pytest.mark.unit
    def test_calculate_file_hash_file_not_found(self, temp_dir):
        """Test hash calculation for non-existent file."""
        nonexistent_file = os.path.join(temp_dir, "nonexistent.txt")
        
        with pytest.raises(FileNotFoundError):
            calculate_file_hash(nonexistent_file)
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_calculate_file_hash_permission_denied(self, temp_dir):
        """Test hash calculation when permission is denied."""
        test_file = os.path.join(temp_dir, "protected.txt")
        
        with open(test_file, 'w') as f:
            f.write("content")
        
        # Mock file opening to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                calculate_file_hash(test_file)
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_calculate_file_hash_consistency(self, temp_dir):
        """Test that hash calculation is consistent for same content."""
        test_content = b"Consistent content for testing"
        
        # Create two files with same content
        file1 = os.path.join(temp_dir, "file1.txt")
        file2 = os.path.join(temp_dir, "file2.txt")
        
        with open(file1, 'wb') as f:
            f.write(test_content)
        with open(file2, 'wb') as f:
            f.write(test_content)
        
        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)
        
        assert hash1 == hash2
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_calculate_file_hash_different_content(self, temp_dir):
        """Test that different content produces different hashes."""
        file1 = os.path.join(temp_dir, "file1.txt")
        file2 = os.path.join(temp_dir, "file2.txt")
        
        with open(file1, 'wb') as f:
            f.write(b"Content A")
        with open(file2, 'wb') as f:
            f.write(b"Content B")
        
        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)
        
        assert hash1 != hash2
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_calculate_file_hash_unicode_content(self, temp_dir):
        """Test hash calculation with Unicode content."""
        test_file = os.path.join(temp_dir, "unicode.txt")
        unicode_content = "Hello, 世界! 🌍".encode('utf-8')
        
        with open(test_file, 'wb') as f:
            f.write(unicode_content)
        
        result = calculate_file_hash(test_file)
        
        expected_hash = hashlib.sha256(unicode_content).hexdigest()
        assert result == expected_hash


class TestFileOperationsIntegration:
    """Test integration between file operations."""
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_move_and_hash_workflow(self, temp_dir):
        """Test complete workflow of moving file and verifying hash."""
        # Create source file
        src_file = os.path.join(temp_dir, "source.txt")
        test_content = b"Test content for move and hash verification"
        
        with open(src_file, 'wb') as f:
            f.write(test_content)
        
        # Calculate original hash
        original_hash = calculate_file_hash(src_file)
        
        # Move file
        dest_file = os.path.join(temp_dir, "moved.txt")
        with patch('file_handler.file_operations.preserve_timestamps'):
            move_file(src_file, dest_file)
        
        # Verify file was moved and content is intact
        assert not os.path.exists(src_file)
        assert os.path.exists(dest_file)
        
        # Calculate hash of moved file
        moved_hash = calculate_file_hash(dest_file)
        
        # Hashes should be identical
        assert original_hash == moved_hash
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_duplicate_detection_workflow(self, temp_dir):
        """Test workflow for detecting duplicate files."""
        content = b"Duplicate content for testing"
        
        # Create original file
        original = os.path.join(temp_dir, "original.txt")
        with open(original, 'wb') as f:
            f.write(content)
        
        # Create potential duplicate
        duplicate = os.path.join(temp_dir, "duplicate.txt")
        with open(duplicate, 'wb') as f:
            f.write(content)
        
        # Create different file
        different = os.path.join(temp_dir, "different.txt")
        with open(different, 'wb') as f:
            f.write(b"Different content")
        
        # Calculate hashes
        original_hash = calculate_file_hash(original)
        duplicate_hash = calculate_file_hash(duplicate)
        different_hash = calculate_file_hash(different)
        
        # Verify duplicate detection
        assert original_hash == duplicate_hash
        assert original_hash != different_hash
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_timestamp_preservation_after_move(self, temp_dir):
        """Test that timestamps are preserved after moving files."""
        # Create source file
        src_file = os.path.join(temp_dir, "source.txt")
        with open(src_file, 'w') as f:
            f.write("content")
        
        # Get original timestamps
        original_stat = os.stat(src_file)
        original_atime = original_stat.st_atime
        original_mtime = original_stat.st_mtime
        
        # Move file
        dest_file = os.path.join(temp_dir, "dest.txt")
        move_file(src_file, dest_file)  # This should call preserve_timestamps
        
        # Check preserved timestamps
        dest_stat = os.stat(dest_file)
        
        # Allow small difference due to filesystem precision
        assert abs(dest_stat.st_atime - original_atime) < 2.0
        assert abs(dest_stat.st_mtime - original_mtime) < 2.0


class TestFileOperationsEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.unit
    def test_operations_with_none_parameters(self):
        """Test file operations with None parameters."""
        with pytest.raises((TypeError, AttributeError)):
            move_file(None, None)
        
        with pytest.raises((TypeError, AttributeError)):
            calculate_file_hash(None)
        
        with pytest.raises((TypeError, AttributeError)):
            preserve_timestamps(None, None)
    
    @pytest.mark.unit
    def test_operations_with_empty_string_paths(self, temp_dir):
        """Test file operations with empty string paths."""
        with pytest.raises((FileNotFoundError, OSError)):
            move_file("", "dest.txt")
        
        with pytest.raises((FileNotFoundError, OSError)):
            calculate_file_hash("")
        
        with pytest.raises((FileNotFoundError, OSError)):
            preserve_timestamps("", "")
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_operations_with_special_characters_in_paths(self, temp_dir):
        """Test file operations with special characters in file paths."""
        special_chars = ["spaces in name.txt", "unicode文件.txt", "symbols!@#$%.txt"]
        
        for filename in special_chars:
            src_file = os.path.join(temp_dir, f"src_{filename}")
            dest_file = os.path.join(temp_dir, f"dest_{filename}")
            
            # Create source file
            with open(src_file, 'w', encoding='utf-8') as f:
                f.write(f"Content for {filename}")
            
            # Test hash calculation
            hash_result = calculate_file_hash(src_file)
            assert len(hash_result) == 64  # SHA256 hex length
            
            # Test move operation
            with patch('file_handler.file_operations.preserve_timestamps'):
                move_file(src_file, dest_file)
            
            assert not os.path.exists(src_file)
            assert os.path.exists(dest_file)
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_operations_with_very_long_paths(self, temp_dir):
        """Test file operations with very long file paths."""
        # Create nested directory structure
        long_path = temp_dir
        for i in range(10):  # Create reasonably deep nesting
            long_path = os.path.join(long_path, f"level_{i}")
        
        os.makedirs(long_path, exist_ok=True)
        
        long_filename = "very_long_filename_" + "a" * 100 + ".txt"
        src_file = os.path.join(long_path, f"src_{long_filename}")
        dest_file = os.path.join(long_path, f"dest_{long_filename}")
        
        # Create file
        with open(src_file, 'w') as f:
            f.write("Content in long path")
        
        # Test operations
        hash_result = calculate_file_hash(src_file)
        assert len(hash_result) == 64
        
        with patch('file_handler.file_operations.preserve_timestamps'):
            move_file(src_file, dest_file)
        
        assert not os.path.exists(src_file)
        assert os.path.exists(dest_file)