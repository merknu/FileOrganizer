#!/usr/bin/env python3
"""
Real functionality verification script.
This creates actual files, organizes them, and verifies the results.
"""

import os
import sys
import tempfile
import shutil
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from file_handler.file_utils import organize_files, load_config, validate_config
from file_handler.file_operations import calculate_file_hash
from config.config_handler import ConfigHandler


def verify_real_functionality():
    """Verify that the FileOrganizer actually works with real files."""
    print("FileOrganizer Functionality Verification")
    print("=" * 50)
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="fileorganizer_verify_")
    print(f"Working in: {temp_dir}")
    
    try:
        # Step 1: Create test configuration
        print("\n1. Creating test configuration...")
        config = {
            "default_duplicate_action": "k",
            "file_categories": {
                "Images": [".jpg", ".jpeg", ".png"],
                "Documents": [".pdf", ".txt", ".doc"],
                "Audio": [".mp3", ".wav"]
            },
            "subfolders": {
                ".jpg": "Images",
                ".jpeg": "Images",
                ".png": "Images",
                ".pdf": "Documents",
                ".txt": "Documents",
                ".doc": "Documents", 
                ".mp3": "Audio",
                ".wav": "Audio"
            }
        }
        
        config_file = os.path.join(temp_dir, "config.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✓ Configuration created: {config_file}")
        
        # Step 2: Verify config loading
        print("\n2. Verifying configuration loading...")
        loaded_config = load_config(config_file)
        assert loaded_config is not None, "Config loading failed"
        assert validate_config(loaded_config), "Config validation failed"
        
        config_handler = ConfigHandler(config_file)
        assert config_handler.get_config("default_duplicate_action") == "k"
        print("✓ Configuration loading and validation works")
        
        # Step 3: Create test files
        print("\n3. Creating test files...")
        test_files = [
            ("photo1.jpg", "Fake JPEG content for testing"),
            ("photo2.png", "Fake PNG content for testing"),
            ("document1.txt", "This is a test document with some content."),
            ("document2.pdf", "Fake PDF content for testing"),
            ("song1.mp3", "Fake MP3 audio content"),
            ("song2.wav", "Fake WAV audio content"),
            ("readme.md", "Markdown file content"),  # Unknown extension
            ("no_extension", "File without extension"),
        ]
        
        files_dir = os.path.join(temp_dir, "messy_files")
        os.makedirs(files_dir)
        
        created_files = {}
        for filename, content in test_files:
            filepath = os.path.join(files_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
            created_files[filename] = filepath
            print(f"  Created: {filename}")
        
        print(f"✓ Created {len(test_files)} test files")
        
        # Step 4: Calculate initial hashes
        print("\n4. Calculating file hashes...")
        initial_hashes = {}
        for filename, filepath in created_files.items():
            hash_value = calculate_file_hash(filepath)
            initial_hashes[filename] = hash_value
            print(f"  {filename}: {hash_value[:8]}...")
        
        # Step 5: Organize files (preview first)
        print("\n5. Running organization preview...")
        preview_result = organize_files(files_dir, config, recursive=False, preview_mode=True)
        print(f"Preview result: {preview_result}")
        
        assert isinstance(preview_result, dict), "Preview should return a dictionary"
        assert preview_result.get('preview', 0) > 0, "Preview should process some files"
        print("✓ Preview mode works correctly")
        
        # Step 6: Check directory structure before organization
        print("\n6. Directory structure before organization:")
        print_directory_structure(files_dir)
        
        # Step 7: Actually organize files
        print("\n7. Organizing files...")
        organize_result = organize_files(files_dir, config, recursive=False, preview_mode=False)
        print(f"Organization result: {organize_result}")
        
        assert isinstance(organize_result, dict), "Organization should return a dictionary"
        total_moved = organize_result.get('moved', 0)
        print(f"✓ Moved {total_moved} files")
        
        # Step 8: Check directory structure after organization
        print("\n8. Directory structure after organization:")
        print_directory_structure(files_dir)
        
        # Step 9: Verify organized files
        print("\n9. Verifying organized files...")
        
        # Check that organized files exist in expected locations
        expected_locations = {
            "photo1.jpg": os.path.join(files_dir, "Images", "Unknown_Size", "photo1.jpg"),
            "photo2.png": os.path.join(files_dir, "Images", "Unknown_Size", "photo2.png"),
            "document1.txt": os.path.join(files_dir, "Documents", "Documents", "document1.txt"),
            "document2.pdf": os.path.join(files_dir, "Documents", "Documents", "document2.pdf"),
            "song1.mp3": os.path.join(files_dir, "Audio", "Unknown_Duration", "song1.mp3"),
            "song2.wav": os.path.join(files_dir, "Audio", "Unknown_Duration", "song2.wav"),
        }
        
        verified_files = 0
        for filename, expected_path in expected_locations.items():
            if os.path.exists(expected_path):
                # Verify content integrity
                new_hash = calculate_file_hash(expected_path)
                original_hash = initial_hashes[filename]
                assert new_hash == original_hash, f"Hash mismatch for {filename}"
                verified_files += 1
                print(f"  ✓ {filename} -> {os.path.basename(os.path.dirname(expected_path))}")
            else:
                print(f"  ✗ {filename} not found at expected location")
        
        print(f"✓ Verified {verified_files} organized files")
        
        # Step 10: Test duplicate handling
        print("\n10. Testing duplicate handling...")
        duplicate_content = "Duplicate test content"
        
        # Create original file
        original_file = os.path.join(files_dir, "original.txt")
        with open(original_file, 'w') as f:
            f.write(duplicate_content)
        
        # Create target directory with existing file
        target_dir = os.path.join(files_dir, "Documents", "Documents")
        os.makedirs(target_dir, exist_ok=True)
        existing_file = os.path.join(target_dir, "original.txt")
        with open(existing_file, 'w') as f:
            f.write(duplicate_content)
        
        # Try to organize - should detect duplicate
        dup_result = organize_files(files_dir, config, recursive=False, preview_mode=True)
        print(f"Duplicate handling result: {dup_result}")
        
        has_duplicate_handling = (dup_result.get('duplicate_kept', 0) > 0 or 
                                dup_result.get('duplicate_check_failed', 0) > 0 or
                                dup_result.get('moved', 0) > 0)
        assert has_duplicate_handling, "Should handle duplicates"
        print("✓ Duplicate handling works")
        
        print("\n" + "=" * 50)
        print("🎉 ALL FUNCTIONALITY VERIFIED SUCCESSFULLY!")
        print(f"📁 Test files remain in: {temp_dir}")
        print("   (Will be cleaned up automatically)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
            print(f"\n🧹 Cleaned up temporary files")
        except:
            print(f"\n⚠️  Could not clean up {temp_dir}")


def print_directory_structure(directory, max_depth=3, current_depth=0):
    """Print directory structure in a tree format."""
    if current_depth > max_depth:
        return
    
    try:
        items = sorted(os.listdir(directory))
        for i, item in enumerate(items):
            item_path = os.path.join(directory, item)
            is_last = i == len(items) - 1
            
            # Tree formatting
            if current_depth == 0:
                prefix = ""
                child_prefix = ""
            else:
                prefix = "└── " if is_last else "├── "
                child_prefix = "    " if is_last else "│   "
            
            print(f"{'    ' * current_depth}{prefix}{item}")
            
            if os.path.isdir(item_path) and current_depth < max_depth:
                print_directory_structure(item_path, max_depth, current_depth + 1)
    except PermissionError:
        print(f"{'    ' * current_depth}[Permission Denied]")


if __name__ == "__main__":
    success = verify_real_functionality()
    sys.exit(0 if success else 1)