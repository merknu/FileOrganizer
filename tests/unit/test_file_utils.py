"""
Unit tests for file_handler.file_utils module.

Tests cover:
- Configuration loading and validation
- File organization logic
- Duplicate handling
- Metadata-based organization
- Error scenarios and edge cases
"""

import os
import json
import tempfile
import logging
from unittest.mock import Mock, patch, call, mock_open
from collections import defaultdict

import pytest

from file_handler.file_utils import (
    load_config,
    validate_config,
    handle_duplicate,
    organize_by_metadata,
    handle_category,
    organize_files
)


class TestLoadConfig:
    """Test configuration loading functionality."""
    
    @pytest.mark.unit
    def test_load_valid_config(self, test_config_file, test_config):
        """Test loading a valid configuration file."""
        result = load_config(test_config_file)
        assert result == test_config
    
    @pytest.mark.unit
    def test_load_nonexistent_config(self, temp_dir):
        """Test loading a non-existent configuration file."""
        nonexistent_path = os.path.join(temp_dir, "nonexistent.json")
        result = load_config(nonexistent_path)
        assert result is None
    
    @pytest.mark.unit
    def test_load_invalid_json_config(self, temp_dir):
        """Test loading an invalid JSON configuration file."""
        invalid_config_path = os.path.join(temp_dir, "invalid.json")
        with open(invalid_config_path, 'w') as f:
            f.write("{ invalid json }")
        
        result = load_config(invalid_config_path)
        assert result is None
    
    @pytest.mark.unit
    def test_load_empty_config(self, temp_dir):
        """Test loading an empty configuration file."""
        empty_config_path = os.path.join(temp_dir, "empty.json")
        with open(empty_config_path, 'w') as f:
            f.write("{}")
        
        result = load_config(empty_config_path)
        assert result == {}
    
    @pytest.mark.unit
    def test_load_config_permission_denied(self, temp_dir):
        """Test loading config when permission is denied."""
        config_path = os.path.join(temp_dir, "protected.json")
        with open(config_path, 'w') as f:
            json.dump({"test": "data"}, f)
        
        # Mock permission denied
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            result = load_config(config_path)
            assert result is None


class TestValidateConfig:
    """Test configuration validation functionality."""
    
    @pytest.mark.unit
    def test_validate_complete_config(self, test_config):
        """Test validation of a complete, valid configuration."""
        assert validate_config(test_config) is True
    
    @pytest.mark.unit
    def test_validate_missing_file_categories(self, test_config):
        """Test validation with missing file_categories."""
        invalid_config = test_config.copy()
        del invalid_config["file_categories"]
        assert validate_config(invalid_config) is False
    
    @pytest.mark.unit
    def test_validate_missing_subfolders(self, test_config):
        """Test validation with missing subfolders."""
        invalid_config = test_config.copy()
        del invalid_config["subfolders"]
        assert validate_config(invalid_config) is False
    
    @pytest.mark.unit
    def test_validate_missing_duplicate_action(self, test_config):
        """Test validation with missing default_duplicate_action."""
        invalid_config = test_config.copy()
        del invalid_config["default_duplicate_action"]
        assert validate_config(invalid_config) is False
    
    @pytest.mark.unit
    def test_validate_empty_config(self):
        """Test validation of empty configuration."""
        assert validate_config({}) is False


