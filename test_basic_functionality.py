#!/usr/bin/env python3
"""
Basic functional tests for FileOrganizer using unittest.
These tests validate core functionality without external dependencies.
"""

import unittest
import tempfile
import os
import shutil
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from file_handler.file_utils import (
    load_config, 
    validate_config, 
    handle_duplicate,
    organize_by_metadata,
    organize_files
)
from file_handler.file_operations import (
    move_file,
    calculate_file_hash,
    preserve_timestamps
)
from config.config_handler import ConfigHandler


class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality that should work without external dependencies."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = {
            "default_duplicate_action": "k",
            "file_categories": {
                "Images": [".jpg", ".jpeg", ".png"],
                "Documents": [".pdf", ".txt", ".doc"],
                "Audio": [".mp3", ".wav"]
            },
            "subfolders": {
                ".jpg": "Images",
                ".txt": "Documents",
                ".mp3": "Audio"
            }
        }
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename, content="test content"):
        """Helper to create test files."""
        filepath = os.path.join(self.temp_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    def test_config_loading_valid_file(self):
        """Test loading a valid configuration file."""
        config_path = os.path.join(self.temp_dir, "config.json")
        with open(config_path, 'w') as f:
            json.dump(self.test_config, f)
        
        loaded_config = load_config(config_path)
        self.assertEqual(loaded_config, self.test_config)
    
    def test_config_loading_nonexistent_file(self):
        """Test loading a non-existent configuration file."""
        result = load_config(os.path.join(self.temp_dir, "nonexistent.json"))
        self.assertIsNone(result)
    
    def test_config_validation_valid(self):
        """Test validation of valid configuration."""
        self.assertTrue(validate_config(self.test_config))
    
    def test_config_validation_missing_keys(self):
        """Test validation with missing required keys."""
        invalid_config = {"default_duplicate_action": "k"}  # Missing other keys
        self.assertFalse(validate_config(invalid_config))
    
    def test_handle_duplicate_gui_mode(self):
        """Test duplicate handling in GUI mode."""
        result = handle_duplicate("src.txt", "dest.txt", "k", gui_mode=True)
        self.assertEqual(result, "k")
        
        result = handle_duplicate("src.txt", "dest.txt", "o", gui_mode=True)
        self.assertEqual(result, "o")
    
    def test_organize_by_metadata_known_extension(self):
        """Test metadata organization for known file types."""
        # Test will fall back to category name since we don't have metadata handlers
        result = organize_by_metadata("test.jpg", ".jpg", self.test_config)
        # Should either return metadata-based path or "Others"
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
    
    def test_organize_by_metadata_unknown_extension(self):
        """Test metadata organization for unknown file types."""
        result = organize_by_metadata("test.xyz", ".xyz", self.test_config)
        self.assertEqual(result, "Others")
    
    def test_file_hash_calculation(self):
        """Test file hash calculation."""
        test_file = self.create_test_file("test.txt", "test content for hash")
        hash1 = calculate_file_hash(test_file)
        
        # Hash should be consistent
        hash2 = calculate_file_hash(test_file)
        self.assertEqual(hash1, hash2)
        
        # Hash should be SHA256 (64 hex characters)
        self.assertEqual(len(hash1), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash1))
    
    def test_file_hash_different_content(self):
        """Test that different content produces different hashes."""
        file1 = self.create_test_file("file1.txt", "content1")
        file2 = self.create_test_file("file2.txt", "content2")
        
        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)
        
        self.assertNotEqual(hash1, hash2)
    
    def test_move_file_operation(self):
        """Test basic file moving operation."""
        # Create source file
        src_file = self.create_test_file("source.txt", "move test content")
        
        # Create destination path
        dest_dir = os.path.join(self.temp_dir, "dest")
        os.makedirs(dest_dir)
        dest_file = os.path.join(dest_dir, "moved.txt")
        
        # Move file
        move_file(src_file, dest_file)
        
        # Verify move
        self.assertFalse(os.path.exists(src_file))
        self.assertTrue(os.path.exists(dest_file))
        
        # Verify content
        with open(dest_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, "move test content")
    
    def test_config_handler_basic(self):
        """Test ConfigHandler basic functionality."""
        config_path = os.path.join(self.temp_dir, "handler_config.json")
        with open(config_path, 'w') as f:
            json.dump(self.test_config, f)
        
        handler = ConfigHandler(config_path)
        
        # Test getting existing key
        self.assertEqual(handler.get_config("default_duplicate_action"), "k")
        
        # Test getting non-existent key
        self.assertIsNone(handler.get_config("nonexistent_key"))
    
    def test_organize_files_basic_functionality(self):
        """Test basic file organization functionality."""
        # Create test folder with some files
        test_folder = os.path.join(self.temp_dir, "test_files")
        os.makedirs(test_folder)
        
        # Create test files
        self.create_test_file(os.path.join("test_files", "image.jpg"), "fake image")
        self.create_test_file(os.path.join("test_files", "document.txt"), "fake document")
        self.create_test_file(os.path.join("test_files", "no_ext"), "no extension")
        
        # Test in preview mode to avoid actual file moves
        result = organize_files(test_folder, self.test_config, preview_mode=True)
        
        # Should return a dictionary with results
        self.assertIsInstance(result, dict)
        
        # Should have processed some files
        total_processed = sum(v for k, v in result.items() if k in ['preview', 'moved', 'no_extension'])
        self.assertGreater(total_processed, 0)
    
    def test_organize_files_nonexistent_folder(self):
        """Test organizing non-existent folder."""
        result = organize_files("/nonexistent/folder", self.test_config)
        self.assertEqual(result.get("error"), 1)
    
    def test_organize_files_empty_folder(self):
        """Test organizing empty folder."""
        empty_folder = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_folder)
        
        result = organize_files(empty_folder, self.test_config)
        
        # Should return valid result without errors
        self.assertIsInstance(result, dict)
        # Should not have processing errors
        self.assertEqual(result.get("error", 0), 0)


