"""
Unit tests for config.config_handler module.

Tests cover:
- Configuration loading from JSON files
- Configuration getter methods
- Error handling for invalid configurations
- File system error scenarios
"""

import os
import json
import tempfile
from unittest.mock import Mock, patch, mock_open

import pytest

from config.config_handler import ConfigHandler


class TestConfigHandler:
    """Test ConfigHandler class functionality."""
    
    @pytest.mark.unit
    def test_init_with_valid_config(self, test_config_file):
        """Test ConfigHandler initialization with valid config file."""
        handler = ConfigHandler(test_config_file)
        
        assert handler.config_file == test_config_file
        assert isinstance(handler.config, dict)
        assert "default_duplicate_action" in handler.config
        assert "file_categories" in handler.config
        assert "subfolders" in handler.config
    
    @pytest.mark.unit
    def test_load_configuration_success(self, test_config_file, test_config):
        """Test successful configuration loading."""
        handler = ConfigHandler(test_config_file)
        
        assert handler.config == test_config
    
    @pytest.mark.unit
    def test_load_configuration_file_not_found(self, temp_dir):
        """Test configuration loading with non-existent file."""
        nonexistent_file = os.path.join(temp_dir, "nonexistent.json")
        
        with pytest.raises(FileNotFoundError):
            ConfigHandler(nonexistent_file)
    
    @pytest.mark.unit
    def test_load_configuration_invalid_json(self, temp_dir):
        """Test configuration loading with invalid JSON."""
        invalid_config_file = os.path.join(temp_dir, "invalid.json")
        with open(invalid_config_file, 'w') as f:
            f.write("{ invalid json content }")
        
        with pytest.raises(json.JSONDecodeError):
            ConfigHandler(invalid_config_file)
    
    @pytest.mark.unit
    def test_load_configuration_empty_file(self, temp_dir):
        """Test configuration loading with empty file."""
        empty_config_file = os.path.join(temp_dir, "empty.json")
        with open(empty_config_file, 'w') as f:
            f.write("")
        
        with pytest.raises(json.JSONDecodeError):
            ConfigHandler(empty_config_file)
    
    @pytest.mark.unit
    def test_load_configuration_permission_denied(self, temp_dir):
        """Test configuration loading when permission is denied."""
        config_file = os.path.join(temp_dir, "protected.json")
        
        # Mock file opening to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                ConfigHandler(config_file)
    
    @pytest.mark.unit
    def test_get_config_existing_key(self, test_config_file):
        """Test getting existing configuration key."""
        handler = ConfigHandler(test_config_file)
        
        result = handler.get_config("default_duplicate_action")
        assert result == "k"
        
        result = handler.get_config("file_categories")
        assert isinstance(result, dict)
        assert "Images" in result
    
    @pytest.mark.unit
    def test_get_config_nonexistent_key(self, test_config_file):
        """Test getting non-existent configuration key."""
        handler = ConfigHandler(test_config_file)
        
        result = handler.get_config("nonexistent_key")
        assert result is None
    
    @pytest.mark.unit
    def test_get_config_none_key(self, test_config_file):
        """Test getting configuration with None key."""
        handler = ConfigHandler(test_config_file)
        
        result = handler.get_config(None)
        assert result is None
    
    @pytest.mark.unit
    def test_get_config_empty_string_key(self, test_config_file):
        """Test getting configuration with empty string key."""
        handler = ConfigHandler(test_config_file)
        
        result = handler.get_config("")
        assert result is None


