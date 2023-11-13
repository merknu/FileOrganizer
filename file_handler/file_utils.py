# Path: file_handler\file_utils.py
# This file is used to handle the files
import os
import logging
import json
from collections import defaultdict
from metadata_handlers import get_image_size, get_audio_duration, get_document_word_count, get_video_duration
from file_operations import move_file, preserve_timestamps, calculate_file_hash

# Load configuration from a JSON file
def load_config(config_file):
    try:
        with open(config_file) as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file {config_file} not found.")
        return None
    except json.JSONDecodeError:
        logging.error(f"Configuration file {config_file} is not a valid JSON.")
        return None

# Handle duplicate files
def handle_duplicate(src, dest, default_action):
    action = input(f"Duplicate file detected: {src}\n"
                   f"Destination: {dest}\n"
                   f"Options: (k)eep, (o)verwrite, (r)ename [default: {default_action}]: ")
    return action.lower() if action else default_action

# Organize files by metadata
def organize_by_metadata(file_path, ext, app_config):
    file_categories = app_config.get("file_categories", {})
    document_subfolders = app_config.get("subfolders", {})

    for category, extensions in file_categories.items():
        if ext in extensions:
            return handle_category(file_path, category, ext, document_subfolders)

    return "Others"

# Handle each file category
def handle_category(file_path, category, ext, document_subfolders):
    if category == "Images":
        width, height = get_image_size(file_path)
        return f"Images/{width}x{height}"
    elif category == "Audio":
        duration = int(get_audio_duration(file_path))
        return f"Audio/{duration}s"
    elif category == "Documents":
        subfolder = document_subfolders.get(ext.lower(), "Other Documents")
        return f"Documents/{subfolder}"
    elif category == "Video":
        duration = int(get_video_duration(file_path))
        return f"Video/{duration}s"
    else:
        return category

# Organize files in a given folder
def organize_files(folder, app_config, recursive=None, preview_mode=False, callback=None):
    summary = defaultdict(int)
    for file in os.listdir(folder):
        src = os.path.join(folder, file)

        if os.path.isdir(src) and recursive:
            organize_files(src, app_config, recursive, preview_mode)
            continue

        if not os.path.isfile(src):
            continue

        name, ext = os.path.splitext(file)
        ext = ext.lower()

        subfolder = organize_by_metadata(src, ext, app_config)
        target_folder = os.path.join(folder, subfolder)
        os.makedirs(target_folder, exist_ok=True)

        dest = os.path.join(target_folder, file)

        if os.path.exists(dest) and calculate_file_hash(src) == calculate_file_hash(dest):
            default_action = app_config.get("default_duplicate_action", "k")
            action = handle_duplicate(src, dest, default_action)

            if action == "r":
                dest = os.path.join(target_folder, f"{name}_copy{ext}")
            elif action == "k":
                continue

        if not preview_mode:
            try:
                move_file(src, dest)
                summary['moved'] += 1
                logging.info(f"Moved {src} to {dest}")
                if callback:
                    callback()
            except FileNotFoundError as e:
                summary['skipped'] += 1
                logging.error(f"Error moving file {src} to {dest}: {e}")
        else:
            summary['preview'] += 1
            logging.info(f"Preview: {src} would be moved to {dest}")
            if callback:
                callback()

    return summary

# Main execution
if __name__ == "__main__":
    # Setup logging (if not already set up)
    logging.basicConfig(level=logging.INFO)

    app_config = load_config("config.json")
    if app_config:
        organize_files(os.path.join("path", "to", "folder"), app_config, recursive=True, preview_mode=False)