class TestFileOperationsIntegration(unittest.TestCase):
    """Test file operations integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, filename, content="test content"):
        """Helper to create test files."""
        filepath = os.path.join(self.temp_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    def test_duplicate_detection_workflow(self):
        """Test complete duplicate detection workflow."""
        content = "duplicate test content"
        
        # Create original file
        original = self.create_test_file("original.txt", content)
        
        # Create duplicate with same content
        duplicate = self.create_test_file("duplicate.txt", content)
        
        # Create different file
        different = self.create_test_file("different.txt", "different content")
        
        # Calculate hashes
        original_hash = calculate_file_hash(original)
        duplicate_hash = calculate_file_hash(duplicate)
        different_hash = calculate_file_hash(different)
        
        # Verify duplicate detection
        self.assertEqual(original_hash, duplicate_hash)
        self.assertNotEqual(original_hash, different_hash)
    
    def test_move_and_verify_workflow(self):
        """Test move file and verify content workflow."""
        # Create source file with specific content
        content = "test content for move verification"
        src_file = self.create_test_file("source.txt", content)
        
        # Calculate hash before move
        original_hash = calculate_file_hash(src_file)
        
        # Move file
        dest_file = os.path.join(self.temp_dir, "moved.txt")
        move_file(src_file, dest_file)
        
        # Verify move
        self.assertFalse(os.path.exists(src_file))
        self.assertTrue(os.path.exists(dest_file))
        
        # Verify content integrity
        moved_hash = calculate_file_hash(dest_file)
        self.assertEqual(original_hash, moved_hash)
        
        with open(dest_file, 'r') as f:
            moved_content = f.read()
        self.assertEqual(moved_content, content)


def run_basic_tests():
    """Run basic functionality tests."""
    print("Running FileOrganizer Basic Functionality Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestBasicFunctionality))
    suite.addTest(unittest.makeSuite(TestFileOperationsIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
    
    return success


if __name__ == '__main__':
    success = run_basic_tests()
    exit(0 if success else 1)