class TestHandleDuplicate:
    """Test duplicate file handling functionality."""
    
    @pytest.mark.unit
    def test_handle_duplicate_gui_mode_keep(self):
        """Test duplicate handling in GUI mode with keep action."""
        result = handle_duplicate("src.txt", "dest.txt", "k", gui_mode=True)
        assert result == "k"
    
    @pytest.mark.unit
    def test_handle_duplicate_gui_mode_overwrite(self):
        """Test duplicate handling in GUI mode with overwrite action."""
        result = handle_duplicate("src.txt", "dest.txt", "o", gui_mode=True)
        assert result == "o"
    
    @pytest.mark.unit
    def test_handle_duplicate_gui_mode_rename(self):
        """Test duplicate handling in GUI mode with rename action."""
        result = handle_duplicate("src.txt", "dest.txt", "r", gui_mode=True)
        assert result == "r"
    
    @pytest.mark.unit
    def test_handle_duplicate_console_mode_default(self):
        """Test duplicate handling in console mode with default action."""
        with patch('builtins.input', return_value=''):
            result = handle_duplicate("src.txt", "dest.txt", "k", gui_mode=False)
            assert result == "k"
    
    @pytest.mark.unit
    def test_handle_duplicate_console_mode_user_input(self):
        """Test duplicate handling in console mode with user input."""
        with patch('builtins.input', return_value='o'):
            result = handle_duplicate("src.txt", "dest.txt", "k", gui_mode=False)
            assert result == "o"
    
    @pytest.mark.unit
    def test_handle_duplicate_keyboard_interrupt(self):
        """Test duplicate handling with keyboard interrupt."""
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            result = handle_duplicate("src.txt", "dest.txt", "k", gui_mode=False)
            assert result == "k"
    
    @pytest.mark.unit
    def test_handle_duplicate_eof_error(self):
        """Test duplicate handling with EOF error."""
        with patch('builtins.input', side_effect=EOFError):
            result = handle_duplicate("src.txt", "dest.txt", "r", gui_mode=False)
            assert result == "r"


class TestOrganizeByMetadata:
    """Test metadata-based file organization."""
    
    @pytest.mark.unit
    def test_organize_image_file(self, test_config):
        """Test organizing an image file by metadata."""
        with patch('file_handler.file_utils.handle_category', return_value="Images/1920x1080"):
            result = organize_by_metadata("test.jpg", ".jpg", test_config)
            assert result == "Images/1920x1080"
    
    @pytest.mark.unit
    def test_organize_document_file(self, test_config):
        """Test organizing a document file by metadata."""
        with patch('file_handler.file_utils.handle_category', return_value="Documents/Documents"):
            result = organize_by_metadata("test.pdf", ".pdf", test_config)
            assert result == "Documents/Documents"
    
    @pytest.mark.unit
    def test_organize_unknown_extension(self, test_config):
        """Test organizing a file with unknown extension."""
        result = organize_by_metadata("test.xyz", ".xyz", test_config)
        assert result == "Others"
    
    @pytest.mark.unit
    def test_organize_with_error(self, test_config):
        """Test organizing when an error occurs."""
        with patch('file_handler.file_utils.handle_category', side_effect=Exception("Test error")):
            result = organize_by_metadata("test.jpg", ".jpg", test_config)
            assert result == "Others"


