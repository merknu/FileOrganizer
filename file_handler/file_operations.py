# file_handler/file_operations.py
import os
import shutil
from hashlib import sha256

# Move files from the source folder to the destination folder
def move_file(src, dest):
    shutil.move(src, dest)
    preserve_timestamps(src, dest)

# Preserve the timestamps of the files from the source folder to the destination folder
def preserve_timestamps(src, dest):
    stat_info = os.stat(src)
    os.utime(dest, (stat_info.st_atime, stat_info.st_mtime))

# Calculate the SHA256 hash of a file
def calculate_file_hash(file_path):
    with open(file_path, "rb") as file:
        file_hash = sha256(file.read()).hexdigest()
    return file_hash