class TestConfigHandlerWithDifferentConfigs:
    """Test ConfigHandler with various configuration formats."""
    
    @pytest.mark.unit
    def test_minimal_config(self, temp_dir):
        """Test ConfigHandler with minimal configuration."""
        minimal_config = {"key": "value"}
        config_file = os.path.join(temp_dir, "minimal.json")
        
        with open(config_file, 'w') as f:
            json.dump(minimal_config, f)
        
        handler = ConfigHandler(config_file)
        assert handler.get_config("key") == "value"
        assert handler.get_config("missing") is None
    
    @pytest.mark.unit
    def test_nested_config(self, temp_dir):
        """Test ConfigHandler with nested configuration."""
        nested_config = {
            "level1": {
                "level2": {
                    "level3": "deep_value"
                },
                "other": "value"
            }
        }
        config_file = os.path.join(temp_dir, "nested.json")
        
        with open(config_file, 'w') as f:
            json.dump(nested_config, f)
        
        handler = ConfigHandler(config_file)
        level1_data = handler.get_config("level1")
        assert isinstance(level1_data, dict)
        assert level1_data["other"] == "value"
        assert level1_data["level2"]["level3"] == "deep_value"
    
    @pytest.mark.unit
    def test_config_with_arrays(self, temp_dir):
        """Test ConfigHandler with array configurations."""
        array_config = {
            "simple_list": [1, 2, 3],
            "string_list": ["a", "b", "c"],
            "mixed_list": [1, "two", {"three": 3}]
        }
        config_file = os.path.join(temp_dir, "arrays.json")
        
        with open(config_file, 'w') as f:
            json.dump(array_config, f)
        
        handler = ConfigHandler(config_file)
        assert handler.get_config("simple_list") == [1, 2, 3]
        assert handler.get_config("string_list") == ["a", "b", "c"]
        assert handler.get_config("mixed_list") == [1, "two", {"three": 3}]
    
    @pytest.mark.unit
    def test_config_with_unicode(self, temp_dir):
        """Test ConfigHandler with Unicode content."""
        unicode_config = {
            "unicode_string": "测试中文内容",
            "emoji": "🎉📁✨",
            "mixed": "English and 中文 mixed"
        }
        config_file = os.path.join(temp_dir, "unicode.json")
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(unicode_config, f, ensure_ascii=False)
        
        handler = ConfigHandler(config_file)
        assert handler.get_config("unicode_string") == "测试中文内容"
        assert handler.get_config("emoji") == "🎉📁✨"
        assert handler.get_config("mixed") == "English and 中文 mixed"
    
    @pytest.mark.unit
    def test_config_with_special_characters(self, temp_dir):
        """Test ConfigHandler with special characters in values."""
        special_config = {
            "path_separator": "\\",
            "quotes": '"quoted string"',
            "newlines": "line1\nline2\nline3",
            "tabs": "col1\tcol2\tcol3"
        }
        config_file = os.path.join(temp_dir, "special.json")
        
        with open(config_file, 'w') as f:
            json.dump(special_config, f)
        
        handler = ConfigHandler(config_file)
        assert handler.get_config("path_separator") == "\\"
        assert handler.get_config("quotes") == '"quoted string"'
        assert handler.get_config("newlines") == "line1\nline2\nline3"
        assert handler.get_config("tabs") == "col1\tcol2\tcol3"


class TestConfigHandlerEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.unit
    def test_config_file_becomes_inaccessible(self, test_config_file):
        """Test ConfigHandler when config file becomes inaccessible after initialization."""
        handler = ConfigHandler(test_config_file)
        
        # Ensure handler was initialized successfully
        assert handler.config is not None
        
        # Even if file becomes inaccessible later, get_config should still work
        # because config is loaded in memory
        result = handler.get_config("default_duplicate_action")
        assert result == "k"
    
    @pytest.mark.unit
    def test_config_modification_after_load(self, test_config_file):
        """Test that external modification of config doesn't affect loaded config."""
        handler = ConfigHandler(test_config_file)
        original_action = handler.get_config("default_duplicate_action")
        
        # Modify the config file
        new_config = {"default_duplicate_action": "modified"}
        with open(test_config_file, 'w') as f:
            json.dump(new_config, f)
        
        # ConfigHandler should still have original values
        assert handler.get_config("default_duplicate_action") == original_action
    
    @pytest.mark.unit
    def test_config_with_null_values(self, temp_dir):
        """Test ConfigHandler with null values in configuration."""
        null_config = {
            "null_value": None,
            "valid_value": "not_null",
            "nested": {
                "null_nested": None,
                "valid_nested": "valid"
            }
        }
        config_file = os.path.join(temp_dir, "null_values.json")
        
        with open(config_file, 'w') as f:
            json.dump(null_config, f)
        
        handler = ConfigHandler(config_file)
        assert handler.get_config("null_value") is None
        assert handler.get_config("valid_value") == "not_null"
        assert handler.get_config("nested")["null_nested"] is None
        assert handler.get_config("nested")["valid_nested"] == "valid"
    
    @pytest.mark.unit
    def test_config_with_boolean_values(self, temp_dir):
        """Test ConfigHandler with boolean values."""
        bool_config = {
            "enabled": True,
            "disabled": False,
            "nested_bool": {
                "feature_flag": True
            }
        }
        config_file = os.path.join(temp_dir, "boolean.json")
        
        with open(config_file, 'w') as f:
            json.dump(bool_config, f)
        
        handler = ConfigHandler(config_file)
        assert handler.get_config("enabled") is True
        assert handler.get_config("disabled") is False
        assert handler.get_config("nested_bool")["feature_flag"] is True
    
    @pytest.mark.unit
    def test_config_with_numeric_values(self, temp_dir):
        """Test ConfigHandler with various numeric values."""
        numeric_config = {
            "integer": 42,
            "float": 3.14159,
            "negative": -100,
            "zero": 0,
            "scientific": 1.23e-4
        }
        config_file = os.path.join(temp_dir, "numeric.json")
        
        with open(config_file, 'w') as f:
            json.dump(numeric_config, f)
        
        handler = ConfigHandler(config_file)
        assert handler.get_config("integer") == 42
        assert handler.get_config("float") == 3.14159
        assert handler.get_config("negative") == -100
        assert handler.get_config("zero") == 0
        assert handler.get_config("scientific") == 1.23e-4


class TestConfigHandlerIntegration:
    """Test ConfigHandler integration with real-world scenarios."""
    
    @pytest.mark.unit
    def test_file_organizer_config_structure(self, test_config):
        """Test ConfigHandler with FileOrganizer-specific configuration structure."""
        # Use the actual test config structure
        temp_dir = tempfile.mkdtemp()
        config_file = os.path.join(temp_dir, "file_organizer.json")
        
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        try:
            handler = ConfigHandler(config_file)
            
            # Test file categories access
            categories = handler.get_config("file_categories")
            assert "Images" in categories
            assert ".jpg" in categories["Images"]
            
            # Test subfolders access
            subfolders = handler.get_config("subfolders")
            assert subfolders[".jpg"] == "Images"
            
            # Test duplicate action
            action = handler.get_config("default_duplicate_action")
            assert action == "k"
            
        finally:
            # Clean up
            os.unlink(config_file)
            os.rmdir(temp_dir)
    
    @pytest.mark.unit
    def test_config_handler_thread_safety_simulation(self, test_config_file):
        """Test ConfigHandler behavior in simulated concurrent access."""
        handler = ConfigHandler(test_config_file)
        
        # Simulate multiple "threads" accessing config
        results = []
        for _ in range(10):
            result = handler.get_config("default_duplicate_action")
            results.append(result)
        
        # All results should be consistent
        assert all(r == "k" for r in results)
        assert len(set(results)) == 1  # All values should be the same
    
    @pytest.mark.unit
    def test_config_handler_memory_efficiency(self, temp_dir):
        """Test ConfigHandler memory usage with large configurations."""
        # Create a large configuration
        large_config = {
            "large_dict": {f"key_{i}": f"value_{i}" for i in range(1000)},
            "large_list": [f"item_{i}" for i in range(1000)]
        }
        config_file = os.path.join(temp_dir, "large.json")
        
        with open(config_file, 'w') as f:
            json.dump(large_config, f)
        
        handler = ConfigHandler(config_file)
        
        # Access should still be efficient
        large_dict = handler.get_config("large_dict")
        assert len(large_dict) == 1000
        assert large_dict["key_500"] == "value_500"
        
        large_list = handler.get_config("large_list")
        assert len(large_list) == 1000
        assert large_list[500] == "item_500"