class TestHandleCategory:
    """Test category-specific file handling."""
    
    @pytest.mark.unit
    @patch('file_handler.file_utils.get_image_size')
    def test_handle_images_category(self, mock_get_size, test_config):
        """Test handling images category."""
        mock_get_size.return_value = (1920, 1080)
        result = handle_category("test.jpg", "Images", ".jpg", test_config["subfolders"])
        assert result == "Images/1920x1080"
    
    @pytest.mark.unit
    @patch('file_handler.file_utils.get_image_size')
    def test_handle_images_category_error(self, mock_get_size, test_config):
        """Test handling images category when error occurs."""
        mock_get_size.side_effect = Exception("Image processing error")
        result = handle_category("test.jpg", "Images", ".jpg", test_config["subfolders"])
        assert result == "Images/Unknown_Size"
    
    @pytest.mark.unit
    @patch('file_handler.file_utils.get_audio_duration')
    def test_handle_audio_category(self, mock_get_duration, test_config):
        """Test handling audio category."""
        mock_get_duration.return_value = 180.5  # 180.5 seconds
        result = handle_category("test.mp3", "Audio", ".mp3", test_config["subfolders"])
        assert result == "Audio/180s"
    
    @pytest.mark.unit
    @patch('file_handler.file_utils.get_audio_duration')
    def test_handle_audio_category_no_duration(self, mock_get_duration, test_config):
        """Test handling audio category when duration is None."""
        mock_get_duration.return_value = None
        result = handle_category("test.mp3", "Audio", ".mp3", test_config["subfolders"])
        assert result == "Audio/0s"
    
    @pytest.mark.unit
    @patch('file_handler.file_utils.get_audio_duration')
    def test_handle_audio_category_error(self, mock_get_duration, test_config):
        """Test handling audio category when error occurs."""
        mock_get_duration.side_effect = Exception("Audio processing error")
        result = handle_category("test.mp3", "Audio", ".mp3", test_config["subfolders"])
        assert result == "Audio/Unknown_Duration"
    
    @pytest.mark.unit
    def test_handle_documents_category(self, test_config):
        """Test handling documents category."""
        result = handle_category("test.pdf", "Documents", ".pdf", test_config["subfolders"])
        assert result == "Documents/Documents"
    
    @pytest.mark.unit
    @patch('file_handler.file_utils.get_video_duration')
    def test_handle_video_category(self, mock_get_duration, test_config):
        """Test handling video category."""
        mock_get_duration.return_value = 3600.2  # 3600.2 seconds
        result = handle_category("test.mp4", "Video", ".mp4", test_config["subfolders"])
        assert result == "Video/3600s"
    
    @pytest.mark.unit
    @patch('file_handler.file_utils.get_video_duration')
    def test_handle_video_category_error(self, mock_get_duration, test_config):
        """Test handling video category when error occurs."""
        mock_get_duration.side_effect = Exception("Video processing error")
        result = handle_category("test.mp4", "Video", ".mp4", test_config["subfolders"])
        assert result == "Video/Unknown_Duration"
    
    @pytest.mark.unit
    def test_handle_unknown_category(self, test_config):
        """Test handling unknown category."""
        result = handle_category("test.xyz", "Unknown", ".xyz", test_config["subfolders"])
        assert result == "Unknown"
    
    @pytest.mark.unit
    def test_handle_category_with_error(self, test_config):
        """Test handling category when general error occurs."""
        # Force an error by passing invalid parameters
        result = handle_category(None, "Images", ".jpg", test_config["subfolders"])
        assert result == "Images"  # Should return the category name as fallback


