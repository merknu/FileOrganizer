# Path: file_handler/file_utils.py
# This file handles file organization with improved error handling and structure
import os
import logging
import json
from collections import defaultdict
from typing import Dict, Any, Optional, Callable
from .metadata_handlers import get_image_size, get_audio_duration, get_document_word_count, get_video_duration
from .file_operations import move_file, calculate_file_hash


def load_config(config_file: str) -> Optional[Dict[str, Any]]:
    """Load configuration from a JSON file with improved error handling."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file {config_file} not found.")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Configuration file {config_file} is not valid JSON: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error loading config {config_file}: {e}")
        return None


def handle_duplicate(src: str, dest: str, default_action: str) -> str:
    """Handle duplicate files with user interaction."""
    try:
        action = input(f"Duplicate file detected: {src}\n"
                      f"Destination: {dest}\n"
                      f"Options: (k)eep, (o)verwrite, (r)ename [default: {default_action}]: ")
        return action.lower() if action else default_action
    except (EOFError, KeyboardInterrupt):
        logging.info("User interrupted duplicate handling, using default action")
        return default_action


def organize_by_metadata(file_path: str, ext: str, app_config: Dict[str, Any]) -> str:
    """Organize files by metadata with better error handling."""
    file_categories = app_config.get("file_categories", {})
    document_subfolders = app_config.get("subfolders", {})

    try:
        for category, extensions in file_categories.items():
            if ext in extensions:
                return handle_category(file_path, category, ext, document_subfolders)
    except Exception as e:
        logging.warning(f"Error organizing by metadata for {file_path}: {e}")
    
    return "Others"


def handle_category(file_path: str, category: str, ext: str, document_subfolders: Dict[str, str]) -> str:
    """Handle each file category with improved error handling."""
    try:
        if category == "Images":
            try:
                width, height = get_image_size(file_path)
                return f"Images/{width}x{height}"
            except Exception as e:
                logging.warning(f"Could not get image size for {file_path}: {e}")
                return "Images/Unknown_Size"
                
        elif category == "Audio":
            try:
                duration = int(get_audio_duration(file_path) or 0)
                return f"Audio/{duration}s"
            except Exception as e:
                logging.warning(f"Could not get audio duration for {file_path}: {e}")
                return "Audio/Unknown_Duration"
                
        elif category == "Documents":
            subfolder = document_subfolders.get(ext.lower(), "Other_Documents")
            return f"Documents/{subfolder}"
            
        elif category == "Video":
            try:
                duration = int(get_video_duration(file_path) or 0)
                return f"Video/{duration}s"
            except Exception as e:
                logging.warning(f"Could not get video duration for {file_path}: {e}")
                return "Video/Unknown_Duration"
                
    except Exception as e:
        logging.error(f"Error handling category {category} for {file_path}: {e}")
    
    return category


def organize_files(folder: str, app_config: Dict[str, Any], recursive: bool = False, 
                  preview_mode: bool = False, callback: Optional[Callable] = None) -> Dict[str, int]:
    """
    Organize files in a given folder with improved error handling.
    
    Args:
        folder: Path to the folder to organize
        app_config: Configuration dictionary
        recursive: Whether to process subdirectories
        preview_mode: If True, only preview changes without moving files
        callback: Optional callback function to call after processing each file
    
    Returns:
        Dictionary with summary statistics
    """
    if not os.path.exists(folder):
        logging.error(f"Folder does not exist: {folder}")
        return {"error": 1}
    
    if not os.path.isdir(folder):
        logging.error(f"Path is not a directory: {folder}")
        return {"error": 1}
    
    summary = defaultdict(int)
    
    try:
        files = os.listdir(folder)
    except PermissionError:
        logging.error(f"Permission denied accessing folder: {folder}")
        return {"permission_denied": 1}
    except Exception as e:
        logging.error(f"Error listing files in {folder}: {e}")
        return {"error": 1}
    
    for file in files:
        src = os.path.join(folder, file)
        
        try:
            # Handle subdirectories if recursive
            if os.path.isdir(src) and recursive:
                sub_summary = organize_files(src, app_config, recursive, preview_mode, callback)
                for key, value in sub_summary.items():
                    summary[key] += value
                continue
            
            # Skip if not a file
            if not os.path.isfile(src):
                continue
            
            name, ext = os.path.splitext(file)
            ext = ext.lower()
            
            # Skip files without extensions
            if not ext:
                summary['no_extension'] += 1
                continue
            
            # Determine target subfolder
            subfolder = organize_by_metadata(src, ext, app_config)
            target_folder = os.path.join(folder, subfolder)
            
            # Create target directory
            try:
                os.makedirs(target_folder, exist_ok=True)
            except Exception as e:
                logging.error(f"Could not create directory {target_folder}: {e}")
                summary['mkdir_failed'] += 1
                continue
            
            dest = os.path.join(target_folder, file)
            
            # Handle duplicates
            if os.path.exists(dest):
                try:
                    if calculate_file_hash(src) == calculate_file_hash(dest):
                        default_action = app_config.get("default_duplicate_action", "k")
                        action = handle_duplicate(src, dest, default_action)
                        
                        if action == "r":
                            base_name, ext = os.path.splitext(file)
                            counter = 1
                            while os.path.exists(dest):
                                new_name = f"{base_name}_copy{counter}{ext}"
                                dest = os.path.join(target_folder, new_name)
                                counter += 1
                        elif action == "k":
                            summary['duplicate_kept'] += 1
                            continue
                except Exception as e:
                    logging.warning(f"Error checking duplicate for {src}: {e}")
                    summary['duplicate_check_failed'] += 1
                    continue
            
            # Move or preview file
            if not preview_mode:
                try:
                    move_file(src, dest)
                    summary['moved'] += 1
                    logging.info(f"Moved {src} to {dest}")
                except Exception as e:
                    summary['move_failed'] += 1
                    logging.error(f"Error moving file {src} to {dest}: {e}")
            else:
                summary['preview'] += 1
                logging.info(f"Preview: {src} would be moved to {dest}")
            
            # Call callback if provided
            if callback:
                try:
                    callback()
                except Exception as e:
                    logging.warning(f"Error in callback: {e}")
                    
        except Exception as e:
            logging.error(f"Error processing file {src}: {e}")
            summary['processing_error'] += 1
    
    return dict(summary)


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration structure."""
    required_keys = ["file_categories", "subfolders", "default_duplicate_action"]
    
    for key in required_keys:
        if key not in config:
            logging.error(f"Missing required config key: {key}")
            return False
    
    return True


# Main execution for testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Load and validate config
    app_config = load_config("../config/config.json")
    if not app_config:
        logging.error("Failed to load configuration")
        exit(1)
    
    if not validate_config(app_config):
        logging.error("Invalid configuration")
        exit(1)
    
    # Test organization (preview mode)
    test_folder = input("Enter folder path to organize (or press Enter to skip): ").strip()
    if test_folder and os.path.exists(test_folder):
        print("Running in preview mode...")
        summary = organize_files(test_folder, app_config, recursive=True, preview_mode=True)
        print("Preview Summary:", dict(summary))
        
        if input("Proceed with actual organization? (y/N): ").lower() == 'y':
            summary = organize_files(test_folder, app_config, recursive=True, preview_mode=False)
            print("Final Summary:", dict(summary))
    else:
        print("Test skipped - no valid folder provided")
