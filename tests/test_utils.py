"""
Tests for utility functions
"""

import unittest
from pathlib import Path
import tempfile
import shutil

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils.file_utils import (
    format_file_size,
    validate_path,
    sanitize_filename,
    get_unique_path
)


class TestFileUtils(unittest.TestCase):
    """Test file utility functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_format_file_size(self):
        """Test file size formatting"""
        self.assertEqual(format_file_size(0), "0.00 B")
        self.assertEqual(format_file_size(1024), "1.00 KB")
        self.assertEqual(format_file_size(1048576), "1.00 MB")
        self.assertEqual(format_file_size(1073741824), "1.00 GB")
        self.assertEqual(format_file_size(1099511627776), "1.00 TB")

    def test_format_file_size_decimals(self):
        """Test file size formatting with decimals"""
        self.assertEqual(format_file_size(1536), "1.50 KB")
        self.assertEqual(format_file_size(1572864), "1.50 MB")

    def test_validate_path_valid(self):
        """Test path validation with valid paths"""
        self.assertTrue(validate_path(str(self.test_dir)))
        self.assertTrue(validate_path("/tmp"))
        self.assertTrue(validate_path("./test"))

    def test_validate_path_invalid(self):
        """Test path validation with invalid paths"""
        self.assertFalse(validate_path(""))
        self.assertFalse(validate_path(None))

    def test_sanitize_filename(self):
        """Test filename sanitization"""
        self.assertEqual(sanitize_filename("my:file?.txt"), "my_file_.txt")
        self.assertEqual(sanitize_filename("file<>name.doc"), "file__name.doc")
        self.assertEqual(sanitize_filename('file"with|chars*.txt'), "file_with_chars_.txt")

    def test_sanitize_filename_empty(self):
        """Test filename sanitization with empty/invalid names"""
        self.assertEqual(sanitize_filename(""), "unnamed")
        self.assertEqual(sanitize_filename("..."), "unnamed")
        self.assertEqual(sanitize_filename("   "), "unnamed")

    def test_sanitize_filename_leading_trailing(self):
        """Test filename sanitization removes leading/trailing dots and spaces"""
        self.assertEqual(sanitize_filename("  file.txt  "), "file.txt")
        self.assertEqual(sanitize_filename("...file.txt..."), "file.txt")

    def test_get_unique_path_no_conflict(self):
        """Test unique path generation when no conflict exists"""
        test_file = self.test_dir / "test.txt"
        result = get_unique_path(test_file)
        self.assertEqual(result, test_file)

    def test_get_unique_path_with_conflict(self):
        """Test unique path generation with existing file"""
        test_file = self.test_dir / "test.txt"
        test_file.touch()

        result = get_unique_path(test_file)
        self.assertEqual(result, self.test_dir / "test (1).txt")
        self.assertFalse(result.exists())

    def test_get_unique_path_multiple_conflicts(self):
        """Test unique path generation with multiple existing files"""
        base_file = self.test_dir / "test.txt"
        base_file.touch()
        (self.test_dir / "test (1).txt").touch()
        (self.test_dir / "test (2).txt").touch()

        result = get_unique_path(base_file)
        self.assertEqual(result, self.test_dir / "test (3).txt")

    def test_get_unique_path_with_string(self):
        """Test unique path generation with string input"""
        test_file = str(self.test_dir / "test.txt")
        result = get_unique_path(test_file)
        self.assertEqual(result, Path(test_file))


if __name__ == '__main__':
    unittest.main()