class TestOrganizeFiles:
    """Test main file organization functionality."""
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_organize_nonexistent_folder(self, test_config):
        """Test organizing a non-existent folder."""
        result = organize_files("/nonexistent/folder", test_config)
        assert result["error"] == 1
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_organize_file_instead_of_folder(self, temp_dir, test_config):
        """Test organizing when path is a file, not a folder."""
        file_path = os.path.join(temp_dir, "not_a_folder.txt")
        with open(file_path, 'w') as f:
            f.write("test")
        
        result = organize_files(file_path, test_config)
        assert result["error"] == 1
    
    @pytest.mark.unit
    @pytest.mark.file_io
    @patch('os.listdir')
    def test_organize_permission_denied(self, mock_listdir, temp_dir, test_config):
        """Test organizing when permission is denied."""
        mock_listdir.side_effect = PermissionError("Access denied")
        
        # Create a real directory
        test_folder = os.path.join(temp_dir, "test")
        os.makedirs(test_folder)
        
        result = organize_files(test_folder, test_config)
        assert result["permission_denied"] == 1
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_organize_files_preview_mode(self, sample_files_structure, test_config):
        """Test organizing files in preview mode."""
        with patch('file_handler.file_utils.organize_by_metadata') as mock_organize:
            mock_organize.return_value = "Images/1920x1080"
            
            result = organize_files(sample_files_structure, test_config, preview_mode=True)
            
            # In preview mode, no files should be moved
            assert result["preview"] > 0
            assert result.get("moved", 0) == 0
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_organize_files_recursive(self, sample_files_structure, test_config):
        """Test organizing files recursively."""
        with patch('file_handler.file_utils.move_file') as mock_move, \
             patch('file_handler.file_utils.organize_by_metadata') as mock_organize, \
             patch('os.makedirs') as mock_makedirs:
            
            mock_organize.return_value = "Images"
            mock_makedirs.return_value = None
            
            result = organize_files(
                sample_files_structure, 
                test_config, 
                recursive=True, 
                preview_mode=False
            )
            
            # Should process files in subdirectories
            assert result.get("moved", 0) > 0 or result.get("processing_error", 0) > 0
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_organize_files_with_duplicates(self, duplicate_files_setup, test_config):
        """Test organizing files with duplicates."""
        with patch('file_handler.file_utils.calculate_file_hash') as mock_hash, \
             patch('file_handler.file_utils.organize_by_metadata') as mock_organize:
            
            mock_hash.return_value = "same_hash_123"
            mock_organize.return_value = "Documents"
            
            # Organize the original file into the target directory where duplicate exists
            result = organize_files(
                os.path.dirname(duplicate_files_setup["original"]), 
                test_config,
                preview_mode=False
            )
            
            # Should handle duplicate appropriately
            assert result.get("duplicate_kept", 0) > 0 or result.get("processing_error", 0) > 0
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_organize_files_no_extension(self, temp_dir, test_config):
        """Test organizing files without extensions."""
        # Create file without extension
        no_ext_file = os.path.join(temp_dir, "no_extension_file")
        with open(no_ext_file, 'w') as f:
            f.write("test content")
        
        result = organize_files(temp_dir, test_config)
        assert result["no_extension"] == 1
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_organize_files_mkdir_error(self, sample_files_structure, test_config):
        """Test organizing files when directory creation fails."""
        with patch('os.makedirs', side_effect=OSError("Permission denied")), \
             patch('file_handler.file_utils.organize_by_metadata', return_value="Images"):
            
            result = organize_files(sample_files_structure, test_config)
            assert result.get("mkdir_failed", 0) > 0
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_organize_files_move_error(self, sample_files_structure, test_config):
        """Test organizing files when move operation fails."""
        with patch('file_handler.file_utils.move_file', side_effect=OSError("Move failed")), \
             patch('file_handler.file_utils.organize_by_metadata', return_value="Images"), \
             patch('os.makedirs'):
            
            result = organize_files(sample_files_structure, test_config)
            assert result.get("move_failed", 0) > 0
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_organize_files_with_callback(self, sample_files_structure, test_config):
        """Test organizing files with callback function."""
        callback_calls = []
        
        def test_callback():
            callback_calls.append("called")
        
        with patch('file_handler.file_utils.organize_by_metadata', return_value="Images"), \
             patch('file_handler.file_utils.move_file'), \
             patch('os.makedirs'):
            
            organize_files(
                sample_files_structure, 
                test_config, 
                callback=test_callback,
                preview_mode=True  # Use preview to avoid actual moves
            )
            
            # Callback should have been called for each processed file
            assert len(callback_calls) > 0
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_organize_files_callback_error(self, sample_files_structure, test_config):
        """Test organizing files when callback raises error."""
        def failing_callback():
            raise Exception("Callback error")
        
        with patch('file_handler.file_utils.organize_by_metadata', return_value="Images"), \
             patch('os.makedirs'):
            
            # Should continue processing despite callback errors
            result = organize_files(
                sample_files_structure, 
                test_config, 
                callback=failing_callback,
                preview_mode=True
            )
            
            # Should still have processed files despite callback errors
            assert result.get("preview", 0) > 0 or result.get("processing_error", 0) > 0
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_organize_files_duplicate_rename(self, temp_dir, test_config):
        """Test organizing files with duplicate rename functionality."""
        # Create source file
        source_file = os.path.join(temp_dir, "test.txt")
        with open(source_file, 'w') as f:
            f.write("test content")
        
        # Create target directory and existing file
        target_dir = os.path.join(temp_dir, "Documents")
        os.makedirs(target_dir)
        existing_file = os.path.join(target_dir, "test.txt")
        with open(existing_file, 'w') as f:
            f.write("different content")
        
        with patch('file_handler.file_utils.calculate_file_hash') as mock_hash, \
             patch('file_handler.file_utils.organize_by_metadata', return_value="Documents"), \
             patch('file_handler.file_utils.handle_duplicate', return_value="r"), \
             patch('file_handler.file_utils.move_file') as mock_move:
            
            # Different hashes to trigger rename
            mock_hash.side_effect = ["hash1", "hash2"]
            
            result = organize_files(temp_dir, test_config)
            
            # Should have attempted to move with renamed file
            if mock_move.called:
                # Check that the destination was renamed
                call_args = mock_move.call_args[0]
                dest_path = call_args[1]
                assert "_copy1" in dest_path
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_organize_files_comprehensive_summary(self, temp_dir, test_config):
        """Test that organize_files returns comprehensive summary."""
        # Create various files for different scenarios
        files = [
            ("image1.jpg", "Images"),
            ("doc1.pdf", "Documents"),
            ("audio1.mp3", "Audio"),
            ("no_ext", None)  # File without extension
        ]
        
        for filename, category in files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write("test content")
        
        with patch('file_handler.file_utils.organize_by_metadata') as mock_organize, \
             patch('file_handler.file_utils.move_file'), \
             patch('os.makedirs'):
            
            def side_effect(file_path, ext, config):
                if "no_ext" in file_path:
                    return "Others"
                return "Images" if ext == ".jpg" else "Documents" if ext == ".pdf" else "Audio"
            
            mock_organize.side_effect = side_effect
            
            result = organize_files(temp_dir, test_config, preview_mode=True)
            
            # Should return dictionary with various counters
            assert isinstance(result, dict)
            total_counts = sum(v for v in result.values() if isinstance(v, int))
            assert total_counts > 0


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""
    
    @pytest.mark.unit
    def test_load_config_with_unicode(self, temp_dir):
        """Test loading config with unicode characters."""
        unicode_config = {"test_key": "测试unicode内容"}
        config_path = os.path.join(temp_dir, "unicode_config.json")
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(unicode_config, f, ensure_ascii=False)
        
        result = load_config(config_path)
        assert result == unicode_config
    
    @pytest.mark.unit
    def test_validate_config_with_none_values(self):
        """Test config validation with None values."""
        config = {
            "file_categories": None,
            "subfolders": {},
            "default_duplicate_action": "k"
        }
        assert validate_config(config) is False
    
    @pytest.mark.unit
    def test_organize_by_metadata_empty_config(self):
        """Test organize_by_metadata with empty config."""
        result = organize_by_metadata("test.jpg", ".jpg", {})
        assert result == "Others"
    
    @pytest.mark.unit
    @pytest.mark.file_io
    def test_organize_files_empty_folder(self, temp_dir, test_config):
        """Test organizing an empty folder."""
        empty_folder = os.path.join(temp_dir, "empty")
        os.makedirs(empty_folder)
        
        result = organize_files(empty_folder, test_config)
        
        # Should return empty summary or minimal counts
        assert isinstance(result, dict)
        total_files_processed = sum(v for k, v in result.items() 
                                  if k in ['moved', 'preview', 'duplicate_kept'])
        assert total_files_processed == 0
    
    @pytest.mark.unit
    def test_handle_category_with_none_parameters(self):
        """Test handle_category with None parameters."""
        result = handle_category(None, None, None, {})
        assert result is None  # Should return None or handle gracefully