# Path: file_handler\file_utils.py
# This file is used to handle the files
from hashlib import sha256
import os
import shutil
import logging
from PIL import Image
from tinytag import TinyTag
from collections import defaultdict
import textract
import subprocess
import json


# this function is used to load the configuration file
def load_config(config_file):
    with open(config_file) as f:
        return json.load(f)


# This function is used to move the files from the source folder to the destination folder
def calculate_file_hash(file_path):
    with open(file_path, "rb") as file:
        file_hash = sha256(file.read()).hexdigest()
    return file_hash


# This function is used to handle the duplicate files
def handle_duplicate(src, dest, default_action):
    action = input(f"Duplicate file detected: {src}\n"
                   f"Destination: {dest}\n"
                   f"Options: (k)eep, (o)verwrite, (r)ename [default: {default_action}]: ")
    return action.lower() if action else default_action


# This function is used to preserve the timestamps of the files in the source folder to the destination folder
def preserve_timestamps(src, dest):
    stat_info = os.stat(src)
    os.utime(dest, (stat_info.st_atime, stat_info.st_mtime))


# This function is used to move the files from the source folder to the destination folder
def move_file(src, dest):
    shutil.move(src, dest)
    preserve_timestamps(src, dest)


# This function is used to get the size of an image file
def get_image_size(file_path):
    with Image.open(file_path) as img:
        return img.size


# This function is used to get the duration of an audio file
def get_audio_duration(file_path):
    tag = TinyTag.get(file_path)
    return tag.duration


# This function is used to get the word count of a document
def get_document_word_count(file_path):
    text = textract.process(file_path).decode('utf-8')
    return len(text.split())


# This function is used to get the duration of a video file using ffprobe (ffmpeg) command line tool
def get_video_duration(file_path):
    supported_formats = [".mp4", ".avi", ".mov", ".mkv", ".wmv"]
    _, ext = os.path.splitext(file_path)

    if ext.lower() not in supported_formats:
        raise ValueError(f"Unsupported video format: {ext}")

    cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {file_path}"
    output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()

    return int(float(output))


# This function is used to organize the files by metadata
def organize_by_metadata(file_path, ext, app_config):
    file_categories = app_config.get("file_categories", {})
    document_subfolders = app_config.get("subfolders", {})

    for category, extensions in file_categories.items():
        if ext in extensions:
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

    return "Others"


# This function is used to organize the files
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
                if callback:  # callback is used to update the progress bar in the GUI
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
